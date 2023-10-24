# vim: expandtab smarttab ts=4

import curses
import traceback
import time

from common.configs import *

class SubPad:
    def __init__(self, wh, index):
        self.wh = wh
        self.index = index
        self.shown_height = wh.subpads_shown_height
        self.watching_at_end = True
        self.visible_pos = 0
        # Allow a separation line between tasks
        self.shown_pos_offset = index * (wh.subpads_shown_height + 2) + HEADER_LINES
        self.pad = curses.newpad(DEFAULT_SUBPADS_HEIGHT, wh.width)
        self.pad.scrollok(True)
        #self._swap_buffer(wh.output_buffer[index])

    def _swap_buffer(self, buffered_lines):
        self.pad.addstr(buffered_lines)
        self._refresh(self.watching_at_end)
        #self.wh.stdscr.refresh()

    def _refresh(self, force_watching_at_end=False):
        assert(self.wh.mutex.locked())
        if force_watching_at_end:
            self.watching_at_end = True

        # pad subtitle
        pad_title_pos = self.shown_pos_offset + self.wh.user_control_offset
        if HEADER_LINES <= pad_title_pos < self.wh.height - 1:
            if self.wh.color_available:
                #title = '[PROC %d] %s' % (self.index+1, self.wh.cmds[self.index])
                title = '[PROC %d] (%s) %s' % (self.index+1,
                        (self.wh.tasks_running_status[self.index] \
                            and 'RUNNING' or 'STOPPED'),
                        self.wh.cmds[self.index])
                title += ' ' * (self.wh.width - len(title))
                    
                self.wh.gfl.log('SubPad(%d)' % self.index, 'refresh pad_title_pos ' + str(pad_title_pos) + ' '  + title, 5)
                self.wh.stdscr.addstr(pad_title_pos, 0, title,
                        curses.color_pair(self.wh.tasks_running_status[self.index] and 2 or 3))
            else:
                title = '[PROC %d] (%s) %s' % (self.index+1,
                        (self.wh.tasks_running_status[self.index] \
                            and 'RUNNING' or 'STOPPED'),
                        self.wh.cmds[self.index])
                self.wh.gfl.log('SubPad(%d)' % self.index, 'refresh pad_title_pos ' + str(pad_title_pos) + title, 5)
                self.wh.stdscr.addstr(pad_title_pos, 0, title)

        # pad area: pad_render_offset_start ~ pad_render_offset_end
        # window area: 2 ~ self.wh.height
        pad_render_offset_start = self.shown_pos_offset + self.wh.user_control_offset + 1
        pad_render_offset_end = pad_render_offset_start + self.shown_height - 1
        render_offset_start = max(pad_render_offset_start, HEADER_LINES)
        render_offset_end = min(pad_render_offset_end, self.wh.height - 1)
        if render_offset_start >= self.wh.height \
        or render_offset_end < HEADER_LINES:
            return

        render_height = render_offset_end - render_offset_start + 1

        y, x = self.pad.getyx()
        if self.watching_at_end:
            if render_offset_start == HEADER_LINES:
                self.visible_pos = max(max(y, self.shown_height) - render_height, 0)
            else:
                self.visible_pos = max(y - self.shown_height, 0)
            #self.visible_pos = max(y - render_height + 1, 0)

        #if not True in self.wh.tasks_running_status:
        #    self.wh.stdscr.addstr(0, 0, f'Subpad {self.index}')
        #    self.wh.stdscr.refresh()
        #    time.sleep(1)

        # +2 is magic number, haha
        # This is because we reserve a line at the bottom
        self.pad.refresh(self.visible_pos, 0,
                render_offset_start, 0,
                render_offset_end, self.wh.width)

        #if not True in self.wh.tasks_running_status:
        #    if self.index == 0:
        #        time.sleep(2)
        #    else:
        #        time.sleep(1)

        self.wh.gfl.log('SubPad(%d)' % self.index,
                'refresh ' + repr(self) + f' region w={self.wh.width},h={self.wh.height},rs={render_offset_start},re={render_offset_end}', 3)
        #traceback.print_stack(file=self.wh.gfl._fl)

        self.wh.gfl.log('SubPad(%d)' % self.index, 'refresh ' + repr(self) + ' finish.', 5)
        self.wh.stdscr.refresh()

    def refresh(self, force_watching_at_end=False):
        self._refresh(force_watching_at_end)
        self.wh.stdscr.refresh()

    def __repr__(self):
        y, x = self.pad.getyx()
        return f'WindowHandler.SubPad(h={self.shown_height},v={self.visible_pos},o={self.shown_pos_offset},y={y},x={x})'

