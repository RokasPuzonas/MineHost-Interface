from bs4 import BeautifulSoup, Tag
import re
from datetime import datetime

from .server import MCServer
from .session import Session

# The changing of the password and profile info, are intentionally not implemented.
# It's just too much power

datetime_format = "%Y-%m-%d %H:%M:%S"

class Account:
	def __init__(self, username: str = None, password: str = None, session: Session = None):
		self.username = username
		if username is not None and password is not None:
			self.session = Session(username, password)
		elif session is not None:
			self.session = session
		else:
			raise Exception("Session or logins must be given")

	def __repr__(self):
		return f"<Account({self.username or self._cookies.get('PHPSESSID', 'NONE')})>"

	def getServers(self):
		control_res = self.session.get("/mano-serveriai")
		servers = []
		for server_id in re.findall("/minecraft-serverio-valdymas/(\d*)/", control_res.text):
			servers.append(MCServer(server_id, self.session))
		return servers
		
	def getServer(self, i: int = 0):
		return self.getServers()[i]

	def getBalance(self):
		balance_res = self.session.get("/balanso-pildymas")
		balance_match = re.search(r"balanse yra (\d+\.?\d*)", balance_res.text)
		return float(balance_match.group(1))

	def getProfileInfo(self):
		profile_res = self.session.get("/profilio-nustatymai")
		soup = BeautifulSoup(profile_res.text, "lxml")
		return {
			"email": re.search("Vartotojas: ([\w\.-]+@[\w\.-]+)", profile_res.text).group(1),
			"name": soup.find("input", id="v1")["value"],
			"surname": soup.find("input", id="v2")["value"],
			"phone": soup.find("input", id="v4")["value"],
			"skype": soup.find("input", id="v5")["value"]
		}

	def getLoginHistory(self, limit: int = 10):
		history_res = self.session.get("/istorija/prisijungimu-istorija")
		soup = BeautifulSoup(history_res.text, "lxml")
		history = []

		for entry in soup.find("table").children:
			if type(entry) != Tag: continue
			
			fields = entry.findAll("td", align="center")
			if len(fields) != 3: continue

			history.append({
				"date": datetime.strptime(fields[1].text, datetime_format),
				"ip": fields[2].text
			})
			if len(history) == limit: break

		return history

	def getFinanceHistory(self, limit: int = 10):
		history_res = self.session.get("/balanso-pildymas/ataskaita")
		soup = BeautifulSoup(history_res.text, "lxml")
		history = []

		for entry in soup.find("table").children:
			if type(entry) != Tag: continue
			
			fields = entry.findAll("td")
			if len(fields) != 4: continue

			history.append({
				"date": datetime.strptime(fields[0].text, datetime_format),
				"action": fields[1].text,
				"balance_change": float(fields[2].text[:-4]),
				"balance_remainder": float(fields[3].text[:-3]),
			})
			if len(history) == limit: break

		return history

	def getProfileInfoHistory(self, limit: int = 10):
		history_res = self.session.get("/profilio-nustatymai")
		soup = BeautifulSoup(history_res.text, "lxml")
		history = []

		for entry in soup.find("table").children:
			if type(entry) != Tag: continue
			
			fields = entry.findAll("td")
			if len(fields) != 6: continue

			history.append({
				"date": datetime.strptime(fields[0].text, datetime_format),
				"name": fields[1].text,
				"surname": fields[2].text,
				"phone": fields[3].text,
				"skype": fields[4].text,
				"ip": fields[5].text
			})
			if len(history) == limit: break

		return history

