python-python-fserver: A small NDN Network - File Server Proxy in Python
==========

This is a Small Named Data Networking Network consisting of a Repo and a Catalog implemented in python. It is designed to compare the speed of the new proposed architecture, NDN, to the current architecture IP. More specifically, how NDN could be utilized to improve file transfers from a file server using different methods.

> This is NOT an official implementation and consider 'experimental'.

ndn-python-fserver uses the [python-ndn](https://github.com/named-data/python-ndn) library and the [python-ndn-repo](https://github.com/UCLA-IRL/ndn-python-repo) for it's implementation. All credit for the repo itself and the python ndn API should be rightfully given to the correct authors.

## Installation

### Prerequisites

* [python-ndn](https://python-ndn.readthedocs.io/en/latest/src/installation.html)

* [nfd](https://named-data.net/doc/NFD/0.5.0/INSTALL.html)

### Examples

There are different branches associated to this repository. The different branches correspond to the different methods of file transfering. Please fill out the ssh_config with the appropriate address of the file server and add that naming before continuing.

Methods:

* [sftp](https://github.com/justincpresley/ndn-python-fserver/tree/sftp)

There are 3 parts to this small NDN network The catalog, the repo, and the client.

Each part should be ran on a different terminal.

**The Catalog**

1. navigate to /catalog
2. run " python3 catalog.py "

**The Repo**

1. navigate to /repo/ndn_python_repo/cmd
2. run " python3 main.py "

**The Client**

1. make sure both catalog and repo are running
2. navigate to /repo/examples
3. run " python3 getfile -r "testName" -n "insertname" "
4. make sure insertname is a valid name in /catalog/input_table.dat

### Compare

To compare this architecture, you can use the following script:

1. navigate to /straight
2. run " python3 straight.py "

## License and Authors

ndn-python-fserver is an open source project that is licensed. See [`LICENSE.md`](LICENSE.md) for more information.

The Names of all authors associated with this project (excluding the ndn repo implementation and the ndn api) are below:

  * *Justin C Presley* (justincpresley)
	
