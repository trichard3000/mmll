#!/usr/bin/python

'''
pylibme7
- a very basic python object for interacting with Bosch ME7 ECU's
- requires pylibftdi


Copyright 2013 Ted Richardson.
Distributed under the terms of the GNU General Public License (GPL)
See LICENSE.txt for licensing information.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
--
trichard3000
'''

from __future__ import print_function, division
import sys, time, argparse
from pylibftdi import Device, BitBangDevice  # This may need to be installed separately

debug = 0   

class Ecu:

   def __init__(self):
      self.ser = Device(mode='b', lazy_open=True)


   def bbang(self, bba):
      # Take the one-byte address to "bit bang" and bang the port
      self.bba = bba
      self.bbser = BitBangDevice()
      self.bbser.open()
      self.bbser.direction = 0x01
      self.bbser.port = 1
      time.sleep(.5)
      self.bbser.port = 0
      outstr = "><"
      sys.stdout.write('\r' + outstr)
      sys.stdout.flush()
      time.sleep(.2)
      bbbitmask = 1
      for i in range(8):
         if (self.bba[0] & bbbitmask) > 0:
            outbit = 1
         else:
            outbit = 0   
         self.bbser.port = outbit
         outstr = ">" + str(outbit) + outstr[1:] 
         sys.stdout.write('\r' + outstr)
         sys.stdout.flush()
         bbbitmask = bbbitmask * 2
         time.sleep(.2)
      self.bbser.port = 1
      sys.stdout.write("\n")
      self.bbser.close()

   def initialize(self, connect):
      self.connect = connect
      if self.connect == "SLOW-0x11":
         self.ser.close()
         time.sleep(.5)

         self.ecuconnect = False
         while self.ecuconnect == False:
            print("Attempting ECU connect: " + self.connect )

            # Bit bang the K-line
            bbseq = [ 0x11 ]
            self.bbang(bbseq)
            self.ser.open()
            self.ser.ftdi_fn.ftdi_set_line_property(8, 1, 0)
            self.ser.baudrate = 10400
            self.ser.flush()

            # Wait for ECU response to bit bang
            waithex = [ 0x55, 0xef, 0x8f, 1 ]
            self.waitfor(waithex)
            # Wait a bit
            time.sleep(.026)

            # Send 0x70
            self.send([ 0x70 ])
   
            # 0xee means that we're talking to the ECU
            waithex = [ 0xee, 1 ]
            response = self.waitfor(waithex)
            if response[0] == True:
                self.ecuconnect = True
            else:
                print("ECU Connect Failed.  Retrying.")

   def waitfor(self, wf):
      # This was used for debugging and really is only used for the init at this point.
      # wf should be a list with the timeout in the last element
      self.wf = wf
      isfound = False
      idx = 0
      foundlist = []
      capturebytes = []
      to = self.wf[-1]
      timecheck = time.time()
      while (time.time() <= (timecheck+to)) & (isfound == False): 
         try:
            recvbyte = self.recvraw(1)
            if recvbyte != "":
               recvdata = ord(recvbyte)
               capturebytes = capturebytes + [ recvdata ]
               if recvdata == self.wf[idx]: 
                  foundlist = foundlist + [ recvdata ]
                  idx = idx + 1
               else: 
                  foundlist = []
                  idx = 0
               if idx == len(self.wf)-1:
                  isfound = True
         except:
            print('error')
            break
      return [ isfound, foundlist, capturebytes ]

   def send(self, sendlist):
      self.sendlist = sendlist
      # Puts every byte in the sendlist out the serial port
      for i in self.sendlist:
         self.ser.write(chr(i))

   def recvraw(self, bytes):
      self.bytes = bytes
      recvdata = self.ser.read(self.bytes)
      return recvdata

   def recv(self, bytes):
      self.bytes = bytes
      isread = False
      while isread == False:
         recvbyte = self.ser.read(self.bytes)
         if recvbyte != "":
            recvdata = recvbyte
            isread = True
      return recvdata      

   def sendcommand(self, sendlist):
      # Wraps raw KWP command in a length byte and a checksum byte and hands it to send()
      self.sendlist = sendlist
      csum = 0
      self.sendlist = [len(self.sendlist)] + self.sendlist 
      csum = self.checksum(self.sendlist)
      self.sendlist = self.sendlist + [csum] 
      self.send(self.sendlist)
      cmdval = self.commandvalidate(self.sendlist)
      return cmdval

   def commandvalidate(self, command):
      # Every KWP command is echoed back.  This clears out these bytes.
      self.command = command
      cv = True
      for i in range(len(self.command)):
         recvdata = self.recv(1)
         if ord(recvdata) != self.command[i]:
            cv = cv & False
      return cv   

   def checksum(self, checklist):
      # Calculates the simple checksum for the KWP command bytes.
      self.checklist = checklist
      csum = 0
      for i in self.checklist:
         csum = csum + i
      csum = (csum & 0xFF) % 0xFF
      return csum

   def getresponse(self):
      # gets a properly formated KWP response from a command and returns the data. 
      debugneeds = 4
      numbytes = 0
      while numbytes == 0:     # This is a hack because sometimes responses have leading 0x00's.  Why?  This removes them.
         numbytes = ord(self.recv(1))
      gr = [ numbytes ]
      if debug >= debugneeds: print("Get bytes: " + hex(numbytes))
      for i in range(numbytes):
         recvdata = ord(self.recv(1))
         if debug >= debugneeds: print("Get byte" + str(i) + ": " + hex(recvdata))
         gr = gr + [ recvdata ]
      checkbyte = self.recv(1)
      if debug >= debugneeds: print(gr)
      if debug >= debugneeds: print("GR: " + hex(ord(checkbyte)) + "<-->" + hex(self.checksum(gr))) 
      return (gr + [ ord(checkbyte) ])

   def readecuid(self, paramdef):      
      # KWP2000 command to pull the ECU ID
      self.paramdef = paramdef
      debugneeds = 4
      reqserviceid = [ 0x1A ]
      sendlist = reqserviceid + self.paramdef
      if debug >= debugneeds: print( sendlist )
      self.sendcommand(sendlist)
      response = self.getresponse()
      if debug >= debugneeds: print(response)
      return response

   def stopcomm(self):
      # KWP2000 command to tell the ECU that the communications is finished
      stopcommunication = [ 0x82 ]
      self.sendcommand(stopcommunication)
      response = self.getresponse()
      return response

   def startdiagsession(self, bps):
      # KWP2000 setup that sets the baud for the logging session
      self.bps = bps
      startdiagnosticsession = [ 0x10 ]
      setbaud = [ 0x86 ]  #Is this the actual function of 0x86?
   #   if self.bps == 10400:
   #      bpsout = [ 0x?? ]
   #   if self.bps == 14400:
   #      bpsout = [ 0x?? ]
      if self.bps == 19200:
         bpsout = [ 0x30 ]
      if self.bps == 38400:
         bpsout = [ 0x50 ]
      if self.bps == 56000:
         bpsout = [ 0x63 ]
      if self.bps == 57600:
         bpsout = [ 0x64 ]
   #   if self.bps == 125000:
   #      bpsout = [ 0x?? ]
      sendlist = startdiagnosticsession + setbaud + bpsout
      self.sendcommand(sendlist)
      response = self.getresponse()
      self.ser.baudrate = self.bps
      time.sleep(1)
      return response

   def accesstimingparameter(self, params):
      # KWP2000 command to access timing parameters
      self.params = params
      accesstiming_setval = [ 0x083, 0x03 ]
      accesstiming = accesstiming_setval + self.params
      sendlist = accesstiming
      self.sendcommand(sendlist)
      response = self.getresponse()
      return response
   
   def readmembyaddr(self, readvals):
      # Function to read an area of ECU memory.
      debugneeds = 4
      self.readvals = readvals
      rdmembyaddr = [ 0x23 ]
      sendlist = rdmembyaddr + self.readvals
      if debug >= debugneeds: print("readmembyaddr() sendlist: " + sendlist)
      self.sendcommand(sendlist)
      response = self.getresponse()
      if debug >= debugneeds: print("readmembyaddr() response: " + response)
      return response

   def writemembyaddr(self, writevals):
      # Function to write to an area of ECU memory.
      debugneeds = 4
      self.writevals = writevals
      wrmembyaddr = [ 0x3D ]
      sendlist = wrmembyaddr + self.writevals
      if debug >= debugneeds: print("writemembyaddr() sendlist: " + sendlist)
      self.sendcommand(sendlist)
      response = self.getresponse()
      if debug >= debugneeds: print("writemembyaddr() response: " + response)
      return response

   def testerpresent(self):
      # KWP2000 TesterPresent command
      tp = [ 0x3E ]
      self.sendcommand(tp)
      response = self.getresponse()
      return response

   def setuplogrecord(self, logline):
      # KWP2000 command to access timing parameters
      self.logline = logline
      response = []
      sendlist = [ 0xb7 ]                           # is 0xB7 the "locator?"
      sendlist = sendlist + [ 0x03 ]           # Number of bytes per field ?
      sendlist = sendlist + self.logline                
      self.sendcommand(sendlist)
      response = self.getresponse()
      return response

   def getlogrecord(self):
      # Command to request a logging record
      gr = [ 0xb7 ]
      self.sendcommand(gr)
      response = self.getresponse()
      return response

   def sendhexstring(self, dumpstring):
      # Takes a list of characters as a string, turns every two characters into a hex byte and sends it raw.
      # used as needed for dev/test/debug
      self.dumpstring = dumpstring
      for i in range(len(self.dumpstring)/2):
         self.send([ int('0x'+self.dumpstring[i*2:(i*2)+2],16) ])



def main():
   print("Loading pylibme7")

   
if __name__ == '__main__':

   try:
     main()

   except KeyboardInterrupt:
     print("hard stop")

