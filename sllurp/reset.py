from __future__ import print_function
import argparse
import time
import logging
from twisted.internet import reactor

import sllurp.llrp as llrp
from sllurp.llrp_proto import LLRPROSpec

logger = logging.getLogger('sllurp')
logger.propagate = False

def main():
    parser = argparse.ArgumentParser(description='Reset RFID Reader')
    parser.add_argument('host', help='hostname or IP address of RFID reader')
    parser.add_argument('-p', '--port', default=llrp.LLRP_PORT,
            help='port to connect to (default {})'.format(llrp.LLRP_PORT))
    parser.add_argument('-d', '--debug', action='store_true',
            help='show debugging output')
    parser.add_argument('-l', '--logfile')
    args = parser.parse_args()

    logLevel = (args.debug and logging.DEBUG or logging.INFO)
    logger.setLevel(logLevel)
    logFormat = '%(asctime)s %(name)s: %(levelname)s: %(message)s'
    formatter = logging.Formatter(logFormat)
    if args.logfile:
        fHandler = logging.FileHandler(args.logfile)
        fHandler.setFormatter(formatter)
        logger.addHandler(fHandler)
    else:
        sHandler = logging.StreamHandler()
        sHandler.setFormatter(formatter)
        logger.addHandler(sHandler)
    logger.log(logLevel, 'log level: {}'.format(logging.getLevelName(logLevel)))

    # spawn a thread to talk to the reader
    reader = llrp.LLRPReaderThread(args.host, args.port,
            start_inventory=False, disconnect_when_done=True,
            standalone=True)
    reader.setDaemon(True)
    reader.addCallback('READER_EVENT_NOTIFICATION', reader.stop_inventory)
    reader.start()

    # check every 0.1 seconds whether thread is done with its work (or whether
    # the user has pressed ^C)
    try:
        while reader.isAlive():
            reader.join(0.1)
    except KeyboardInterrupt:
        logger.fatal('interrupted')
        reactor.callFromThread(reactor.stop)

if __name__ == '__main__':
    main()
