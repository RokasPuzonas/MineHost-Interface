import requests

class IncorrectLoginException(Exception):
	"""Raised when the given email and passwords are incorrect.
	"""
	pass


class InvalidSessionException(Exception):
	"""Raised when the current session is logged out or timed out.
	"""
	pass


class Session(requests.Session):
	"""Wrapper object around the requests.Session.
	Checks if it's logged on every request.
	"""

	def __init__(self, email: str = None, password: str = None):
		"""Initializes session if email and password are given.

		:param email: If provided with password will try to login.
		:type email: str, optional
		:param password: If provided with email will try to login.
		:type password: str, optional
		"""
		super().__init__()
		if email is not None and password is not None:
			self.login(email, password)

	def login(self, email: str, password: str):
		"""Attempts to login using the given credentials.

		:param email: Email used to login.
		:type email: str
		:param password: Password associated to given email.
		:type password: str
		:raises IncorrectLoginException: Raised on failed login.
		"""
		requests.Session.request(self, "POST", "https://minehost.lt/prisijungimas-prie-sistemos", data = {
			"login": email,
			"password": password
		})
		if not self.isValid():
			raise IncorrectLoginException()

	def logout(self):
		"""The session becomes invalid and will raise error if tried to request anything.
		"""
		self.get("/logout")

	def request(self, method, url, *args, **kvargs) -> requests.Response:
		"""Wrapper function around the default requests.request method.
		Instead of giving the whole url like "https://minehost.lt/logout" now you only need to write "/logout".`
		
		:return: requests.Response object
		"""
		response = requests.Session.request(self, method, "https://minehost.lt"+url, *args, **kvargs)
		# Basic check to see if the session is still logged in. Looks for the logout button.
		if response.text.find("href=\"/logout\"") == -1 and response.text.find("src=\"/img/logo.png\"") > 0:
			raise InvalidSessionException()
		
		return response

	def isValid(self) -> bool:
		"""Returns true if current session is logged in, otherwise false.

		:return: True if logged in.
		"""
		res = self.get("/valdymo-pultas")
		return res.text.find("<meta http-equiv=\"refresh\" content=\"0;url=/prisijungimas-prie-sistemos\">") == -1

