# Author: Jake Longo
# controller script for lecroy oscilloscope

# After a week of trial-and-error, I found that the VICP automatic command runs much slower and causes
# a lot of problems in synchronization. Looks like the vbs approach is much better supported for Lecroy.
# If you wish to change anything in this file, consider that                --- Si 2017.12.5

import time
import visa
import struct
import logging

import numpy             as np
import matplotlib.pyplot as plt

# scope functionality
class Scope(object):

  def __init__(self):
    self.open()
    self.valid_trigger_states = ['AUTO', 'NORM', 'SINGLE', 'STOP']

  def __del__(self):
    self.close()

  def open(self):
   #  get all resources connected to PC
    self.rm    = visa.ResourceManager()
   #  open vcip protocol
    try:
      self.scope = self.rm.open_resource('TCPIP::127.0.0.1::INSTR')
      self.reset()
      self.scope.timeout=5000
      self.scope.clear()
      r=self.scope.query(r"""vbs? 'return=app.WaitUntilIdle(5)' """)
    except:
      self.scope = None
      logging.info("Unable to locate the scope VISA interface")

  def close(self):
    # disconnect the oscilloscope
    # there is a bug in the pyvisa impl. so we'll wrap in
    # a try/catch
    try:
      if (self.scope is not None):
        self.scope.close()

      if (self.rm is not None):
        self.rm.close()

    except:
      logging.info("pyvisa error in closing resource")
  # Set up for a certain trace acquisition process --- Si 2017.12.5 Added
  # vdiv:         vertical resolution (V/div)
  # timebase:     horizontal resolution (S/div)
  # samplerate:   Fixed sample rate (Sa/s)
  # duration:     Measure Duration (usually set as 10*timebase, might not work otherwise)
  # voffset:      Vertical offset
  def setup(self,vdiv,timebase,samplerate,duration,voffset):
    # setup for the trace acquisition
    # set time base

    if(self.scope):
      self.scope.write(r"""vbs 'app.Acquisition.ClearSweeps' """)# clear
    if (self.scope):
      self.scope.write("TDIV " + timebase)
    if (self.scope):
      self.scope.write("C1:VDIV " + vdiv)
    # set waveform format
    if (self.scope):
      self.scope.write("CFMT DEF9,WORD,BIN")
    # set Sampling Rate
    if (self.scope):
      self.scope.write(r"""vbs 'app.Acquisition.Horizontal.Maximize = "FixedSampleRate" '""")
      self.scope.write(r"""vbs 'app.Acquisition.Horizontal.SampleRate = "%s" '""" %samplerate)
      self.scope.write(r"""vbs 'app.Acquisition.Horizontal.AcquisitionDuration = "%s" '"""%duration)
      self.scope.write(r"""vbs 'app.Acquisition.C1.VerOffset = "%s" '""" % voffset)
  # Set up trigger condition
  # delay: negative means start acuisition at post trigger xx s; positive shows the percent of trace before trigger
  # level: the level of trigger which counts as one valid trace
  def set_trigger(self,delay,level):
    # set trigger mod to single
    if (None == self.scope):
      self.open()
    # set trigger delay
    if (self.scope):
      self.scope.write("TRDL " + delay)
    # set trigger level
    if (self.scope):
      self.scope.write("C2:TRLV " + level)
    # set triggr positive edge
    if (self.scope):
      self.scope.write("C2:TRSL POS")
  # Stop the previous capture and start a new one
  def start_trigger(self):
    # set trigger state
    if (self.scope):
      #self.scope.write("TRMD SINGLE")
      #stop
      self.scope.write(r"""vbs 'app.acquisition.triggermode = "stopped" ' """)
      r = self.scope.query(r"""vbs? 'return=app.WaitUntilIdle(5)' """)
      self.scope.write(r"""vbs 'app.acquisition.triggermode = "single" ' """)
      r = self.scope.query(r"""vbs? 'return=app.WaitUntilIdle(5)' """)
  # get the triggering status
  def get_trigger(self):
    # read trigger state from the oscilloscope
    if (None == self.scope):
      self.open()

    if (self.scope):
      ret = self.scope.query("TRMD?")
      return ret.split()[1]

  # check whether Lecroy has already been triggered
  # This is poor-mans timeout. There
  # doesn't seem to be a good platform independant
  # way to raise a timeout exception so this will
  # have to do
  # wait untill the trigger is activated and the capture stops
  def wait_for_trigger(self):
    if (None == self.scope):
      self.open()

    if (self.scope):
      for tries in range(10):
        if (self.get_trigger() == 'STOP'):
          return True
        else:
          time.sleep(0.5)

    print("Trigger timout")
    return False
  # Read one trace back
  # samples: number of samples on that trace
  # isshort: short or float
  def get_channel(self,samples,isshort,channel='C1'):
    # read channel data
    if (None == self.scope):
      self.open()
    if (self.scope):
        if(isshort):
            cmd = self.scope.write('{0}:WF? DATA1'.format(channel))
            trc = self.scope.read_raw()
            hsh = trc.find(b'#', 0)
            skp = int(trc[hsh + 1:hsh + 2])
            trc = trc[hsh +skp+2:-1]
            ret = np.fromstring(trc, dtype='<h', count=samples)
            return ret
        else:
            cmd = self.scope.write('{0}:INSPECT? "SIMPLE"'.format(channel))
            trc = self.scope.read_raw()
            hsh = trc.find(b'\n', 0)
            trc = trc[hsh+2:-1]
            ret = np.fromstring(trc, dtype='float', sep=' ', count=samples)
        return ret
    else:
      return None

  def reset(self):# reset the ocssiloscope
    if (self.scope is not None):

      logging.info("resetting oscilloscope!")
     # self.scope.write("*RCL 6")

      time.sleep(1)
      not_ready = True

      while(not_ready):
        ret = self.scope.query("INR?")
        ret = ret.split()[1]
        not_ready = (0x01 == ((int(ret) >> 13) & 0x01))
        time.sleep(0.5)

    return

if __name__ == "__main__":
  logging.basicConfig(format='%(levelname)s:%(module)s:%(funcName)s:%(message)s', level=logging.INFO)
  scope = Scope()
  scope.reset();
  #scope.set_trigger('SINGLE')
  scope.wait_for_trigger()
