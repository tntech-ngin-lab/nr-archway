#!/usr/bin/env python3
"""
    NDN Repo getfile example.

    @Author jonnykong@cs.ucla.edu
"""

import argparse
import asyncio as aio
import logging
import time
from ndn.app import NDNApp
from ndn.encoding import Name
from ndn.security import KeychainDigest
import sys
sys.path.insert(0,'..')
from ndn_python_repo.clients import GetfileClient

async def run_getfile_client(app: NDNApp, **kwargs):
    """
    Async helper function to run the GetfileClient.
    This function is necessary because it's responsible for calling app.shutdown().
    """
    client = GetfileClient(app)
    await client.fetch_file(kwargs['name_at_repo'])
    app.shutdown()

def main():
    parser = argparse.ArgumentParser(description='getfile')
    parser.add_argument('-n', '--name_at_repo',
                        required=True, help='Name used to store file at Repo')
    args = parser.parse_args()

    logging.basicConfig(format='[%(asctime)s]%(levelname)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    start = time.time()
    app = NDNApp()
    try:
        app.run_forever(
            after_start=run_getfile_client(app, name_at_repo=Name.from_str(args.name_at_repo)))
    except FileNotFoundError:
        print('Error: could not connect to NFD.')

    print(f'Total time: {time.time() - start} seconds')

if __name__ == '__main__':
    main()
