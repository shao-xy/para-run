#!/usr/bin/env python3

import curses
import time

def main1(stdscr):
	h, w = stdscr.getmaxyx()
	direction = 1
	pos = 0

	while True:
		#curses.setsyx(pos, 0)
		stdscr.move(pos, 0)
		stdscr.refresh()
		time.sleep(1)
		if pos + direction >= h:
			direction = -1
		elif pos + direction < 0:
			direction = 1
		pos += direction

def main(stdscr):
	h, w = stdscr.getmaxyx()
	x, y = 0, 0
	s = 'Hello world!'
	q = -1
	while q != ord('q'):
		stdscr.clear()
		stdscr.addstr(y, x, s)

if __name__ == '__main__':
    #curses.wrapper(main)
    curses.wrapper(main1)
