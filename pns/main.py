from .config import Config
from argparse import ArgumentParser
import json
import os
from threading import Thread
from multiprocessing import Process
import time
import sys
import signal
import asyncio
import threading
from .logger import logger

#
# quit_event = threading.Event()
# signal.signal(signal.SIGINT, lambda *_args: quit_event.set())

def main():
    data_default = "~/.pns"
    parser = ArgumentParser(
        "pns", description="Start pocket-name-service"
    )

    parser.add_argument(
        "-d",
        "--data-dir",
        type=str,
        default=data_default
    )

    args = parser.parse_args()

    file = open(os.path.join(args.data_dir,"data/config/config.json")).read()
    dict = json.loads(file)

    config = Config(**dict)

    logger.info("Starting PNS in directory {}".format(os.path.join(args.data_dir, "data")))
    # logger.info("Log file initialized at {}".format(os.path.join(args,data)))
    # why not?
    with open("pns/pns.txt") as myfile:
        logger.info(myfile.read())
    os.environ["pns_data_dir"] = os.path.join(args.data_dir, "data")

    from .indexer import start_pns
    from .rpc import boot

    t1 = Process(target=start_pns, args=(config,))
    t2 = Process(target=boot)

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

    # t1.join()
    # t2.join()
