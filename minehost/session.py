import requests

# The "Cookies" functions are used, when you already have dictionary of cookies,
# So that the function internally would not need to create one

class IncorrectLoginException(Exception):
	pass


class InvalidSessionException(Exception):
	pass


class Session(requests.Session):
	def __init__(self, username: str = None, password: str = None):
		super().__init__()
		if username is not None and password is not None:
			self.login(username, password)

	def login(self, username: str, password: str):
		requests.Session.request(self, "POST", "https://minehost.lt/prisijungimas-prie-sistemos", data = {
			"login": username,
			"password": password
		})
		if not self.isValid():
			raise IncorrectLoginException()

	def logout(self):
		self.get("/logout")

	def request(self, method, url, *args, **kvargs):
		response = requests.Session.request(self, method, "https://minehost.lt"+url, *args, **kvargs)
		# Basic check to see if the session is still logged in. Looks for the logout button.
		if response.text.find("href=\"/logout\"") == -1 and response.text.find("src=\"/img/logo.png\"") > 0:
			raise InvalidSessionException()
		
		return response

	def isValid(self):
		res = self.get("/valdymo-pultas")
		return res.text.find("<meta http-equiv=\"refresh\" content=\"0;url=/prisijungimas-prie-sistemos\">") == -1

