import minehost

# Ensure that the latest are installed
# pip install -U setuptools wheel

# Build package
# python3 setup.py sdist bdist_wheel

# Upload to Test PyPi
# twine upload -R testpypi dist/*

# Upload to PyPi
# twine upload dist/*

# Install package from Test PyPi
# pip install --index-url https://test.pypi.org/simple/ <package-name>

def main():		
	session = minehost.Session()

	try:
		with open("session-id.ignore.txt", "r") as f:
			session.cookies.set("PHPSESSID", f.read())
		if not session.isValid():
			raise minehost.InvalidSessionException
	except (IOError, minehost.InvalidSessionException):
		session.login("kasparas253@gmail.com", "5e1877")

	acc = minehost.Account(session=session)
	server = acc.getServer()
	print(server.getInfo())

	with open("session-id.ignore.txt", "w") as f:
		f.write(session.cookies.get("PHPSESSID"))

if __name__ == "__main__":
	main()