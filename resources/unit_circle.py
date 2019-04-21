import curses
import math

def add_circle_point(window, text, degrees, attribute):
  center_y = window.getmaxyx()[0]
  center_x = window.getmaxyx()[1]
  seg_length = min(center_y, center_x)/2
  window.addstr(
    center_y/2 - int(seg_length * math.cos(math.pi/180 * degrees)), 
    center_x/2 - len(text)/2 + int(2 * seg_length * math.sin(math.pi/180 * degrees)), 
    text,
    attribute
  )

def get_circle_resp(window):
  selected = 0

  center_y = window.getmaxyx()[0]
  center_x = window.getmaxyx()[1]
 
  text = list()
  text.append("Move cursor with the arrow keys")
  text.append("0 degrees is directly in front of you")
  text.append("180 degrees is directly behind you")
  text.append("Locate the direction of the ping as best you can")
  text.append("Press 'Enter' when you are done")

  for index, line in enumerate(text):
    window.addstr(center_y/2 - len(text)/2 + index, center_x/2 - len(line)/2, line)

  while True:
    for deg in range(0, 360, 10):
      add_circle_point(
        window, 
        str(deg), 
        deg, 
        curses.A_REVERSE if deg == selected else curses.A_NORMAL
      )

    window.refresh()
    ch = window.getch()

    if ch == curses.KEY_ENTER or ch == ord('\r') or ch == ord('\n'):
      return selected

    elif ch == curses.KEY_RIGHT:
      if selected == 90:
        continue
      elif selected > 270 or selected < 90:
        selected += 10
      else:
        selected -= 10

    elif ch == curses.KEY_LEFT:
      if selected == 270:
        continue
      if selected > 270 or selected < 90:
        selected -= 10
      else:
        selected += 10

    elif ch == curses.KEY_UP:
      if selected == 0:
        continue
      if selected < 180:
        selected -= 10
      else:
        selected += 10

    elif ch == curses.KEY_DOWN:
      if selected == 180:
        continue
      if selected < 180:
        selected += 10
      else:
        selected -= 10

    if selected == 360:
      selected = 0
    elif selected == -10:
      selected = 350

def main(stdscr):
  stdscr.clear()
  curses.curs_set(0)
  curses.cbreak()

  get_circle_resp(stdscr)

  curses.endwin()

curses.wrapper(main)
