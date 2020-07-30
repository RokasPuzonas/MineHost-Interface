from bs4 import BeautifulSoup, Tag
import re
from ftplib import FTP
from datetime import datetime
import paramiko
import time

datetime_format = "%Y-%m-%d %H:%M:%S"


class InvalidDomainException(Exception):
	pass

# TODO: Make the sending of commands not need to sleep inbetween, If It dosen't sleep then it dosen'y always send the commands to the server
class CommandSender:
	def __init__(self, host, username, password, port=22):
		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.ssh.connect(host, port=port, username="console", password=password)
		self.channel = None

	def __enter__(self):
		if self.channel is None:
			self.open()
		return self

	def __exit__(self, _1, _2, _3):
		if self.channel is not None:
			self.close()

	def __del__(self):
		self.ssh.close()

	def send(self, *args):
		if self.channel is None:
			raise Exception("Channel is not open")
		
		self.channel.sendall("\n".join(args)+"\n")
		time.sleep(0.5)

	def open(self):
		if self.channel is not None:
			raise Exception("Channel is already open")

		self.channel = self.ssh.invoke_shell()
		self.channel.sendall("console\n")
		time.sleep(0.5)

	def close(self):
		if self.channel is None:
			raise Exception("Channel is not open")

		self.channel.close()
		self.channel = None

class MCServer:
	def __init__(self, server_id, session):
		self.id = server_id
		self.session = session
		
		info_res = self.session.get(self.__url)
		soup = BeautifulSoup(info_res.text, "lxml")
		
		info_rows = soup.select("table td[align=right] b")
		self.address = info_rows[6].text.split(":")[0]
		self.ip, self.port = info_rows[7].text.split(":")
		self.port = int(self.port)

		control_res = self.session.get(f"{self.__url}/valdymas")
		soup = BeautifulSoup(control_res.text, "lxml")
		self.__key = soup.find("input", id="khd")["value"]

	def __repr__(self):
		return f"<MinecraftServer({self.short_address})>"

	@property
	def __url(self):
		return f"/minecraft-serverio-valdymas/{self.id}"

	def getPassword(self):
		res = self.session.get(f"{self.__url}/failai")
		soup = BeautifulSoup(res.text, "lxml")
		return soup.select("table td span:nth-child(2)")[0].text

	def changePassword(self):
		res = self.session.get(f"{self.__url}/failai/change-password")
		return res.text.find("class=\"alert alert-info\"") > 0

	def getInfo(self):
		res = self.session.get(self.__url)
		soup = BeautifulSoup(res.text, "lxml")
		
		version = soup.find(id="mc_versija").text
		version = version != "-" and version or None

		ping = soup.find(id="mc_ping").text
		ping = ping != "-" and int(ping) or None

		online_players = soup.find(id="mc_online").text
		online_players = online_players != "-" and int(online_players) or None
		
		max_players = soup.find(id="mc_zaidejai").text
		max_players = max_players != "-" and int(max_players) or None
		
		return {
			"state": soup.find(id="mc_status").text,
			"version": version,
			"ping": ping,
			"online_players": online_players,
			"max_players": max_players
		}
	
	def getExpirationDate(self):
		res = self.session.get(f"{self.__url}/finansai")
		date_match = re.search(r"Serveris galioja iki: (\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2})", res.text)
		return datetime.strptime(date_match.group(1), datetime_format)

	@property
	def start_file(self):
		response = self.session.get(f"{self.__url}/paleidimo-failas")
		soup = BeautifulSoup(response.text, "lxml")
		return soup.find("input", id="startlinein").text

	@start_file.setter
	def start_file(self, start_file: str):
		self.session.post(f"{self.__url}/mc-versijos", data={
			"startfile": str(start_file)
		})

	@property
	def ssh_port(self):
		return self.port+1
	
	@property
	def sftp_port(self):
		return self.port+1
	
	@property
	def ftp_port(self):
		return self.port+3

	@property
	def short_address(self):
		info_res = self.session.get(self.__url)
		soup = BeautifulSoup(info_res.text, "lxml")
		return soup.find(id="shortaddr").text

	@short_address.setter
	def short_address(self, short_address: str):
		domains = (".minehost.lt", ".hotmc.eu")
		subdomain, domain_index = None, None

		for domain in domains:
			found_index = short_address.find(domain)
			if found_index == len(short_address)-len(domain):
				domain_index = domains.index(domain)
				subdomain = short_address[:found_index]
				break
		
		if domain_index is None:
			raise InvalidDomainException()

		res = self.session.get("/query/subdomenas.php", params={
			"f": self.id,
			"s": subdomain,
			"t": domain_index
		})
		if res.content.decode("UTF-8") == "Šis subdomenas jau užimtas. Bandykite kitą":
			raise InvalidDomainException()

	def FTP(self):
		ftp = FTP()
		ftp.connect(self.ip, self.ftp_port)
		ftp.login("serveris", self.getPassword())
		return ftp

	def SSH(self):
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(self.ip, port=self.ssh_port, username="console", password=self.getPassword())
		return ssh

	def CommandSender(self):
		return CommandSender(self.ip, "serveris", self.getPassword(), self.ssh_port)

	def __isControlLocked(self):
		res = self.session.post("/query/user_loadingct.php", data={
			"k": self.__key
		})
		return res.text != ""

	def start(self):
		if self.__isControlLocked():
			return False

		self.session.post(f"/query/server_ct.php", data={
			"k": self.__key,
			"c": "startmc",
			"st": "mc"
		})
		return True

	def stop(self):
		if self.__isControlLocked():
			return False

		self.session.post(f"/query/server_ct.php", data={
			"k": self.__key,
			"c": "stopmc",
			"st": "mc"
		})
		return True

	def kill(self):
		if self.__isControlLocked():
			return False

		self.session.post(f"/query/server_ct.php", data={
			"k": self.__key,
			"c": "killrestartmc",
			"st": "mc"
		})
		return True

