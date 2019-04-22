###############################################################################
#
#  USC EE322 Final Project - Spring 2019
#
###############################################################################

from struct import unpack
from scipy.io import wavfile
from scipy.signal import fftconvolve
from numpy import convolve
from time import sleep
import os
import wave
import numpy as np
import sounddevice as sd
import soundfile as sf
import curses
import math
import random

def read_dat(side, elevation, azimuth):
  """
  @brief      { Reads am hrtf file for a given direction if one exists }

  @param      side       L / R
  @param      elevation  -40 to +90 by increments of 10
  @param      azimuth    0 to 355 by increments of 5

  @return     { returns an array of the transfer data or None if one is not available }
  """
  dat = list()

  path = "full/elev{:01d}/{:s}{:01d}e{:03d}a.dat".format(
  	elevation, 
  	side, 
  	elevation, 
  	azimuth
  )

  if not os.path.exists(path):
    return None
  else:
    with open(path, "rb") as f:
      while True:
        short = f.read(2)
        if short:
          # byte ordering must be in reverse: '!'
          dat.append(float(unpack("!h", short)[0]) / 32768)
        else:
          break
  return np.array(dat)

def load_hrtf():
  """
  @brief      { Loads all the hrtfs available }

  @return     { 
    data structure for HRTF data:
      elevation ranges from -40 to +90 in increments of 10
      azimuth ranges from 0 to 355 in increments of 5
      left and right
    3D array of key value pairs:
 
    HRTF = {
      L: {
        -40 : {
          0 : list(data),
          .
          .
          .
        },
      .
      .
      .
      },
      R: {
        .
        .
        .
      }
    }
 
  }
  """
  hrtf = dict()
  hrtf['L'] = dict()
  hrtf['R'] = dict()
  for side in hrtf.keys():
    for elevation in range(-40, 90, 10):
      #  all of the elevations are there, just the azimuths get cut off
      hrtf[side][elevation] = dict()
      for azimuth in range(0, 355, 5):
        response = read_dat(side, elevation, azimuth)
        if response is not None:
          hrtf[side][elevation][azimuth] = response

  return hrtf

def get_closest_key(keys, target):
  """
  @brief      { Gets the closest key }
  
  @param      keys    The keys
  @param      target  The target
  
  @return     { The closest key }
  """
  return target if target in keys else min(
  	keys, 
  	key=lambda k: abs(k - target)
  )

def convolve_stereo(data, hrtf, elevation, azimuth):
  """
  @brief      { performs the Fast Fourier Transform on the given array }

  @param      data       The data
  @param      elevation  The requested elevation
  @param      azimuth    The requested azimuth

  @return     { stereo matrix ready to be played }
  """
  if elevation > 90:
  	elevation = 90
  elif elevation < -40:
  	elevation = -40

  if azimuth < 0:
  	while azimuth < 0:
  	  azimuth = azimuth + 360

  azimuth = azimuth % 360

  # the layout for L and R are the same
  actual_elevation = get_closest_key(
  	hrtf['L'].keys(), 
  	elevation
  )
  actual_azimuth = get_closest_key(
  	hrtf['L'][actual_elevation].keys(), 
  	azimuth
  )

  left = convolve(
  	data, 
  	hrtf['L'][actual_elevation][actual_azimuth]
  )
  right = convolve(
  	data, 
  	hrtf['L'][actual_elevation][0 if actual_azimuth is 0 else 360 - actual_azimuth]
  )
  stereo = np.transpose([left, right])
  return stereo

def add_circle_point(window, text, degrees, radius, attribute):
  center_y = window.getmaxyx()[0]
  center_x = window.getmaxyx()[1]
  seg_length = radius
  window.addstr(
    center_y/2 - int(seg_length * math.cos(math.pi/180 * degrees)), 
    center_x/2 - len(text)/2 + int(2 * seg_length * math.sin(math.pi/180 * degrees)), 
    text,
    attribute
  )

def main(stdscr):
  hrtf = load_hrtf()
  data, fs = sf.read("ping.wav")

  stdscr.clear()
  curses.curs_set(0)
  curses.cbreak()

  trial_1_source = list()
  trial_1_resp = list()
  trial_2_source = list()
  trial_2_resp = list()
  trial_3_source = list()
  trial_3_resp = list()

  selected = 0

  center_y = stdscr.getmaxyx()[0]
  center_x = stdscr.getmaxyx()[1]

  curses.init_pair(1, curses.COLOR_RED, 0)

  directions = list()

  for item in range(0, 10):
    directions.append(random.randrange(0, 360, 10))

  #############################################################################
  #
  # Part 0 - Intro
  #
  #############################################################################

  text = list()
  text.append("Welcome to our EE322 final project!")
  text.append("Move cursor with the arrow keys")
  text.append("0 degrees is directly in front of you")
  text.append("180 degrees is directly behind you")
  text.append("Hover the cursor over the number and")
  text.append("press 'Enter' to select")

  for index, line in enumerate(text):
    stdscr.addstr(
      center_y/2 - int(math.ceil(len(text)/2)) + index,
      center_x/2 - int(math.ceil(len(line)/2)),
      line
    )

  ready = "Ready? "
  stdscr.addstr(
    center_y/2 + int(math.ceil(len(text)/2)), 
    center_x/2 - int(math.ceil(len(ready)/2)),
    ready 
  )
  enter = "[ENTER]"
  stdscr.addstr(
    center_y/2 + int(math.ceil(len(text)/2)), 
    center_x/2 + int(math.ceil(len(ready)/2)),
    enter,
    curses.A_BLINK | curses.A_REVERSE
  )

  while True:
    for deg in range(0, 360, 10):
        add_circle_point(
          stdscr, 
          str(deg), 
          deg,
          min(center_y, center_x)/2,
          curses.A_REVERSE if deg == selected else curses.A_NORMAL
        )

    ch = stdscr.getch()
    
    if ch == curses.KEY_ENTER or ch == ord('\r') or ch == ord('\n'):
      enter_clear = "       "
      stdscr.addstr(
        center_y/2 + int(math.ceil(len(text)/2)), 
        center_x/2 + int(math.ceil(len(ready)/2)),
        enter_clear,
        curses.A_NORMAL
      )
      break

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

  #############################################################################
  #
  # Part 1 - Ping from random locations, record results
  #
  #############################################################################
  
  stdscr.clear()

  text = list()
  text.append("Set 1: Best Guess")
  text.append("Locate the direction of the ping as best you can")

  for index, line in enumerate(text):
    stdscr.addstr(
      center_y/2 - int(math.ceil(len(text)/2)) + index,
      center_x/2 - int(math.ceil(len(line)/2)),
      line
    )

  ready = "Ready? "
  stdscr.addstr(
    center_y/2 + int(math.ceil(len(text)/2)), 
    center_x/2 - int(math.ceil(len(ready)/2)),
    ready 
  )
  enter = "[ENTER]"
  stdscr.addstr(
    center_y/2 + int(math.ceil(len(text)/2)), 
    center_x/2 + int(math.ceil(len(ready)/2)),
    enter,
    curses.A_BLINK | curses.A_REVERSE
  )

  while True:
    for deg in range(0, 360, 10):
        add_circle_point(
          stdscr, 
          str(deg), 
          deg,
          min(center_y, center_x)/2,
          curses.A_REVERSE if deg == selected else curses.A_NORMAL
        )

    ch = stdscr.getch()
    
    if ch == curses.KEY_ENTER or ch == ord('\r') or ch == ord('\n'):
      enter_clear = "       "
      stdscr.addstr(
        center_y/2 + int(math.ceil(len(text)/2)), 
        center_x/2 + int(math.ceil(len(ready)/2)),
        enter_clear,
        curses.A_NORMAL
      )
      break

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

  for trial in range(0, 10):
    for index in range(5, -1, -1):
      countdown = "Ping in {}".format(index)
      stdscr.addstr(
        center_y/2 + int(math.ceil(len(text)/2)), 
        center_x/2 - int(math.ceil(len(countdown)/2)),
        countdown
      )
      stdscr.refresh()
      sleep(1)

    stdscr.refresh()

    trial_1_source.append(directions[trial])

    stereo = convolve_stereo(data[:, 0], hrtf, 0, directions[trial])
    sd.play(stereo, fs, blocking=False)
    sd.wait()

    while True:
      for deg in range(0, 360, 10):
        add_circle_point(
          stdscr, 
          str(deg), 
          deg,
          min(center_y, center_x)/2,
          curses.A_REVERSE if deg == selected else curses.A_NORMAL
        )

      ch = stdscr.getch()
      
      if ch == curses.KEY_ENTER or ch == ord('\r') or ch == ord('\n'):
        break

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

    trial_1_resp.append(selected)

  #############################################################################
  #
  # Part 2 - Ping from random locations, notify the player, record results
  #
  #############################################################################

  stdscr.clear()

  text = list()
  text.append("Set 2: Training")
  text.append("A red asterisk (*) will be shown")
  text.append("to indicate where the ping is coming from")
  text.append("Important: The red asterisk may not represent")
  text.append("exactly where you hear it from")
  text.append("Locate the direction of the ping as best you can")

  for index, line in enumerate(text):
    stdscr.addstr(
      center_y/2 - int(math.ceil(len(text)/2)) + index, 
      center_x/2 - int(math.ceil(len(line)/2)), 
      line
    )

  ready = "Ready? "
  stdscr.addstr(
    center_y/2 + int(math.ceil(len(text)/2)), 
    center_x/2 - int(math.ceil(len(ready)/2)),
    ready 
  )
  enter = "[ENTER]"
  stdscr.addstr(
    center_y/2 + int(math.ceil(len(text)/2)), 
    center_x/2 + int(math.ceil(len(ready)/2)),
    enter,
    curses.A_BLINK | curses.A_REVERSE
  )

  while True:
    for deg in range(0, 360, 10):
        add_circle_point(
          stdscr, 
          str(deg), 
          deg,
          min(center_y, center_x)/2,
          curses.A_REVERSE if deg == selected else curses.A_NORMAL
        )

    ch = stdscr.getch()
    
    if ch == curses.KEY_ENTER or ch == ord('\r') or ch == ord('\n'):
      enter_clear = "       "
      stdscr.addstr(
        center_y/2 + int(math.ceil(len(text)/2)), 
        center_x/2 + int(math.ceil(len(ready)/2)),
        enter_clear,
        curses.A_NORMAL
      )
      break

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

  for trial in range(0, 10):

    trial_2_source.append(directions[trial])

    add_circle_point(
      stdscr, 
      "*", 
      directions[trial], 
      min(center_y, center_x)/2 - 2, 
      curses.color_pair(1)
    )
    stdscr.refresh()

    for index in range(5, -1, -1):
      countdown = "Ping in {}".format(index)
      stdscr.addstr(
        center_y/2 + int(math.ceil(len(text)/2)), 
        center_x/2 - int(math.ceil(len(countdown)/2)), 
        countdown
      )
      stdscr.refresh()
      sleep(1)

    stereo = convolve_stereo(data[:, 0], hrtf, 0, directions[trial])
    sd.play(stereo, fs)
    sd.wait()

    while True:
      for deg in range(0, 360, 10):
        add_circle_point(
          stdscr, 
          str(deg), 
          deg,
          min(center_y, center_x)/2,
          curses.A_REVERSE if deg == selected else curses.A_NORMAL
        )

      ch = stdscr.getch()
      
      if ch == curses.KEY_ENTER or ch == ord('\r') or ch == ord('\n'):
        break

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

    trial_2_resp.append(selected)

    add_circle_point(
      stdscr, 
      " ", 
      directions[trial], 
      min(center_y, center_x)/2 - 2,
      curses.A_NORMAL
    )
    stdscr.refresh()

  #############################################################################
  #
  # Part 3 - Ping from random locations, record results
  #
  #############################################################################
  
  stdscr.clear()

  text = list()
  text.append("Set 3: Training Results")
  text.append("Now, there won't be any asterisk")
  text.append("Locate the direction of the ping as best you can")

  for index, line in enumerate(text):
    stdscr.addstr(
      center_y/2 - int(math.ceil(len(text)/2)) + index,
      center_x/2 - int(math.ceil(len(line)/2)),
      line
    )

  ready = "Ready? "
  stdscr.addstr(
    center_y/2 + int(math.ceil(len(text)/2)) + 1, 
    center_x/2 - int(math.ceil(len(ready)/2)),
    ready 
  )
  enter = "[ENTER]"
  stdscr.addstr(
    center_y/2 + int(math.ceil(len(text)/2)) + 1, 
    center_x/2 + int(math.ceil(len(ready)/2)),
    enter,
    curses.A_BLINK | curses.A_REVERSE
  )

  while True:
    for deg in range(0, 360, 10):
        add_circle_point(
          stdscr, 
          str(deg), 
          deg,
          min(center_y, center_x)/2,
          curses.A_REVERSE if deg == selected else curses.A_NORMAL
        )

    ch = stdscr.getch()
    
    if ch == curses.KEY_ENTER or ch == ord('\r') or ch == ord('\n'):
      enter_clear = "       "
      stdscr.addstr(
        center_y/2 + int(math.ceil(len(text)/2)) + 1, 
        center_x/2 + int(math.ceil(len(ready)/2)),
        enter_clear,
        curses.A_NORMAL
      )
      break

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

  for trial in range(0, 10):
    for index in range(5, -1, -1):
      countdown = "Ping in {}".format(index)
      stdscr.addstr(
        center_y/2 + int(math.ceil(len(text)/2)) + 1, 
        center_x/2 - int(math.ceil(len(countdown)/2)),
        countdown
      )
      stdscr.refresh()
      sleep(1)

    stdscr.refresh()

    trial_3_source.append(directions[trial])

    stereo = convolve_stereo(data[:, 0], hrtf, 0, directions[trial])
    sd.play(stereo, fs)
    sd.wait()

    while True:
      for deg in range(0, 360, 10):
        add_circle_point(
          stdscr, 
          str(deg), 
          deg,
          min(center_y, center_x)/2,
          curses.A_REVERSE if deg == selected else curses.A_NORMAL
        )

      ch = stdscr.getch()
      
      if ch == curses.KEY_ENTER or ch == ord('\r') or ch == ord('\n'):
        break

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

    trial_3_resp.append(selected)

  #############################################################################
  #
  # Results
  #
  #############################################################################
  
  stdscr.clear()

  set_1_avg = float()
  set_2_avg = float()
  set_3_avg = float()

  for index in range(0, 10):
    set_1_avg += (math.cos(math.pi / 180 * abs(trial_1_resp[index] - trial_1_source[index])) + 1)/2
    set_2_avg += (math.cos(math.pi / 180 * abs(trial_2_resp[index] - trial_2_source[index])) + 1)/2
    set_3_avg += (math.cos(math.pi / 180 * abs(trial_3_resp[index] - trial_3_source[index])) + 1)/2

  set_1_avg *= 10
  set_2_avg *= 10
  set_3_avg *= 10

  text = list()
  text.append("Game Over!")
  text.append("Set 1 results: {0:.2f}% Accuracy".format(set_1_avg))
  text.append("Set 2 results: {0:.2f}% Accuracy".format(set_2_avg))
  text.append("Set 3 results: {0:.2f}% Accuracy".format(set_3_avg))

  for index, line in enumerate(text):
    stdscr.addstr(
      center_y/2 - int(math.ceil(len(text)/2)) + index,
      center_x/2 - int(math.ceil(len(line)/2)),
      line
    )

  ready = "Finished? "
  stdscr.addstr(
    center_y/2 + int(math.ceil(len(text)/2)) + 1, 
    center_x/2 - int(math.ceil(len(ready)/2)),
    ready 
  )
  enter = "[ENTER]"
  stdscr.addstr(
    center_y/2 + int(math.ceil(len(text)/2)) + 1, 
    center_x/2 + int(math.ceil(len(ready)/2)),
    enter,
    curses.A_BLINK | curses.A_REVERSE
  )

  while True:
    for deg in range(0, 360, 10):
        add_circle_point(
          stdscr, 
          str(deg), 
          deg,
          min(center_y, center_x)/2,
          curses.A_REVERSE if deg == selected else curses.A_NORMAL
        )

    ch = stdscr.getch()
    
    if ch == curses.KEY_ENTER or ch == ord('\r') or ch == ord('\n'):
      enter_clear = "       "
      stdscr.addstr(
        center_y/2 + int(math.ceil(len(text)/2)) + 1, 
        center_x/2 + int(math.ceil(len(ready)/2)),
        enter_clear,
        curses.A_NORMAL
      )
      break

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

  f = open("res.csv", "w")
  for index in range(0, 10):
    f.write("{},{},{},{},{},{}\n".format(trial_1_resp[index], trial_1_source[index], trial_2_resp[index], trial_2_source[index], trial_3_resp[index], trial_3_source[index]))
  f.close()
  curses.endwin()

curses.wrapper(main)

# if __name__ == '__main__':
#   main()
