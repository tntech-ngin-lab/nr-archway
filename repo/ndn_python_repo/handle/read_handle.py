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
    def __init__(self, app: NDNApp, storage: Storage, config: dict):
        self.app = app
        self.storage = storage
        self.register_root = config['repo_config']['register_root']
        self.repo_name = config['repo_config']['repo_name']
        self.curr_file_requests = []
        self.failed_requests = []
        self.curr_requests_limit = 2 # number of threads or can fill requests
        self.segment_size = 8000
        if self.register_root:
            self.listen(Name.from_str('/'))
    def listen(self, prefix):
        self.app.route(prefix)(self._on_interest)
        logging.info(f'Read handle: listening to {Name.to_str(prefix)}')
    def unlisten(self, prefix):
        aio.ensure_future(self.app.unregister(prefix))
        logging.info(f'Read handle: stop listening to {Name.to_str(prefix)}')
    async def _request_from_catalog(self, int_name):
        try:
            name = Name.from_str('/catalog') + int_name
            logging.info(f'Read handle: sending interest to {Name.to_str(name)}')
            ex_int_name, meta_info, content = await self.app.express_interest(name, must_be_fresh=True, can_be_prefix=False, lifetime=6000)
            logging.info(f'Read handle: received Data Name from {Name.to_str(ex_int_name)}')
            if content:
                logging.info(f'Read handle: content received: {bytes(content).decode()}')
            else:
                logging.info(f'Read handle: content received: None')
            clist = list(content.split(","))
            if len(clist) != 5:
                return None
            translation = {}
            translation["interface"] = clist[0] if clist[0]!="null" else None
            translation["host"] = clist[1] if clist[1]!="null" else None
            translation["filename"] = clist[2] if clist[2]!="null" else None
            translation["username"] = clist[3] if clist[3]!="null" else None
            translation["password"] = clist[4] if clist[4]!="null" else None
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
    async def _stream_file_to_repo(self, int_name, translation):
        pass
    def _on_interest(self, int_name, int_param, _app_param):
        logging.info(f'On interest: {Name.to_str(int_name)}')
        aio.get_event_loop().create_task(self._on_interest_helper(int_name, int_param, _app_param))
    async def _on_interest_helper(self, int_name, int_param, _app_param):
        if int_param.must_be_fresh: return
        data_bytes = None
        while True:
            data_bytes = self.storage.get_data_packet(int_name, int_param.can_be_prefix)
            if data_bytes:
                logging.info(f'Read handle: Found Data for {Component.to_str(int_name[-1])}')
                self.app.put_raw_packet(data_bytes)
                return
            else:
                if Name.to_str(int_name[:-1]) not in self.curr_file_requests:
                    if Name.to_str(int_name[:-1]) in self.failed_requests:
                        logging.info(f'Read handle: No Data, No translation for {Component.to_str(int_name[-1])}')
                        self.app.put_data(int_name, content=None, content_type=ContentType.NACK)
                        return
                    else:
                        # start thread instead
                        self.curr_file_requests.append(Name.to_str(int_name[:-1]))
                        translation = await self._request_from_catalog(int_name[:-1])
                        if translation != None:
                            status = await self._stream_file_to_repo(int_name, translation)
                            if status == False:
                                self.failed_requests.append(Name.to_str(int_name[:-1]))
                                #delete all packets from storage
                        else:
                            self.failed_requests.append(Name.to_str(int_name[:-1]))
                        self.curr_file_requests.remove(Name.to_str(int_name[:-1]))
            await aio.sleep(0.1)