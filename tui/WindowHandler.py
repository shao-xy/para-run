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

    def append_line(self, task_id, line):
        self.mutex.acquire()
        self.gfl.log('WindowHandler', 'append_line %d %s' % (task_id, str(line)), 2)
        self.output_buffer[task_id - 1] += line
        self.has_update = True
        self.mutex.release()

    def maybe_render_all_buffers(self):
        if self.flag_refresh:
            self.refresh_all()
            self.flag_refresh = False
            return

        if not self.has_update:
            return

        self.mutex.acquire()
        self.gfl.log('WindowHandler', 'maybe_render_all_buffers', 10)
        for i in range(self.tasks_total):
            if self.output_buffer[i]:
                self.subpads[i]._swap_buffer(self.output_buffer[i])
                self.output_buffer[i] = b''
        self.mutex.release()

        self.stdscr.refresh()

    def mark_finished(self, task_id):
        if not self.inited:    return
        self.mutex.acquire()
        self.tasks_running_status[task_id - 1] = False
        self.gfl.log('WindowHandler', 'mark_finished %d' % task_id, 3)
        self._refresh_header()
        self.subpads[task_id - 1].refresh()
        self.stdscr.refresh()
        self.mutex.release()

    def init_size(self):
        self.height, self.width = self.stdscr.getmaxyx()

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

    def _refresh_header(self):
        if self.color_available:
            self.stdscr.addstr(0, 0, 'PARA-RUN version %s' % VERSION, curses.color_pair(1))
        else:
            self.stdscr.addstr(0, 0, 'PARA-RUN version %s' % VERSION)
        """
        for i in range(len(self.subpads)):
            subpad = self.subpads[i]
            show_pos = subpad.shown_pos_offset + self.user_control_offset - 1
            if show_pos < HEADER_LINES:
                continue
            if show_pos >= self.height:
                break
            if self.color_available:
                if self.tasks_running_status[i]:
                    self.stdscr.addstr(show_pos, 0, '[PROC %d] (RUNNING)' % (i+1), curses.color_pair(2))
                else:
                    self.stdscr.addstr(show_pos, 0, '[PROC %d] (STOPPED)' % (i+1), curses.color_pair(3))
            else:
                if self.tasks_running_status[i]:
                    self.stdscr.addstr(show_pos, 0, '[PROC %d] (RUNNING)' % (i+1))
                else:
                    self.stdscr.addstr(show_pos, 0, '[PROC %d] (STOPPED)' % (i+1))
        """

    def refresh_all(self):
        self.mutex.acquire()
        if not self.inited:
            self.mutex.release()
            return
        self.stdscr.clear()
        self._refresh_header()
        self.stdscr.refresh()
        for subpad in self.subpads:
            subpad.refresh()
        self.mutex.release()
        self.stdscr.refresh()

    def mark_refresh_all(self):
        self.flag_refresh = True

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

            stdscr.nodelay(True)

            running = True
            while running:
                ch = stdscr.getch()
                handler.gfl.log('CURSES', f'ch={ch}', 10)

                render_height_logical_total = HEADER_LINES + \
                    sum([(subpad.shown_height+1) for subpad in handler.subpads])

                inferior = (render_height_logical_total > handler.height) \
                        and (1 - render_height_logical_total) or 0
                if ch == -1:
                    handler.maybe_render_all_buffers()
                elif ch == curses.KEY_DOWN and handler.user_control_offset > inferior:
                    handler.user_control_offset -= 1
                    handler.gfl.log('CURSES', f'Key DOWN pressed. rhlt={render_height_logical_total} uco={handler.user_control_offset}', 2)
                    handler.mark_refresh_all()
                elif ch == curses.KEY_UP and handler.user_control_offset < 0:
                    handler.user_control_offset += 1
                    handler.gfl.log('CURSES', f'Key UP pressed. rhlt={render_height_logical_total} uco={handler.user_control_offset}', 2)
                    handler.mark_refresh_all()
                elif ch == curses.KEY_RESIZE:
                    handler.gfl.log('CURSES', f'Window resize. rhlt={render_height_logical_total} uco={handler.user_control_offset}', 2)
                    handler.init_size()
                    handler.mark_refresh_all()
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
