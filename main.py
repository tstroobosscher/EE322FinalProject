###############################################################################
#
#  USC EE322 Final Project - Spring 2019
#
###############################################################################

from scipy.io import wavfile
from scipy.signal import fftconvolve
from time import sleep
from struct import unpack
import os
import wave
import math
import numpy as np
import sounddevice as sd
import soundfile as sf

import asyncio
import queue

global_azimuth = 0
global_elevation = 0

def get_transfer_path(side, elevation, azimuth):
  return "full/elev{:01d}/{:s}{:01d}e{:03d}a.dat".format(
    elevation, 
    side,
    elevation, 
    azimuth
  )

def get_transfer_data(path):
  dat = list()
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

def read_dat(elevation, azimuth):
  """
  @brief      { Reads am hrtf file for a given direction if one exists }

  @param      elevation  -40 to +90 by increments of 10
  @param      azimuth    0 to 355 by increments of 5

  @return     { returns an 2-array of the transfer data or None if one is not available }
  """

  left_impulse = get_transfer_data(
    get_transfer_path('L', elevation, azimuth)
  )
  right_impulse = get_transfer_data(
    get_transfer_path('R', elevation, azimuth)
  )
  
  if left_impulse is None or right_impulse is None:
  	return None

  return np.transpose(np.array([left_impulse, right_impulse]))

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
      {
        -40 : {
          0 : 2-array,
          .
          .
          .
        },
      .
      .
      .
      },
    }
  }
  """
  hrtf = dict()
  for elevation in range(-40, 90, 10):
    #  all of the elevations are there, just the azimuths get cut off
    hrtf[elevation] = dict()
    for azimuth in range(0, 355, 5):
      response = read_dat(elevation, azimuth)
      if response is not None:
        hrtf[elevation][azimuth] = response

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

def convolve_stereo(data, hrtf, elevation, azimuth, mode = 'valid'):
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
  	hrtf.keys(), 
  	elevation
  )
  actual_azimuth = get_closest_key(
  	hrtf[actual_elevation].keys(), 
  	azimuth
  )

  return fftconvolve(
  	data, 
  	hrtf[actual_elevation][actual_azimuth],
  	mode = mode
  )

async def stream_generator(blocksize, *, channels=2, dtype='float32',
                           pre_fill_blocks=10, **kwargs):
    """Generator that yields blocks of input/output data as NumPy arrys.

    The output blocks are uninitialized and have to be filled with
    appropriate audio signals.
    
    """
    assert blocksize != 0
    q_in = asyncio.Queue()
    q_out = queue.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, outdata, frame_count, time_info, status):
        loop.call_soon_threadsafe(q_in.put_nowait, (indata.copy(), status))
        outdata[:] = q_out.get_nowait()

    # pre-fill output queue
    for _ in range(pre_fill_blocks):
        q_out.put(np.zeros((blocksize, channels), dtype=dtype))

    stream = sd.Stream(blocksize=blocksize, callback=callback, dtype=dtype,
                       channels=channels, **kwargs)
    with stream:
        while True:
            indata, status = await q_in.get()
            outdata = np.empty((blocksize, channels), dtype=dtype)
            yield indata, outdata, status
            q_out.put_nowait(outdata)

async def wire_coro(hrtf, **kwargs):
  """Create a connection between audio inputs and outputs.

  Asynchronously iterates over a stream generator and for each block
  simply copies the input data into the output block.

  """

  async for indata, outdata, status in stream_generator(**kwargs):
    if status:
      print(status)
    convolution = convolve_stereo(indata, hrtf, global_elevation, global_azimuth, 'same')
    outdata[:] = convolution


async def main(**kwargs):
  index = 0
  hrtf = load_hrtf()
  # audio_task = asyncio.create_task(wire_coro(hrtf, **kwargs))
  # while True:
  # 	global_azimuth = math.floor(360* math.sin(index / (2 * math.pi)))
  # 	index += 1
  # 	await asyncio.sleep(1)
  # audio_task.cancel()
  # try:
  #   await audio_task
  # except asyncio.CancelledError:
  #   print('wire was cancelled')

if __name__ == "__main__":
  asyncio.run(main(blocksize = 1024, channels = 2))
