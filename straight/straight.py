import subprocess
import time
from argparse import ArgumentParser, SUPPRESS

def main():
    parser = ArgumentParser(description='ndn-python-repo')
    parser.add_argument('-n','--name',required=True,help='sftp file')
    args = vars(parser.parse_args())

    start = time.time()
    downproc = subprocess.Popen("sftp atmos-nwsc.ucar.edu:/home/corbin/sizefiles/"+args["name"],shell=True)
    while downproc.poll() is None:
        time.sleep(0.001)
    print(f'Total time: {time.time() - start} seconds')

if __name__ == '__main__':
    main()
