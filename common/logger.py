# vim: expandtab smarttab ts=4

import sys
import os
import logging
from datetime import datetime
import threading
import traceback

from common.configs import *

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
    def __init__(self, path = '', mode='w', emergency_out=None):
        if not path:
            self._fl = None
        else:
            try:
                dn = os.path.dirname(path)
                if not os.path.isdir(dn):
                    os.makedirs(dn, mode=0o755, exist_ok=True)
                self._fl = open(path, mode)
            except IOError as e:
                if emergency_out:
                    emergency_out.write(''.join(traceback.format_exception(None, e, e.__traceback__)))
                    emergency_out.write(f'Create output file {path} failed.\n')
                    emergency_out.flush()

        self.mutex = threading.Lock()

    def _should_log(self, *args, **kwargs):
        return True

    def _gen_message(self, tag, msg_line, *args, **kwargs):
        # raise Exception('Abstract class method not implemented.')
        return '%s [%s] %s\n' % (str(datetime.now()), tag, msg_line)

    def log(self, tag, message, *args, **kwargs):
        self.mutex.acquire()
        if not self._fl or not self._should_log(*args, **kwargs):
            self.mutex.release()
            return
        for line in message.split('\n'):
            self._fl.write(self._gen_message(tag, line, *args, **kwargs))
            self._fl.flush()
        self.mutex.release()

    def _write_gen_message(self, msg):
        return msg

    def write(self, msg):
        self.mutex.acquire()
        if self._fl:
            self._fl.write(self._write_gen_message(msg))
        self.mutex.release()

    def flush(self):
        self.mutex.acquire()
        if self._fl:
            self._fl.flush()
        self.mutex.release()

    def dump_error(self, tag, e):
        if not isinstance(e, Exception):
            self.log(tag, str(e))
            return
        self.log(tag, ''.join(traceback.format_exception(None, e, e.__traceback__)))

    def __del__(self):
        #self.mutex.acquire()
        if self._fl:
            self._fl.close()
            self._fl = None
        #self.mutex.release()

class GlobalFileLogger(FileLogger):
    def __init__(self, lvl = 0):
        super().__init__(os.path.join(DEFAULT_RUNTIME_DIR, 'run.log'), mode='a', emergency_out=sys.stderr)
        self.lvl = lvl
        self._fl.write('\n')
        self._fl.flush()

    def _should_log(self, *args, **kwargs):
        lvl = (len(args) > 0) and args[0] or 0
        return lvl <= self.lvl

    def _gen_message(self, tag, msg_line, *args, **kwargs):
        lvl = (len(args) > 0) and args[0] or 0
        return '%s %d [%s] %s\n' % (str(datetime.now()), lvl, tag, msg_line)

    def _write_gen_message(self, msg):
        return '%s -1 [DIRECT] %s\n' % (str(datetime.now()), msg)

class TaskFileLogger(FileLogger):
    def __init__(self, global_start_ts, index, emergency_out):
        ts_str = global_start_ts.strftime('%Y%m%d-%H%M%S')
        output_path = os.path.join(DEFAULT_RUNTIME_DIR, ts_str, f'{index}.output')
        super().__init__(output_path, emergency_out=emergency_out)

    def _write_gen_message(self, msg):
        return '%s: %s' % (str(datetime.now()), msg)
