import setuptools

with open("README.md", "r") as f:
	long_description = f.read()

setuptools.setup(
	name="minehost-interface",
	version="1.0.2",
	author="Rokas Puzonas",
	author_email="rokas.puz@gmail.com",
	description="A simple for interacting with minehost servers.",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/RokasPuzonas/minehost-interface",
	license="MIT",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Topic :: Software Development",
		"Topic :: Software Development :: Libraries",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Topic :: Utilities",
		"Intended Audience :: Developers",
	],
	install_requires=["beautifulsoup4", "requests", "paramiko", "lxml"],
	python_requires=">=3.8",
)