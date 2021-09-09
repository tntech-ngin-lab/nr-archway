import asyncio as aio
import logging
import ndn.utils
import sys, os
from ftplib import FTP
import threading
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout, InterestCanceled, ValidationFailure
from ndn.encoding import Name, Component, InterestParam, MetaInfo, ContentType
from ..storage import Storage
sys.path.insert(0,'..')
from ndn_python_repo.clients import PutfileClient, DeleteClient

class ReadHandle(object):
    def __init__(self, app: NDNApp, storage: Storage, config: dict):
        self.app = app
        self.storage = storage
        self.db_config = config["db_config"]
        self.register_root = config['repo_config']['register_root']
        self.curr_file_requests = []
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
            clist = bytes(content).decode().split(",")
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
    def _stream_ndn_file(self, int_name, translation, thread_storage):
        return False
    def _stream_sftp_file(self, int_name, translation, thread_storage):
        return False
    def _stream_ftp_file(self, int_name, translation, thread_storage):
        if translation["host"] == "null" or translation["filename"] == "null":
            return False
        ftp = FTP(translation["host"], translation["username"] if translation["host"] != "null" else "anonymous", translation["password"] if translation["password"] != "null" else "")

        size = ftp.size(translation["filename"])
        if not size:
            return False
        final_segment_num = (size//self.segment_size)-1 if (size%self.segment_size==0) else (size//self.segment_size)
        final_id = Component.from_segment(final_segment_num)
        mi = MetaInfo(freshness_period=1000, final_block_id=final_id)
        logging.info(f'Size: {size}, Final_segment: {final_segment_num}, Meta: {mi}')

        packet_number = 0
        def handle_ftp_binary(byte_chunk):
            nonlocal packet_number, mi, thread_storage
            data_packet = self.app.prepare_data(int_name + [Component.from_number(packet_number, Component.TYPE_SEGMENT)], byte_chunk, meta_info=mi)
            self.app.put_raw_packet(data_bytes)
            thread_storage.put_data_packet(val["name"], data_packet)
            packet_number = packet_number + 1

        logging.info(f'Streaming the File Now')
        resp = ftp.retrbinary("RETR "+translation["filename"], callback=handle_ftp_binary, blocksize=self.segment_size)
        logging.info(f'Streaming Complete')
        ftp.quit()
        return True
    def _stream_aspera_file(self, int_name, translation, thread_storage):
        return False
    def _stream_http_file(self, int_name, translation, thread_storage):
        return False
    def _stream_https_file(self, int_name, translation, thread_storage):
        return False
    def _stream_file_to_repo(self, int_name, translation, thread_storage):
        if translation["interface"] == "ndn":
            return self._stream_ndn_file(int_name, translation, thread_storage)
        elif translation["interface"] == "sftp":
            return self._stream_sftp_file(int_name, translation, thread_storage)
        elif translation["interface"] == "ftp":
            return self._stream_ftp_file(int_name, translation, thread_storage)
        elif translation["interface"] == "aspera":
            return self._stream_aspera_file(int_name, translation, thread_storage)
        elif translation["interface"] == "http":
            return self._stream_http_file(int_name, translation, thread_storage)
        elif translation["interface"] == "https":
            return self._stream_https_file(int_name, translation, thread_storage)
        else:
            return False
    def _file_thread(self, int_name, int_param, _app_param):
        logging.info(f'Thread started for {Name.to_str(int_name)}')
        aio.run(self._file_thread_helper(int_name, int_param, _app_param))
    async def _file_thread_helper(self, int_name, int_param, _app_param):
        logging.info(f'Inside Thread Helper for {Name.to_str(int_name)}')
        translation = await self._request_from_catalog(int_name[:-1])
        if translation != None:
            thread_storage = create_storage(self.db_config)
            logging.info(f'Translation: {translation}')
            status = self._stream_file_to_repo(int_name[:-1], translation, thread_storage)
            if status == False:
                # return Nack
        else:
            # return Nack
        self.curr_file_requests.remove(Name.to_str(int_name[:-1]))
    def _on_interest(self, int_name, int_param, _app_param):
        logging.info(f'Read handle: On interest {Name.to_str(int_name)}')
        aio.get_event_loop().create_task(self._on_interest_helper(int_name, int_param, _app_param))
    async def _on_interest_helper(self, int_name, int_param, _app_param):
        if int_param.must_be_fresh: return
        data_bytes = self.storage.get_data_packet(int_name, int_param.can_be_prefix)
        if data_bytes:
            logging.info(f'Read handle: Found Data for {Component.to_str(int_name[-1])}')
            self.app.put_raw_packet(data_bytes)
            break
        else:
            # add if there are too many requests currently
            if Name.to_str(int_name[:-1]) not in self.curr_file_requests:
                self.curr_file_requests.append(Name.to_str(int_name[:-1]))
                thread = threading.Thread(target=self._file_thread, args=(int_name, int_param, _app_param,))
                thread.start()
        logging.info(f'Read handle: Served Data {Name.to_str(int_name)}')