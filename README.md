python-python-fserver: A NDN File Server Proxy 
==========

A Named Data Network consisting of a Repo and a Catalog using python.

It supports Python >=3.6 and PyPy3 >=7.1.1.

Please see both python-ndn github documentations if you have any issues.

Catalog : https://github.com/zjkmxy/python-ndn
Repo    : https://github.com/JonnyKong/ndn-python-repo


HOW TO RUN:
	There are 3 parts to what I am working on. The catalog, the repo, and the client.
	Each part should be ran on a different terminal.

	The Catalog
		1. navigate to /catalog/examples
		2. run " python3 catalog.py "

	The Repo
		1. navigate to /repo/ndn_python_repo/cmd
		2. run " python3 main.py "

	The Client
		1. make sure both catalog and repo are running
		2. navigate to /repo/examples
		3. run " python3 getfile -r "testName" -n "insertname" "
		4. make sure insertname is a valid name in /catalog/examples/input_table.dat
