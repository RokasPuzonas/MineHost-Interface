from bs4 import BeautifulSoup, Tag
import re
import ftplib
import datetime
import paramiko
import time

from .session import Session

class InvalidDomainException(Exception):
	"""Raised when trying to change a server address with an unsupported domain.
	"""
	pass


# TODO: Make the sending of commands not need to sleep inbetween, If It dosen't sleep then it dosen'y always send the commands to the server
class CommandSender:
	"""Used to directly send commands to a minecraft server.
	Rather than loggin into ssh, entering console manually.
	"""

	def __init__(self, host: str, password: str, port: int = 22):
		"""Initializes ssh client and tries connecting to given host

		:param host: Host address used while connecting to ssh
		:type host: str
		:param password: Password used for authentication
		:type password: str
		:param port: Port used while connecting to ssh, defaults to 22
		:type port: int, optional
		"""
		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.ssh.connect(host, port=port, username="console", password=password)
		self.channel = None

	def __enter__(self):
		self.open()
		return self

	def __exit__(self, _1, _2, _3):
		self.close()

	def __del__(self):
		self.ssh.close()

	def send(self, *args):
		"""Send commands to the server. You are able to send to multiple commands by giving multiple arguments.
		
		:param \*args: Commands you would like the server to execute.
		:type \*args: str

		:raises Exception: Raised if channel is not open
		"""
		if self.channel is None:
			raise Exception("Channel is not open")
		
		self.channel.sendall("\n".join(args)+"\n")
		time.sleep(0.5)

	def open(self):
		"""Opens a channel used to send commands.

		:raises Exception: Raised if channel is already open
		"""
		if self.channel is not None:
			raise Exception("Channel is already open")

		self.channel = self.ssh.invoke_shell()
		self.channel.sendall("console\n")
		time.sleep(0.5)

	def close(self):
		"""Closes channel used to send commands.

		:raises Exception: Raised if channel is already closed
		"""
		if self.channel is None:
			raise Exception("Channel is not open")

		self.channel.close()
		self.channel = None

# TODO: A way to edit the server.properties file easier.
class MCServer:
	"""Used to control a minehost minecraft server
	"""

	__attrs__ = [ "start_file" ]

	def __init__(self, server_id: str, session: Session):
		"""Initializes minecraft server instance. Retrieves some initial data like: address, ip and port.

		:param server_id: [description]
		:type server_id: str
		:param session: [description]
		:type session: Session
		"""
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
		return f"<MCServer({self.ip}:{self.port})>"

	@property
	def __url(self) -> str:
		return f"/minecraft-serverio-valdymas/{self.id}"

	def getPassword(self) -> str:
		"""Retrieves the password used to login to SSH, FTP and SFTP.

		:return: A string containing the password
		"""
		res = self.session.get(f"{self.__url}/failai")
		soup = BeautifulSoup(res.text, "lxml")
		return soup.select("table td span:nth-child(2)")[0].text

	def changePassword(self) -> bool:
		"""Change the current password to a new randomly generated password. Passwords can only be changed every few minutes.

		:return: Whether the change was successful
		"""
		res = self.session.get(f"{self.__url}/failai/change-password")
		return res.text.find("class=\"alert alert-info\"") > 0

	def getStats(self) -> dict:
		"""Returns a dictionary containing the current statistcs of the server.

		:return: A dictionary containing "state", "version", "ping", "online_players" and "max_players"
		"""
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
	
	def getExpirationDate(self) -> datetime.datetime:
		"""Returns the date at which the server will expire.

		:return: A datetime object
		"""
		res = self.session.get(f"{self.__url}/finansai")
		date_match = re.search(r"Serveris galioja iki: (\d{4}-\d{2}-\d{2} \d{1,2}:\d{2}:\d{2})", res.text)
		return datetime.datetime.strptime(date_match.group(1), "%Y-%m-%d %H:%M:%S")

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

	def FTP(self) -> ftplib.FTP:
		"""Creates a new FTP connection to the server. The password will be automatically inputted.

		:return: An open FTP connection
		"""
		ftp = ftplib.FTP()
		ftp.connect(self.ip, self.ftp_port)
		ftp.login("serveris", self.getPassword())
		return ftp

	def SSH(self) -> paramiko.SSHClient:
		"""Creates a new SSH connection to the server. The password will be automatically inputted.

		:return: An open SSH connection
		"""
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(self.ip, port=self.ssh_port, username="console", password=self.getPassword())
		return ssh

	def CommandSender(self) -> CommandSender:
		"""Creates a new CommandSender which allow you to easily send commands to the console.

		:return: The newly created CommandSender.
		"""
		return CommandSender(self.ip, self.getPassword(), self.ssh_port)

	def __isControlLocked(self):
		res = self.session.post("/query/user_loadingct.php", data={
			"k": self.__key
		})
		return res.text != ""

	def start(self) -> bool:
		"""Tries starting the server.

		:return: Whether if it succeded in starting the server.
		"""
		if self.__isControlLocked():
			return False

		self.session.post(f"/query/server_ct.php", data={
			"k": self.__key,
			"c": "startmc",
			"st": "mc"
		})
		return True

	def stop(self) -> bool:
		"""Tries stopping the server.

		:return: Whether if it succeded in stopping the server.
		"""
		if self.__isControlLocked():
			return False

		self.session.post(f"/query/server_ct.php", data={
			"k": self.__key,
			"c": "stopmc",
			"st": "mc"
		})
		return True

	def kill(self) -> bool:
		"""Tries killing the server. This is the same as stopping but killing dosen't save anything.

		:return: Whether if it succeded in killing the server.
		"""
		if self.__isControlLocked():
			return False

		self.session.post(f"/query/server_ct.php", data={
			"k": self.__key,
			"c": "killrestartmc",
			"st": "mc"
		})
		return True

