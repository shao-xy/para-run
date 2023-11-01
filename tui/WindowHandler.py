# vim: expandtab smarttab ts=4

from common.configs import *

import os
import threading
import curses
from datetime import datetime

from tui.SubPad import SubPad
from common.runner import Task

class WindowHandler:
    def __init__(self, cmds, gfl, args):
        self.gfl = gfl
        self.cmds = cmds
        self.tasks_total = len(cmds)
        self.tasks_running_status = [True] * self.tasks_total
        self.tasks_retcode = [0] * self.tasks_total
        self.output_buffer = [''] * self.tasks_total
        self.mutex = threading.Lock()
        self.subpads_shown_height = args.subwin_height
        self.log_output = args.log_output
        self.start_ts = datetime.now()
        self.user_control_offset = 0
        self.cursor_in_subpad = 0
        self.flag_refresh = False
        self.has_update = False
        self.inited = False

    def _init_size(self):
        self.height, self.width = self.stdscr.getmaxyx()
        #self.stdscr.erase()
        #self.stdscr.refresh()
        self.gfl.log('WindowHandler', f'Screen size resized to {self.height} * {self.width}', 1)

    # Must be called after curses.initscr()
    def init_all(self, stdscr):
        self.stdscr = stdscr
        #self.stdscr.leaveok(True)
        self.color_available = curses.has_colors()
        if self.color_available:
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_GREEN)
            curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)

        self.mutex.acquire()
        self._init_size()
        self._refresh_header()
        self.subpads = [SubPad(self, i) for i in range(self.tasks_total)]
        self.inited = True
        self.mutex.release()

    def append_line(self, task_id, line):
        self.mutex.acquire()
        self.gfl.log('WindowHandler', 'append_line %d %s' % (task_id, line), 2)
        self.output_buffer[task_id - 1] += line
        self.has_update = True
        self._update_buffers()
        self.mutex.release()

    def _update_buffers(self):
        self.gfl.log('WindowHandler', '_update_buffers', 10)
        for i in range(self.tasks_total):
            if self.output_buffer[i]:
                self.subpads[i]._swap_buffer(self.output_buffer[i])
                self.output_buffer[i] = ''
        self.show_cursor(True)
        self.has_update = False

    def mark_finished(self, task_id, returncode):
        self.mutex.acquire()
        self.tasks_running_status[task_id - 1] = False
        self.tasks_retcode[task_id - 1] = returncode
        self.gfl.log('WindowHandler', 'mark_finished %d returncode %d' % (task_id, returncode), 3)
        if self.inited:
            self._refresh_all()
        self.mutex.release()

    def _gen_header(self, finished, total):
        title = 'PARA-RUN V%s' % VERSION
        finish_prompt = 'Finished: %d / %d' % (finished, total)
        process_prompt = '%d%%' % (finished * 100 // total)

        len_title = len(title)
        len_finish_prompt = len(finish_prompt)
        len_process_prompt = len(process_prompt)
        width = self.width

        header = ''
        if width >= len_title + 2 + 2 * len_finish_prompt:
            header += finish_prompt + ' ' * ((width-len_title)//2-len_finish_prompt) \
                        + title
            header += ' ' * (width - len(header) - len_process_prompt) + process_prompt
        elif width >= len_title + 2 + 2 * len_process_prompt:
            header += ' ' * ((width - len_title) // 2) + title
            header += ' ' * (width - len(header) - len_process_prompt) + process_prompt
        elif width >= len_title:
            header += ' ' * ((width - len_title) // 2) + title
            header += ' ' * (width - len(header))
        return header

    def _refresh_header(self):
        finished = sum([ 1 for stat in self.tasks_running_status if not stat ])
        total = len(self.tasks_running_status)
        header = self._gen_header(finished, total)

        if self.color_available:
            highlighted_len = self.width * finished // total
            self.stdscr.addstr(0, 0, header[:highlighted_len], curses.color_pair(1))
            self.stdscr.addstr(header[highlighted_len:])
        else:
            self.stdscr.addstr(0, 0, header)

    def get_cursor_posy(self):
        return self.subpads[self.cursor_in_subpad].get_cursor_posy()

    def show_cursor(self, refresh_stdscr = False):
        pos_y = self.get_cursor_posy()

        if pos_y < HEADER_LINES:
            pos_y = HEADER_LINES
        elif pos_y >= self.height:
            pos_y = self.height - 1
        #curses.setsyx(pos_y, 0)
        self.stdscr.move(pos_y, 0)
        if refresh_stdscr:
            self.stdscr.refresh()

        self.gfl.log('WindowHandler', f'show cursor ({pos_y},0)', 5)

    def _refresh_all(self):
        if not self.inited:
            return
        self.stdscr.clear()
        self._refresh_header()
        self.stdscr.refresh()
        for subpad in self.subpads:
            subpad._refresh()
        self.show_cursor()
        self.stdscr.refresh()

    def refresh_all(self):
        self.mutex.acquire()
        self._refresh_all()
        self.mutex.release()

    def maybe_move_cursor(self):
        cursor_posy = self.get_cursor_posy()
        while cursor_posy < HEADER_LINES:
            if self.cursor_in_subpad < len(self.subpads) - 1:
                self.cursor_in_subpad += 1
                cursor_posy = self.get_cursor_posy()
            else:
                break

        while cursor_posy >= self.height:
            if self.cursor_in_subpad > 0:
                self.cursor_in_subpad -= 1
                cursor_posy = self.get_cursor_posy()
            else:
                break

    def maybe_move_viewport(self):
        pos_y = self.get_cursor_posy()

        # We don't show cursor here:
        if pos_y < HEADER_LINES:
            self.user_control_offset += HEADER_LINES - pos_y
            self.refresh_all()
            self.gfl.log('WindowHandler', f'maybe_move_viewport uco set to {self.user_control_offset}', 5)
        elif pos_y >= self.height:
            self.user_control_offset -= pos_y - self.height + 1
            self.refresh_all()
            self.gfl.log('WindowHandler', f'maybe_move_viewport uco set to {self.user_control_offset}', 5)
        else:
            self.show_cursor()

    def move_cursor_in_pad(self, direction):
        self.subpads[self.cursor_in_subpad].move_cursor(direction)
        self.maybe_move_viewport()

    def adjust_subpad_height(self, size):
        self.mutex.acquire()
        real_adjust_size = self.subpads[self.cursor_in_subpad].adjust_height(size)
        for i in range(self.cursor_in_subpad + 1, len(self.subpads)):
            self.subpads[i].shown_pos_offset += real_adjust_size
        self._refresh_all()
        self.mutex.release()

    def start_worker_threads(self, cmds):
        tasks_acc = 1
        tasks_total = len(cmds)
        self.thrd_pool = []

        for cmd in cmds:
            t = Task(cmd, self, tasks_acc)
            t.start()
            self.thrd_pool.append(t)
            tasks_acc += 1

        return True

    def join_worker_threads(self):
        if not hasattr(self, 'thrd_pool'):
            return

        for t in self.thrd_pool:
            t.join()

    @staticmethod
    def curses_clean(stdscr):
        # Clean up curses
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    @staticmethod
    def main(stdscr, *args, **kwargs):
        assert(len(args) == 2 and len(kwargs) == 0)
        handler = args[0]
        cmds = args[1]

        curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)

        try:
            handler.init_all(stdscr)
            running = True
            if not handler.start_worker_threads(cmds):
                running = False

            while running:
                ch = stdscr.getch()
                handler.gfl.log('CURSES', f'ch={ch}', 5)
                if ch == curses.KEY_RESIZE:
                    handler.gfl.log('CURSES', f'Window resize.', 2)
                    handler._init_size()
                    handler.mutex.acquire()
                    handler.gfl.log('CURSES', f'Window resize start refresh.', 2)
                    #handler._init_size()
                    handler._refresh_all()
                    handler.gfl.log('CURSES', f'Window resize refresh end.', 2)
                    handler.mutex.release()
                    continue

                render_height_logical_total = HEADER_LINES + \
                    sum([(subpad.shown_height+2) for subpad in handler.subpads])

                inferior = (render_height_logical_total > handler.height) \
                        and (1 - render_height_logical_total) or 0
                if ch == ord('e') and handler.user_control_offset > inferior:
                    handler.user_control_offset -= 1
                    handler.maybe_move_cursor()
                    handler.gfl.log('CURSES', f'Key e pressed. rhlt={render_height_logical_total} uco={handler.user_control_offset}', 2)
                    handler.refresh_all()
                elif ch == ord('y') and handler.user_control_offset < 0:
                    handler.user_control_offset += 1
                    handler.maybe_move_cursor()
                    handler.gfl.log('CURSES', f'Key y pressed. rhlt={render_height_logical_total} uco={handler.user_control_offset}', 2)
                    handler.refresh_all()
                elif ch == curses.KEY_DOWN and handler.cursor_in_subpad < len(handler.subpads) - 1:
                    handler.cursor_in_subpad += 1
                    handler.maybe_move_viewport()
                    handler.gfl.log('CURSES', f'Key DOWN pressed. cp={handler.cursor_in_subpad},cip={handler.subpads[handler.cursor_in_subpad].cursor_pos}', 2)
                elif ch == curses.KEY_UP:
                    if handler.cursor_in_subpad > 0:
                        handler.cursor_in_subpad -= 1
                        handler.maybe_move_viewport()
                        handler.gfl.log('CURSES', f'Key UP pressed. cp={handler.cursor_in_subpad},cip={handler.subpads[handler.cursor_in_subpad].cursor_pos}', 2)
                    else:
                        handler.user_control_offset = 0
                        handler.maybe_move_cursor()
                        handler.gfl.log('CURSES', f'Key UP pressed. cp={handler.cursor_in_subpad},cip={handler.subpads[handler.cursor_in_subpad].cursor_pos}', 2)
                        handler.refresh_all()
                elif ch == ord('j'):
                    handler.move_cursor_in_pad(1)
                    handler.gfl.log('CURSES', f'Key j pressed. cp={handler.cursor_in_subpad},cip={handler.subpads[handler.cursor_in_subpad].cursor_pos}', 2)
                elif ch == ord('k'):
                    handler.move_cursor_in_pad(-1)
                    handler.gfl.log('CURSES', f'Key k pressed. cp={handler.cursor_in_subpad},cip={handler.subpads[handler.cursor_in_subpad].cursor_pos}', 2)
                elif ch == ord('+'):
                    handler.adjust_subpad_height(1)
                    handler.gfl.log('CURSES', f'Key + pressed. cp={handler.cursor_in_subpad}', 2)
                elif ch == ord('-'):
                    handler.adjust_subpad_height(-1)
                    handler.gfl.log('CURSES', f'Key - pressed. cp={handler.cursor_in_subpad}', 2)
                elif ch == ord('q'):
                    if not True in handler.tasks_running_status:
                        running = False
        except KeyboardInterrupt:
            pass

        WindowHandler.curses_clean(stdscr)

    @staticmethod
    def start_main(window_handler, cmds):
        ret = -1
        try:
            ret = curses.wrapper(WindowHandler.main, window_handler, cmds)
        except Exception as e:
            window_handler.gfl.dump_error('MAIN', e)
            WindowHandler.curses_clean(stdscr)

        window_handler.join_worker_threads()

        return ret
