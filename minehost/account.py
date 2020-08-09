from bs4 import BeautifulSoup, Tag
import re
from datetime import datetime
import math

from .server import MCServer
from .session import Session, InvalidSessionException

# The changing of the password and profile info, are intentionally not implemented.
# It's just too much power

datetime_format = "%Y-%m-%d %H:%M:%S"

class Account:
	"""Used to get servers, history, balance and other details associated to a specific account.
	"""

	def __init__(self, email: str = None, password: str = None, session: Session = None):
		"""Initializes an account

		:param email: email used to login, defaults to None
		:type email: str, optional
		:param password: password used to login, defaults to None
		:type password: str, optional
		:param session: an already created session can be provided, defaults to None
		:type session: :class:`Session <Session>`, optional
		:raises InvalidSessionException: Raised when the given custom session is invalid or when nothing was provided
		"""

		self.email = email
		self.session = None
		if email is not None and password is not None:
			self.session = Session(email, password)
		elif session is not None:
			self.session = session

		if self.session is None or not self.session.isValid():
			raise InvalidSessionException()

	def __repr__(self):
		return f"<Account({self.email})>"

	def getServers(self) -> list:
		"""Returns a list of minecraft server objects.

		:return: List of MCServer
		"""
		control_res = self.session.get("/mano-serveriai")
		servers = []
		for server_id in re.findall("/minecraft-serverio-valdymas/(\d*)/", control_res.text):
			servers.append(MCServer(server_id, self.session))
		return servers
		
	def getServer(self, i: int = 0) -> MCServer:
		"""Helper method get a server quickly.
		Most people will only want to interact with 1 server.

		:param i: Index of server (0 indexed), defaults to 0
		:type i: int, optional
		:return: A MCServer
		"""
		return self.getServers()[i]

	def getBalance(self) -> float:
		"""Current balance in account.

		:return: A float representing the current balance.
		"""
		balance_res = self.session.get("/balanso-pildymas")
		balance_match = re.search(r"balanse yra (\d+\.?\d*)", balance_res.text)
		return float(balance_match.group(1))

	def getDetails(self) -> dict:
		"""Returns a dictionary containing general details about account.
		Available details: email, name, surname, phone, skype.

		:return: A dictionary with account details.
		"""
		profile_res = self.session.get("/profilio-nustatymai")
		soup = BeautifulSoup(profile_res.text, "lxml")
		return {
			"email": re.search("Vartotojas: ([\w\.-]+@[\w\.-]+)", profile_res.text).group(1),
			"name": soup.find("input", id="v1")["value"],
			"surname": soup.find("input", id="v2")["value"],
			"phone": soup.find("input", id="v4")["value"],
			"skype": soup.find("input", id="v5")["value"]
		}

	def getLoginHistory(self, limit: int = math.inf) -> list:
		"""Returns a list of entries, where each entry holds the date and ip of who logged in.
		Entry keys: date, ip.

		:param limit: The maximum number of entries it should try getting, defaults to math.inf
		:type limit: int, optional
		:return: A list of entries where each entry is a dictionary.
		"""
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
			if len(history) >= limit: break

		return history

	def getFinanceHistory(self, limit: int = math.inf) -> list:
		"""Returns a list of entries where each entry describes a transaction.
		Entry keys: date, action, balance_change, balance_remainder

		:param limit: The maximum number of entries it should try getting, defaults to math.inf
		:type limit: int, optional
		:return: A list of entries where each entry is a dictionary.
		"""
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
			if len(history) >= limit: break

		return history

	def getProfileDetailsHistory(self, limit: int = math.inf) -> list:
		"""Returns a list of entries where each entry describes what was changed and by who.
		Entry keys: date, name, surname, phone, skype, ip.

		:param limit: The maximum number of entries it should try getting, defaults to math.inf
		:type limit: int, optional
		:return: A list of entries where each entry is a dictionary.
		"""
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
			if len(history) >= limit: break

		return history