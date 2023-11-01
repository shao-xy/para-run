# vim: expandtab smarttab ts=4

import os
import threading
import subprocess

from common.logger import TaskFileLogger
from common.configs import *

class Task(threading.Thread):
    def __init__(self, cmd, window_handler, thrd_index):
        super().__init__()
        self.cmd = cmd
        self.wh = window_handler
        self.index = thrd_index
        self.log_tag = f'Task {self.index}'

    def run(self):
        if not self.cmd:    return

        self.wh.gfl.log(self.log_tag, 'Thread start. ' + repr(self), 0)

        sfl = None
        if self.wh.log_output:
            sfl = TaskFileLogger(self.wh.start_ts, self.index, emergency_out=self.wh.gfl)

        subp = subprocess.Popen(self.cmd, shell = True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        for line in iter(subp.stdout.readline, b""):
            line = line.decode('utf-8')
            self.wh.append_line(self.index, line)
            if sfl:
                sfl.write(line)
                sfl.flush()

        returncode = subp.wait()

        self.wh.mark_finished(self.index, returncode)

        self.wh.gfl.log(self.log_tag, 'Thread end. ' + repr(self), 0)

    def __repr__(self):
        return f'[Task:idx={self.index},cmd="{self.cmd}"]'
