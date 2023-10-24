# vim: expandtab smarttab ts=4

import os
import logging
from datetime import datetime
import threading

class Logger:
    def __init__(self):
        logging.basicConfig(level = logging.INFO, format = '%(asctime)s \033[1;32m[%(tag)s]\033[0m %(message)s')
        self._logger = logging.getLogger('MAIN')
        self._logger.setLevel(logging.INFO)

    def log(self, tag, message):
        if message.endswith('\n'):    message = message[:-1]
        for line in message.split('\n'):
            self._logger.info(line, extra={'tag': tag})

class FileLogger:
    def __init__(self, lvl = 0):
        if not os.path.isdir('.para-run/'):
            os.mkdir('.para-run/', mode=0o755)
        self._fl = open('.para-run/run.log', 'a')
        self._fl.write('\n')
        self._fl.flush()
        self.mutex = threading.Lock()
        self.lvl = lvl
    
    def log(self, tag, message, lvl = 0):
        self.mutex.acquire()
        if not self._fl or lvl > self.lvl:
            self.mutex.release()
            return
        for line in message.split('\n'):
            self._fl.write('%s %d [%s] %s\n' % (str(datetime.now()), lvl, tag, line))
            self._fl.flush()
        self.mutex.release()
    
    def __del__(self):
        self.mutex.acquire()
        self._fl.close()
        self._fl = None
        self.mutex.release()

