#!/usr/bin/env python3
# vim: expandtab smarttab ts=4

import time
import curses
import threading

def run_thread(runstate):
    while not runstate[0]:
        time.sleep(1)

    cnt = 1
    while runstate[1] and cnt < 50:
        time.sleep(1)
        runstate[0].addstr(0, 0, str(cnt))
        runstate[0].refresh()
        cnt += 1

def curses_main(stdscr, *args):
    runstate = args[0]
    runstate[0] = stdscr

    stdscr.clear()
    stdscr.keypad(True)

    fout = open('.para-run/test.log', 'a')

    try:
        while runstate[1]:
            ch = stdscr.getch()
            if ch == curses.KEY_RESIZE:
                fout.write('Key resize pressed.\n')
                fout.flush()
            elif ch == curses.KEY_ENTER:
                fout.write('Key Enter pressed.\n')
                fout.flush()
            elif ord('a') <= ch <= ord('z'):
                fout.write('Key %s pressed.\n' % chr(ch))
                fout.flush()
            elif ch == ord('Q'):
                fout.write('Key "Q" pressed.\n')
                fout.flush()
                runstate[1] = False
            else:
                fout.write('Key with number %d pressed.\n' % ch)
                fout.flush()
    except KeyboardInterrupt:
        runstate[1] = False
        fout.write('Ctrl-C pressed. Exiting...\n')
        fout.flush()

    fout.close()
    return 0

def main():
    runstate = [None, True]
    w = threading.Thread(target=curses.wrapper, args=(curses_main,runstate))
    w.start()

    t = threading.Thread(target=run_thread, args=(runstate,))
    t.start()

    w.join()
    t.join()

if __name__ == '__main__':
    main()
