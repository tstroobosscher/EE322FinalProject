###############################################################################
#
#  USC EE322 Final Project - Spring 2019
#
###############################################################################

from struct import unpack
from scipy.io import wavfile
from scipy.signal import fftconvolve
from time import sleep
import os
import wave
import numpy as np
import sounddevice as sd
import soundfile as sf

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

  left = fftconvolve(
  	data, 
  	hrtf['L'][actual_elevation][actual_azimuth]
  )
  right = fftconvolve(
  	data, 
  	hrtf['R'][actual_elevation][actual_azimuth]
  )
  stereo = np.transpose([left, right])
  return stereo

def main():
  print "Hello World!"
  hrtf = load_hrtf()
  data, fs = sf.read("dryspeech.wav")
  stereo = convolve_stereo(data, hrtf, 90, 48)
  sd.play(stereo, fs)
  sd.wait()

if __name__ == "__main__":
  main()
