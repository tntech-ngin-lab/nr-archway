import requests
import threading
import sys
import os
import heapdict
import math
from datetime import datetime
import logging
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout, InterestCanceled, ValidationFailure
from ndn.encoding import Name
from argparse import ArgumentParser, SUPPRESS

logging.basicConfig(format='[{asctime}]{levelname}:{message}',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    style='{')

def requestFileChild(remoteURL,threadID, splitSize,bufferOffset,bufferSize,fileSize,heapDict):
    # Calculates Range of Bytes
    startRange = int(splitSize * threadID)+bufferOffset
    endRange = min(startRange+splitSize-1,fileSize-1,bufferSize+bufferOffset-1)
    # Creates the HTTP header for the request
    headers = {"Range": "bytes=%i-%i" % (startRange,endRange)}
    # Makes the HTTP request on the byte range - stores content in data
    data = requests.get(remoteURL, headers=headers).content
    # Places data in the heapDict with priority set by current thread number
    heapDict[data] = threadID

def requestFile(url,localFile,threadCount,bufferSize):
    # Sends a request for the filesize
    fileSize = int(requests.head(url).headers['Content-length'])
    # Determines size to be downloaded by each thread
    splitSize = min(int(fileSize/threadCount)+1,int(bufferSize/threadCount)+1)
	# Heapdict implements the priority queue
    hd = heapdict.heapdict()
	# For files larger than the buffersize splits the requests
    if (fileSize > bufferSize):
        majorSplits = math.ceil(fileSize/bufferSize)
    else:
        majorSplits = 1
        outputFiles.append(localFile)

    for filePart in range(majorSplits):
        bufferOffset = bufferSize * filePart
        threads = []
        for threadID in range(threadCount):
            download_thread = threading.Thread(target=requestFileChild, args=(url,threadID,splitSize,bufferOffset,bufferSize,fileSize,hd))
            threads.append(download_thread)
        # Starts all threads
        for thread in threads:
            thread.start()
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
		# Writes the first part of the file (creates file if there is not one)
        if(filePart == 0):
            with open(localFile, "wb+") as myfile:
                for i in range(threadCount):
                    item = hd.popitem()
                    myfile.write(item[0])
                myfile.close()
		# Writes the subsequent parts of the file
        else:
            with open(localFile, "ab") as myfile:
                for i in range(threadCount):
                    item = hd.popitem()
                    myfile.write(item[0])
                myfile.close()
        hd.clear()
    logging.info(f'File Downloaded')


async def catalog_consumer(app, name):
    try:
        logging.info(f'Read handle: sending interest to {Name.to_str(name)}')
        ex_int_name, meta_info, content = await app.express_interest(name, must_be_fresh=True, can_be_prefix=False, lifetime=6000)
        logging.info(f'Read handle: received Data Name from {Name.to_str(ex_int_name)}')
        if content:
            logging.info(f'Read handle: content received: {bytes(content).decode()}')
        else:
            logging.info(f'Read handle: content received: None')
        clist = bytes(content).decode().split(",")
        if len(clist) != 6:
            return None
        translation = {}
        translation["interface"] = clist[0] if clist[0]!="null" else None
        translation["host"] = clist[1] if clist[1]!="null" else None
        translation["port"] = clist[2] if clist[2]!="null" else None
        translation["dataname"] = clist[3] if clist[3]!="null" else None
        translation["username"] = clist[4] if clist[4]!="null" else None
        translation["password"] = clist[5] if clist[5]!="null" else None
        return translation
    except InterestNack as e:
        logging.warning(f'Nacked with reason={e.reason}')
    except InterestTimeout:
        logging.warning(f'Timeout')
    except InterestCanceled:
        logging.warning(f'Canceled')
    except ValidationFailure:
        logging.warning(f'Data failed to validate')
    except Exception as e:
        logging.warning(f'Unknown Error has Occured: {e}')
    return None

async def main_helper(app:NDNApp, name:Name) -> None:
    translation = await catalog_consumer(app, name)
    if translation == None:
        logging.info(f'Translation: None')
        return
    logging.info(f'Translation: {translation}')
    url = "http://" + translation["host"] + translation["dataname"]
    logging.info(f'Pulling URL={url}')
    requestFile(url, "temp.txt", 5, 1000000)
    logging.info(f'Pull Completed')
    app.shutdown()

def main() -> None:
    # Command Line Parser
    parser = ArgumentParser(add_help=False,description="Request an Interest")
    requiredArgs = parser.add_argument_group("required arguments")
    optionalArgs = parser.add_argument_group("optional arguments")
    # Adding All Command Line Arguments
    requiredArgs.add_argument("-n","--name",required=True,help="name of the interest")
    optionalArgs.add_argument("-h","--help",action="help",default=SUPPRESS,help="show this help message and exit")
    # Getting All Arugments
    args = vars(parser.parse_args())
    name = Name.from_str('/catalog') + Name.from_str(args["name"])
    app = NDNApp()
    try:
        app.run_forever(after_start=main_helper(app, name))
    except FileNotFoundError:
        logging.warning(f'Error: could not connect to NFD')

if __name__ == '__main__':
    main()