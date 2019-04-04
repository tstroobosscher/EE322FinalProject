###############################################################################
#
#  USC EE322 Final Project - Spring 2019
#
###############################################################################

#  reading and writing .wav files
import wave

import array

from struct import unpack

import os

#
#
#  data structure for HRTF data:
#    elevation ranges from -40 to +90 in increments of 10
#    azimuth ranges from 0 to 355 in increments of 5
#    left and right
# 
#  3D array of key value pairs:
#  
#  HRTF = {
#    L: {
#      -40 : {
#        0 : list(data),
#        .
#        .
#        .
#      },
#      .
#      .
#      .
#    },
#    R: {
#      .
#      .
#      .
#    }
#  }
#  
#

def read_dat(side, elevation, azimuth):
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

  return dat

def load_hrtf():
  hrtf = dict()
  hrtf['L'] = dict()
  hrtf['R'] = dict()
  for side in hrtf.keys():
    for elevation in range(-40, 90, 10):
      hrtf[side][elevation] = dict()
      for azimuth in range(0, 355, 5):
        hrtf[side][elevation][azimuth] = read_dat(side, elevation, azimuth)

  return hrtf

def main():
  print "Hello World!"
  print(load_hrtf())
  exit()

if __name__ == "__main__":
  main()
