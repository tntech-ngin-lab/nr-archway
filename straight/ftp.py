from ftplib import FTP
import sys
import time
import logging

def ftp_download(app, translation):
    ftp = FTP(translation["host"], translation["username"] if translation["host"] != "null" else "anonymous", translation["password"] if translation["password"] != "null" else "")

    size = ftp.size(translation["filename"])
    if not size:
        return False
    logging.info(f'Size: {size}')

    packet_number = 0
    info = open('file_name', 'wb')

    def handle_ftp_binary(byte_chunk):
        nonlocal packet_number, mi
        info.write(byte_chunk)
        packet_number = packet_number + 1

    logging.info(f'Streaming the File Now')
    resp = ftp.retrbinary("RETR "+translation["filename"], callback=handle_ftp_binary, blocksize=8000)
    logging.info(f'Streaming Complete')
    info.close()
    ftp.quit()
    app.shutdown()

def main(app) -> int:
    logging.basicConfig(format='[%(asctime)s]%(levelname)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    start = time.time()
    translation = {}
    translation["host"] = "localhost"
    translation["username"] = "guest"
    translation["password"] = "welcomehere"
    translation["filename"] = "/files/mbstest"
    ftp_download(app, translation)
    print(f'Total time: {time.time() - start} seconds')

if __name__ == "__main__":
    main()