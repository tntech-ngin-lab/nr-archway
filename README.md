ndn-archway: A Bridge to Scientific Data Repositories
====================================================

ndn-archway's introduction, design, and goals are included in this [paper]().

ndn-archway is a NDN protocol built as a solution to connect different-interface, existing repositories for scientific communities. This protocol can be used beyond this initial use however.

ndn-archway consist of 4 parts: client(s), (NDN) repo, (NDN) catalog, and existing IP/NDN repo(s).
It is designed by conjoining two architectures, the future proposed architecture NDN with the current architecture IP.

ndn-archway uses the [python-ndn](https://github.com/named-data/python-ndn) library and the [python-ndn-repo](https://github.com/UCLA-IRL/ndn-python-repo) for it's implementation. All credit for the python-ndn-repo itself and the python-ndn API should be rightfully given to the correct authors.

## Installation

### Prerequisites

* [python-ndn](https://python-ndn.readthedocs.io/en/latest/src/installation.html)

* [nfd](https://named-data.net/doc/NFD/0.5.0/INSTALL.html)

## Environment Steps

### Examples

Available Interfaces:

* ftp

There are 3 parts to this small NDN network The catalog, the repo, and the client. All need to have each other's
public key. Also, fill out the ssh_config with the appropriate address of the file server and add that naming to the repo's config before continuing.

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

nr-archway is an open source project that is licensed. See [`LICENSE.md`](LICENSE.md) for more information.

The Names of all authors associated with this project (excluding the [python-ndn-repo](https://github.com/UCLA-IRL/ndn-python-repo) implementation and the [python-ndn](https://github.com/named-data/python-ndn) library) are below:

  * *Justin C Presley* (justincpresley)