from .config import Config
from .logger import logger
from argparse import ArgumentParser
from multiprocessing import Process
import json
import os
import time
import sys

#
# quit_event = threading.Event()
# signal.signal(signal.SIGINT, lambda *_args: quit_event.set())


def main():
    data_default = "/root/.pns"
    parser = ArgumentParser("pns", description="Start pocket-name-service")

    parser.add_argument("-d", "--data-dir", type=str, default=data_default)

    args = parser.parse_args()

    try:
        file = open(os.path.join(args.data_dir, "data/config/config.json")).read()
    except:
        logger.error("Config file not found at {}".format(os.path.join(args.data_dir, "data/config/config.json")))
        quit()
    dict = json.loads(file)

    print(dict)
    
    config = Config(**dict)

    logger.info(
        "Starting PNS in directory {}".format(os.path.join(args.data_dir, "data"))
    )
    
    with open("pns/pns.txt") as myfile:
        logger.info(myfile.read())
    os.environ["pns_data_dir"] = os.path.join(args.data_dir, "data")

    from .indexer import start_pns
    from .rpc import boot

    t1 = Process(target=start_pns, args=(config,))
    t2 = Process(target=boot, args=(config,))

    t1.daemon = True
    t2.daemon = True

    t1.start()
    t2.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.warning("Shutting down")
        t1.terminate()
        t2.terminate()
        t1.join()
        t2.join()
