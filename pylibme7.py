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
      self.outstr = "><"
      sys.stdout.write('\r' + self.outstr)
      sys.stdout.flush()
      time.sleep(.2)
      self.bbbitmask = 1
      for i in range(8):
         if (self.bba[0] & self.bbbitmask) > 0:
            self.outbit = 1
         else:
            self.outbit = 0   
         self.bbser.port = self.outbit
         self.outstr = ">" + str(self.outbit) + self.outstr[1:] 
         sys.stdout.write('\r' + self.outstr)
         sys.stdout.flush()
         self.bbbitmask = self.bbbitmask * 2
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
            self.bbseq = [ 0x11 ]
            self.bbang(self.bbseq)
            self.ser.open()
            self.ser.ftdi_fn.ftdi_set_line_property(8, 1, 0)
            self.ser.baudrate = 10400
            self.ser.flush()

            # Wait for ECU response to bit bang
            self.waithex = [ 0x55, 0xef, 0x8f, 1 ]
            self.waitfor(self.waithex)
            # Wait a bit
            time.sleep(.026)

            # Send 0x70
            self.send([ 0x70 ])
   
            # 0xee means that we're talking to the ECU
            self.waithex = [ 0xee, 1 ]
            self.response = self.waitfor(self.waithex)
            if self.response[0] == True:
                self.ecuconnect = True
            else:
                print("ECU Connect Failed.  Retrying.")

   def waitfor(self, wf):
      # This was used for debugging and really is only used for the init at this point.
      # wf should be a list with the timeout in the last element
      self.wf = wf
      self.isfound = False
      self.idx = 0
      self.foundlist = []
      self.capturebytes = []
      self.to = self.wf[-1]
      self.timecheck = time.time()
      while (time.time() <= (self.timecheck+self.to)) & (self.isfound == False): 
         try:
            self.recvbyte = self.recvraw(1)
            if self.recvbyte != "":
               self.recvdata = ord(self.recvbyte)
               self.capturebytes = self.capturebytes + [ self.recvdata ]
               if self.recvdata == self.wf[self.idx]: 
                  self.foundlist = self.foundlist + [ self.recvdata ]
                  self.idx = self.idx + 1
               else: 
                  self.foundlist = []
                  self.idx = 0
               if self.idx == len(self.wf)-1:
                  self.isfound = True
         except:
            print('error')
            break
      return [ self.isfound, self.foundlist, self.capturebytes ]

   def send(self, sendlist):
      self.sendlist = sendlist
      # Puts every byte in the sendlist out the serial port
      for i in self.sendlist:
         self.ser.write(chr(i))

   def recvraw(self, bytes):
      self.bytes = bytes
      self.recvdata = self.ser.read(self.bytes)
      return self.recvdata

   def recv(self, bytes):
      self.bytes = bytes
      self.isread = False
      while self.isread == False:
         self.recvbyte = self.ser.read(self.bytes)
         if self.recvbyte != "":
            self.recvdata = self.recvbyte
            self.isread = True
      return self.recvdata      

   def sendcommand(self, sendlist):
      # Wraps raw KWP command in a length byte and a checksum byte and hands it to send()
      self.csum = 0
      self.sendlist = sendlist
      self.sendlist = [len(self.sendlist)] + self.sendlist 
      self.csum = self.checksum(self.sendlist)
      self.sendlist = self.sendlist + [self.csum] 
      self.send(self.sendlist)
      self.cmdval = self.commandvalidate(self.sendlist)
      return self.cmdval

   def commandvalidate(self, command):
      # Every KWP command is echoed back.  This clears out these bytes.
      self.command = command
      self.cv = True
      for i in range(len(self.command)):
         self.recvdata = self.recv(1)
         if ord(self.recvdata) != self.command[i]:
            self.cv = self.cv & False
      return self.cv   

   def checksum(self, checklist):
      # Calculates the simple checksum for the KWP command bytes.
      self.checklist = checklist
      self.csum = 0
      for i in self.checklist:
         self.csum = self.csum + i
      self.csum = (self.csum & 0xFF) % 0xFF
      return self.csum

   def getresponse(self):
      # gets a properly formated KWP response from a command and returns the data. 
      self.debugneeds = 4
      self.numbytes = 0
      while self.numbytes == 0:     # This is a hack because sometimes responses have leading 0x00's.  Why?  This removes them.
         self.numbytes = ord(self.recv(1))
      self.gr = [ self.numbytes ]
      if debug >= self.debugneeds: print("Get bytes: " + hex(self.numbytes))
      for i in range(self.numbytes):
         self.recvdata = ord(self.recv(1))
         if debug >= self.debugneeds: print("Get byte" + str(i) + ": " + hex(self.recvdata))
         self.gr = self.gr + [ self.recvdata ]
      self.checkbyte = self.recv(1)
      if debug >= self.debugneeds: print(self.gr)
      if debug >= self.debugneeds: print("GR: " + hex(ord(self.checkbyte)) + "<-->" + hex(self.checksum(self.gr))) 
      return (self.gr + [ ord(self.checkbyte) ])

   def readecuid(self, paramdef):      
      # KWP2000 command to pull the ECU ID
      self.paramdef = paramdef
      self.debugneeds = 4
      self.reqserviceid = [ 0x1A ]
      self.sendlist = self.reqserviceid + self.paramdef
      if debug >= self.debugneeds: print( self.sendlist )
      self.sendcommand(self.sendlist)
      self.response = self.getresponse()
      if debug >= self.debugneeds: print(self.response)
      return self.response

   def stopcomm(self):
      # KWP2000 command to tell the ECU that the communications is finished
      self.stopcommunication = [ 0x82 ]
      self.sendlist = self.stopcommunication
      self.sendcommand(self.sendlist)
      self.response = self.getresponse()
      return self.response

   def startdiagsession(self, bps):
      # KWP2000 setup that sets the baud for the logging session
      self.bps = bps
      self.startdiagnosticsession = [ 0x10 ]
      self.setbaud = [ 0x86 ]  #Is this the actual function of 0x86?
   #   if self.bps == 10400:
   #      self.bpsout = [ 0x?? ]
   #   if self.bps == 14400:
   #      self.bpsout = [ 0x?? ]
      if self.bps == 19200:
         self.bpsout = [ 0x30 ]
      if self.bps == 38400:
         self.bpsout = [ 0x50 ]
      if self.bps == 56000:
         self.bpsout = [ 0x63 ]
      if self.bps == 57600:
         self.bpsout = [ 0x64 ]
   #   if self.bps == 125000:
   #      self.bpsout = [ 0x?? ]
      self.sendlist = self.startdiagnosticsession + self.setbaud + self.bpsout
      self.sendcommand(self.sendlist)
      self.response = self.getresponse()
      self.ser.baudrate = self.bps
      time.sleep(1)
      return self.response

   def accesstimingparameter(self, params):
      # KWP2000 command to access timing parameters
      self.params = params
      self.accesstiming_setval = [ 0x083, 0x03 ]
      self.accesstiming = self.accesstiming_setval + self.params
      self.sendlist = self.accesstiming
      self.sendcommand(self.sendlist)
      self.response = self.getresponse()
      return self.response
   
   def readmembyaddr(self, readvals):
      # Function to read an area of ECU memory.
      self.readvals = readvals
      self.debugneeds = 4
      self.rdmembyaddr = [ 0x23 ]
      self.sendlist = self.rdmembyaddr + self.readvals
      if debug >= self.debugneeds: print("readmembyaddr() sendlist: " + self.sendlist)
      self.sendcommand(self.sendlist)
      self.response = self.getresponse()
      if debug >= self.debugneeds: print("readmembyaddr() response: " + self.response)
      return self.response

   def writemembyaddr(self, writevals):
      # Function to write to an area of ECU memory.
      self.writevals = writevals
      self.debugneeds = 4
      self.wrmembyaddr = [ 0x3D ]
      self.sendlist = self.wrmembyaddr + self.writevals
      if debug >= self.debugneeds: print("writemembyaddr() sendlist: " + self.sendlist)
      self.sendcommand(self.sendlist)
      self.response = self.getresponse()
      if debug >= self.debugneeds: print("writemembyaddr() response: " + self.response)
      return self.response

   def testerpresent(self):
      # KWP2000 TesterPresent command
      self.tp = [ 0x3E ]
      self.sendcommand(self.tp)
      self.response = self.getresponse()
      return self.response

   def setuplogrecord(self, logline):
      # KWP2000 command to access timing parameters
      self.logline = logline
      self.response = []
      self.sendlist = [ 0xb7 ]                           # is 0xB7 the "locator?"
      self.sendlist = self.sendlist + [ 0x03 ]           # Number of bytes per field ?
      self.sendlist = self.sendlist + self.logline                
      self.sendcommand(self.sendlist)
      self.response = self.getresponse()
      return self.response

   def getlogrecord(self):
      # Command to request a logging record
      self.gr = [ 0xb7 ]
      self.sendcommand(self.gr)
      self.response = self.getresponse()
      return self.response

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

