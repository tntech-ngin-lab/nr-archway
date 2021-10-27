from ftplib import FTP
import sys, os
import time
import logging
from ndn.app import NDNApp
from ndn.types import InterestNack, InterestTimeout, InterestCanceled, ValidationFailure
from ndn.encoding import Name, Component, InterestParam, MetaInfo, ContentType

def main(app) -> int:
    logging.basicConfig(format='[%(asctime)s]%(levelname)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    start = time.time()
    final_segment_num = 999
    final_id = Component.from_segment(final_segment_num)
    mi = MetaInfo(freshness_period=1000, final_block_id=final_id)
    int_name = Name.from_str("/GUEST/FILES/MBSTEST")

    packet_number = 0
    while packet_number < final_segment_num + 1:
        byte_chunk = bytearray(os.urandom(final_segment_num + 1))
        data_packet = app.prepare_data(int_name + [Component.from_number(packet_number, Component.TYPE_SEGMENT)], byte_chunk, meta_info=mi)
        packet_number = packet_number + 1
    data_packet = app.prepare_data(int_name + [Component.from_number(packet_number, Component.TYPE_SEGMENT)], byte_chunk, meta_info=mi)
    print(f'Total time: {time.time() - start} seconds')
    app.shutdown()

if __name__ == "__main__":
    app = NDNApp()
    try:
        app.run_forever(after_start=main(app))
    except FileNotFoundError:
        logging.warning(f'Error: could not connect to NFD')