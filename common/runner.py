# vim: expandtab smarttab ts=4

import threading
import subprocess

from tui.WindowHandler import WindowHandler

def run_single_cmd(cmd, window_handler, thrd_index):
    if not cmd:    return
    subp = subprocess.Popen(cmd, shell = True, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in iter(subp.stdout.readline, b""):
        window_handler.append_line(thrd_index, line)

    window_handler.mark_finished(thrd_index)

def para_run(cmds, gfl):
    window_handler = WindowHandler(cmds, gfl)
    wht = threading.Thread(target=WindowHandler.start_main, args = (window_handler, ))
    wht.start()

    tasks_acc = 1
    tasks_total = len(cmds)
    thrd_pool = []
    for cmd in cmds:
        t = threading.Thread(target = run_single_cmd, args = (cmd, window_handler, tasks_acc))
        t.start()
        thrd_pool.append(t)
        tasks_acc += 1

    for t in thrd_pool:
        t.join()
    wht.join()

