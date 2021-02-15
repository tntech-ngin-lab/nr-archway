import asyncio as aio
import logging
import ndn.utils
import subprocess
import sys
import os
import random
import mmap
import contextlib
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout, InterestCanceled, ValidationFailure
from ndn.encoding import Name, Component, InterestParam, tlv_var
from ndn.encoding import parse_network_nack, parse_interest, make_network_nack, make_interest, NackReason
from ndn.encoding import make_data, MetaInfo, ContentType
from ..storage import Storage
sys.path.insert(0,'..')
from ndn_python_repo.clients import PutfileClient, DeleteClient

class ReadHandle(object):
    """
    ReadCommandHandle processes ordinary interests, and return corresponding data if exists.
    """
    def __init__(self, app: NDNApp, storage: Storage, config: dict):
        """
        :param app: NDNApp.
        :param storage: Storage.
        TODO: determine which prefix to listen on.
        """
        self.app = app
        self.storage = storage
        self.register_root = config['repo_config']['register_root']
        self.repo_name = config['repo_config']['repo_name']
        self.curr_file_requests = {}
        self.segment_size = 8000
        if self.register_root:
            self.listen(Name.from_str('/'))
    def listen(self, prefix):
        """
        This function needs to be called for prefix of all data stored.
        :param prefix: NonStrictName.
        """
        self.app.route(prefix)(self._on_interest)
        logging.info(f'Read handle: listening to {Name.to_str(prefix)}')
    def unlisten(self, prefix):
        """
        :param name: NonStrictName.
        """
        aio.ensure_future(self.app.unregister(prefix))
        logging.info(f'Read handle: stop listening to {Name.to_str(prefix)}')

    async def _get_server_file_size(self, int_name):
        sizeproc = subprocess.Popen("ssh " + self.curr_file_requests[Name.to_str(int_name[:-1])]["server"] + " 'stat " + self.curr_file_requests[Name.to_str(int_name[:-1])]["srcdir"] + "' | grep -oP '(?<=Size: )[0-9]+'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while sizeproc.poll() is None:
            await aio.sleep(0)
        return ( int(sizeproc.communicate()[0].decode().strip('\n')) )
    def _get_current_file_size(self, filename):
        with open(filename, 'r+') as f:
            f.seek(0,2) # move the cursor to the end of the file
            return ( f.tell() )
    def _read_memory_segment(self, filename, segment_size, segment_number):
        with open(filename, 'r+') as f:
            with contextlib.closing(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)) as m:
                m.seek(segment_size * segment_number, 0)
                return ( m.read(segment_size) )
    def _how_many_segments(self, size, segment_size):
        return (size//segment_size) if (size%segment_size==0) else (size//segment_size + 1)

    async def _request_from_catalog(self, int_name):
        try:
            timestamp = ndn.utils.timestamp()
            name = Name.from_str('/catalog') + [Component.from_timestamp(timestamp)]
            logging.info(f'Read handle: sending interest to {Name.to_str(name)}')
            int_name = Name.normalize(int_name)
            int_name = Name.to_str(int_name)
            ex_int_name, meta_info, content = await self.app.express_interest(name, int_name.encode(), must_be_fresh=True, can_be_prefix=False, lifetime=6000)
            logging.info(f'Read handle: received Data Name from {Name.to_str(ex_int_name)}')
            if content:
                logging.info(f'Read handle: content received: {bytes(content).decode()}')
            else:
                logging.info(f'Read handle: content received: None')
            return bytes(content) if content else None
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
    async def _download_file(self, int_name):
        logging.info(f'Read handle: downloading file {self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"]}')
        downproc = subprocess.Popen(["sftp", self.curr_file_requests[Name.to_str(int_name[:-1])]["server"] + ":" + self.curr_file_requests[Name.to_str(int_name[:-1])]["srcdir"], self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"]],  shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.curr_file_requests[Name.to_str(int_name[:-1])]["downloading"] = True

        await self._get_memory_segment(int_name)
        while downproc.poll() is None:
            await aio.sleep(1)

        logging.info(f'Read handle: downloaded file {self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"]}')
        self.curr_file_requests[Name.to_str(int_name[:-1])]["downloading"] = False
        self.curr_file_requests[Name.to_str(int_name[:-1])]["downloaded"] = True
    async def _get_memory_segment(self, int_name):
        segment = int(Component.to_str(int_name[-1])[4:])
        while True:
            if Name.to_str(int_name[:-1]) in self.curr_file_requests.keys():
                if "numsegments" in self.curr_file_requests[Name.to_str(int_name[:-1])].keys():
                    break
                else:
                    await aio.sleep(0)
            else:
                await aio.sleep(0)

        while not os.path.exists(self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"]):
            await aio.sleep(0)
            if self.curr_file_requests[Name.to_str(int_name[:-1])]["downloaded"]:
                break

        logging.info(f'Read handle: getting {segment} out of {self.curr_file_requests[Name.to_str(int_name[:-1])]["numsegments"]-1} data')

        try:
            if segment != self.curr_file_requests[Name.to_str(int_name[:-1])]["numsegments"]-1:
                current_file_size = self._get_current_file_size(self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"])
                while current_file_size<((segment*self.segment_size)+1):
                    await aio.sleep(0)
                    current_file_size = self._get_current_file_size(self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"])
                memory = self._read_memory_segment(self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"], self.segment_size, segment)
            else:
                while self.curr_file_requests[Name.to_str(int_name[:-1])]["downloaded"] == False:
                    await aio.sleep(0)
                memory = self._read_memory_segment(self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"], self.segment_size, segment)
        except:
            return

        final_id = Component.from_number(self.curr_file_requests[Name.to_str(int_name[:-1])]["numsegments"]-1, Component.TYPE_SEGMENT)
        self.app.put_data(int_name, content=memory, freshness_period=None, final_block_id=final_id)
    async def _upload_storage_file(self, int_name):
        logging.info(f'Read handle: creating upload client')
        client = PutfileClient(app=self.app, prefix=Name.from_str(self.repo_name), repo_name=Name.from_str(self.repo_name))
        logging.info(f'Read handle: uploading {self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"]} to storage')
        await client.insert_file(self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"],
                                name_at_repo=int_name[:-1],
                                segment_size=self.segment_size,
                                freshness_period=0,
                                cpu_count=os.cpu_count())
        logging.info(f'Read handle: uploaded {self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"]} to storage')

        await aio.sleep(10)
        if os.path.exists(self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"]):
            os.remove(self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"])

    def _on_interest(self, int_name, int_param, _app_param):
        logging.info(f'On interest: {Name.to_str(int_name)}')
        aio.get_event_loop().create_task(self._on_interest_helper(int_name, int_param, _app_param))
    async def _on_interest_helper(self, int_name, int_param, _app_param):
        """
        Repo should not respond to any interest with MustBeFresh flag set.
        """
        if int_param.must_be_fresh:
            return
        data_bytes = self.storage.get_data_packet(int_name, int_param.can_be_prefix)

        if data_bytes:
            logging.info(f'Read handle: Found Data in Storage for {Component.to_str(int_name[-1])}')
            self.app.put_raw_packet(data_bytes)
            return

        if data_bytes==None:
            interest = make_interest(int_name, int_param)
            lp_packet = make_network_nack(interest, NackReason.NONE) #network nack

            if Component.to_str(int_name[-1])=="seg=0":
                ftp_command = await self._request_from_catalog(int_name)
                self.curr_file_requests[Name.to_str(int_name[:-1])] = {}
                self.curr_file_requests[Name.to_str(int_name[:-1])]["curlcommand"] = ftp_command.decode()
                if self.curr_file_requests[Name.to_str(int_name[:-1])]["curlcommand"]!="None":
                    logging.info(f'Read handle: setting up var current_file_requests')
                    curl_parts = self.curr_file_requests[Name.to_str(int_name[:-1])]["curlcommand"].split(' ')
                    link = curl_parts[-3]
                    link_parts = link.split('/')

                    self.curr_file_requests[Name.to_str(int_name[:-1])]["outputfile"] = curl_parts[-1]
                    self.curr_file_requests[Name.to_str(int_name[:-1])]["srcdir"] = '/' + '/'.join(link_parts[3:])
                    self.curr_file_requests[Name.to_str(int_name[:-1])]["server"] = link_parts[2]
                    self.curr_file_requests[Name.to_str(int_name[:-1])]["downloading"] = False
                    self.curr_file_requests[Name.to_str(int_name[:-1])]["downloaded"] = False
                    self.curr_file_requests[Name.to_str(int_name[:-1])]["size"] = await self._get_server_file_size(int_name)
                    self.curr_file_requests[Name.to_str(int_name[:-1])]["numsegments"] = self._how_many_segments(self.curr_file_requests[Name.to_str(int_name[:-1])]["size"], self.segment_size)

                    await self._download_file(int_name)
                    await self._upload_storage_file(int_name)
                else:
                    self.app.put_raw_packet(lp_packet)

                self.curr_file_requests.pop(Name.to_str(int_name[:-1]))
            else:
                await self._get_memory_segment(int_name)
        logging.info(f'Serve Data: {Name.to_str(int_name)}')