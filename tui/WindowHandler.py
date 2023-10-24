# vim: expandtab smarttab ts=4

from common.configs import *

import threading
import curses
import traceback

from tui.SubPad import SubPad

class WindowHandler:
    def __init__(self, cmds, gfl):
        self.gfl = gfl
        self.cmds = cmds
        self.tasks_total = len(cmds)
        self.tasks_running_status = [True] * self.tasks_total
        self.output_buffer = [b''] * self.tasks_total
        self.mutex = threading.Lock()
        self.subpads_shown_height = DEFAULT_SUBPADS_SHOWN_HEIGHT
        self.user_control_offset = 0
        self.flag_refresh = False
        self.has_update = False
        self.inited = False

    def init_size(self):
        self.mutex.acquire()
        self.height, self.width = self.stdscr.getmaxyx()
        self.mutex.release()

    # Must be called after curses.initscr()
    def init_all(self, stdscr):
        self.stdscr = stdscr
        self.init_size()
        self.color_available = curses.has_colors()
        if self.color_available:
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)
            curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)

        self.mutex.acquire()
        self._refresh_header()
        self.subpads = [SubPad(self, i) for i in range(self.tasks_total)]
        self.inited = True
        self.mutex.release()

    def append_line(self, task_id, line):
        self.mutex.acquire()
        self.gfl.log('WindowHandler', 'append_line %d %s' % (task_id, str(line)), 2)
        self.output_buffer[task_id - 1] += line
        self.has_update = True
        self._update_buffers()
        self.mutex.release()

    def _update_buffers(self):
        self.gfl.log('WindowHandler', '_update_buffers', 10)
        for i in range(self.tasks_total):
            if self.output_buffer[i]:
                self.subpads[i]._swap_buffer(self.output_buffer[i])
                self.output_buffer[i] = b''
        self.has_update = False

    def mark_finished(self, task_id):
        self.mutex.acquire()
        self.tasks_running_status[task_id - 1] = False
        self.gfl.log('WindowHandler', 'mark_finished %d' % task_id, 3)
        if self.inited:
            self._refresh_all()
        self.mutex.release()

    def _refresh_header(self):
        finished = sum([ 1 for stat in self.tasks_running_status if not stat ])
        total = len(self.tasks_running_status)
        header = 'PARA-RUN V%s   Finished: %d / %d' % (VERSION, finished, total)

        if self.color_available:
            header += ' ' * (self.width - len(header))
            highlighted_len = self.width * finished // total
            self.stdscr.addstr(0, 0, header[:highlighted_len], curses.color_pair(1))
            self.stdscr.addstr(header[highlighted_len:])
        else:
            self.stdscr.addstr(0, 0, header)

    def _refresh_all(self):
        if not self.inited:
            self.mutex.release()
            return
        self.stdscr.clear()
        self._refresh_header()
        self.stdscr.refresh()
        for subpad in self.subpads:
            subpad.refresh()
        self.stdscr.refresh()

    def refresh_all(self):
        self.mutex.acquire()
        self._refresh_all()
        self.mutex.release()

    @staticmethod
    def main(stdscr, *args, **kwargs):
        assert(len(args) == 1 and len(kwargs) == 0)
        handler = args[0]

        curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)

        try:
            handler.init_all(stdscr)

            #stdscr.nodelay(True)

            running = True
            while running:
                ch = stdscr.getch()
                handler.gfl.log('CURSES', f'ch={ch}', 10)

                render_height_logical_total = HEADER_LINES + \
                    sum([(subpad.shown_height+2) for subpad in handler.subpads])

                inferior = (render_height_logical_total > handler.height) \
                        and (1 - render_height_logical_total) or 0
                if ch == curses.KEY_DOWN and handler.user_control_offset > inferior:
                    handler.user_control_offset -= 1
                    handler.gfl.log('CURSES', f'Key DOWN pressed. rhlt={render_height_logical_total} uco={handler.user_control_offset}', 2)
                    handler.refresh_all()
                elif ch == curses.KEY_UP and handler.user_control_offset < 0:
                    handler.user_control_offset += 1
                    handler.gfl.log('CURSES', f'Key UP pressed. rhlt={render_height_logical_total} uco={handler.user_control_offset}', 2)
                    handler.refresh_all()
                elif ch == curses.KEY_RESIZE:
                    handler.gfl.log('CURSES', f'Window resize. rhlt={render_height_logical_total} uco={handler.user_control_offset}', 2)
                    handler.init_size()
                    handler.refresh_all()
                elif ch == ord('q'):
                    if not True in handler.tasks_running_status:
                        running = False
        except KeyboardInterrupt:
            pass

        # Clean up curses
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    @staticmethod
    def start_main(window_handler):
        ret = -1
        try:
            ret = curses.wrapper(WindowHandler.main, window_handler)
        except Exception as e:
            window_handler.gfl.log('MAIN', ''.join(traceback.format_exception(None, e, e.__traceback__)))

        return ret
