#!/usr/bin/python

'''
mmll.py
- the Most Minimal Linux Logger

Copyright 2013 Ted Richardson.
Distributed under the terms of the GNU General Public License (GPL)
See LICENSE.txt for licensing information.

usage: mmll.py [-h] -c CONFIGFILE [-o OUTPUTFILE] [-d {0,1,2,3,4}]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --configfile CONFIGFILE
                        The logging config file
  -o OUTPUTFILE, --outputfile OUTPUTFILE
                        The desired output log file - No entry outputs log
                        data to STDOUT
  -d {0,1,2,3,4}, --debug {0,1,2,3,4}
                        Increase the Debug Level (experimental)

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
import pylibme7
from me7lconfig import *

debug = 0   # Default debug value.  Can be overridden from the command line.

def printconfig(config):
   # Print out the config info
   print("Note:  Only using Connect, and Logspeed so far.")  
   print("       Connect must only be 'SLOW-0x11' and not all baud rates are supported yet")
   print("       Sample Rate is ignored once max logging speed is achieved.")
   print()
   print("From Config Files:")
   print("ECU File     : " + config[0][0] )
   print("Sample Rate  : " + config[0][1] )
   print("ME7L Cfg Ver : " + config[0][2] ) 
   print("Connect      : " + config[0][3] ) 
   print("Communicate  : " + config[0][4] )
   print("LogSpeed     : " + config[0][5] )
   print("HWNumber     : " + config[0][6] )
   print("SWNumber     : " + config[0][7] )
   print("PartNumber   : " + config[0][8] )
   print("SWVersion    : " + config[0][9] )
   print("EngineID     : " + config[0][10] )

def textlist(tl):
   # Outputs a list of bytes as a string of the corresponding ASCII characters.
   debugneeds = 4
   textresponse = ""
   for i in range(len(tl)-4):
      textresponse = textresponse + chr(tl[i+3])
   if debug >= debugneeds: print( "textlist() response: " + textresponse )
   return textresponse
 
def parselogdata(config, logdata, starttime):
   # Takes the raw logged values and applies the conversions from the ECU config file.
   logline = (str( round((time.time() - starttime),3) ).ljust(4,'0')).rjust(10) + ', '
   counter = logdata.index( 0xF7 ) + 1
   for l in range(1,len(config)):
      size = int(config[l][3])
      bitmask = int(config[l][4],16)
      s = bool(int(config[l][6]))
      i = bool(int(config[l][7]))
      a = float(config[l][8])
      b = float(config[l][9])
      
      bytes = logdata[ counter : counter + size ]
      byteconv = ""
      # Read bytes in reverse order.
      for j in range(len(bytes)):
         byteconv = hex(bytes[j])[2:].rjust(2,'0') + byteconv 
         internal = int('0x'+byteconv, 16)
      
      # bitmask code eeds tested
      if bitmask > 0:
         internal = internal & bitmask

      # signed/unsigned?
      if s == True:
         internal = signed(internal,size)

      # Inverse or regular?
      if i == False:
         endval = round((a * internal - b ),3)
      else:
         endval = round((a / (internal - b)),3)

      # Creates final line of logged data
      logline = logline + str(endval).rjust(10)
      if l < len(config)-1:
         logline = logline + ', '

      counter = counter + size
   return logline

def signed(n,bytecount):
      # Conversion for signed values
      conv = 2**((bytecount * 8) - 1)
      return ( n & (conv - 1 ) ) - ( n & conv ) 

def main(debug):
   # The main routine

   argparser = argparse.ArgumentParser()
   argparser.add_argument("-c", "--configfile", help="The logging config file", required=True)
   argparser.add_argument("-o", "--outputfile", help="The desired output log file - No entry outputs log data to STDOUT")
   argparser.add_argument("-d", "--debug", type=int, choices=[0, 1, 2, 3, 4], default=debug, help="Increase the Debug Level (experimental)")
   args = argparser.parse_args()


   try:
      # Use config data from the command line
      config = parseconfigfile(str(args.configfile))
      if str(args.outputfile) != "None":
         outfile = open(str(args.outputfile), 'w')
      else:
         outfile = sys.stdout
      debug = args.debug

      # Print Config data
      print()
      printconfig(config)

      print("...sined")


      ecu = pylibme7.Ecu()
      ecu.initialize(config[0][3])

      print("....sealed")

      print("Connected at 14400")
      response = ecu.readecuid([ 0x94 ])
      swnumber = textlist(response)
 
      response = ecu.startdiagsession(int(config[0][5]))
      if debug >= 3:  print("startdiagsession(" + config[0][5] +") response: " + hexlist(response) )
      print("Connected at " + config[0][5] )

      p2min = [ 0x00 ]
      p2max = [ 0x01 ]
      p3min = [ 0x00 ]
      p3max = [ 0x14 ]
      p4min = [ 0x00 ]
      accesstiming = p2min + p2max + p3min + p3max + p4min
      response = ecu.accesstimingparameter(accesstiming)
      if debug >= 3:  print("accesstimingparameter() response: " + hexlist(response) )
 
      print("Timing Set, reading and preparing memory")

      # I don't know how this is used.  Is it really ECU Scaling?
      ecuid_0x81 = ecu.readecuid([ 0x81 ])
      if debug >= 3:  print("ecuid_0x81 =" + hexlist(ecuid_0x81) )

      response = ecu.readecuid([ 0x94 ])
      swnumber = textlist(response)
      if debug >= 3:  print("SWNumber =" + swnumber)

      response = ecu.readecuid([ 0x92 ])
      hwnumber = textlist(response)
      if debug >= 3:  print("HWNumber =" + hwnumber)

      response = ecu.readecuid([ 0x9b ])
      partraw = textlist(response)
      if debug >= 3:  print("partraw  =" + partraw)
      partnumber = partraw[:12]
      swversion = partraw[12:16]
      engineid = partraw[26:42]
      modelid = partraw[42:]
      # Now that we know it, tacking ModelId on the end of the ecu config info
      config[0] = config [0] + [ modelid ]

      #I don't know how this is used.
      ecuid_0x9c = ecu.readecuid([ 0x9c ])
      if debug >= 3:  print("exuid_0x9c =" + hexlist(ecuid_0x9c) )

      # Check ECU values versus config file
      cfgcheck = True
      sys.stdout.write("Checking HWNumber   - config:[" + config[0][6].ljust(10) + "]       ecu:[" + hwnumber.ljust(10) + ']       : ')
      if config[0][6] != hwnumber:
         sys.stdout.write("FAIL" + '\n')
         cfgcheck = False
      else:
         sys.stdout.write("pass" + '\n')

      sys.stdout.write("Checking SWNumber   - config:[" + config[0][7].ljust(10) + "]       ecu:[" + swnumber.ljust(10) + ']       : ')
      if config[0][7] != swnumber:
         sys.stdout.write("FAIL" + '\n')
         cfgcheck = False
      else:
         sys.stdout.write("pass" + '\n')

      sys.stdout.write("Checking Partnumber - config:[" + config[0][8].ljust(12) + "]     ecu:[" + partnumber.ljust(12) + ']     : ')
      if config[0][8] != partnumber:
         sys.stdout.write("FAIL" + '\n')
         cfgcheck = False
      else:
         sys.stdout.write("pass" + '\n')

      sys.stdout.write("Checking SWVersion  - config:[" + config[0][9].ljust(4) + "]             ecu:[" + swversion.ljust(4) + ']             : ')
      if config[0][9] != swversion:
         sys.stdout.write("FAIL" + '\n')
         cfgcheck = False
      else:
         sys.stdout.write("pass" + '\n')

      sys.stdout.write("Checking EngineId   - config:[" + config[0][10].ljust(16) + "] ecu:[" + engineid.ljust(16) + '] : ')
      if config[0][10] != engineid:
         sys.stdout.write("FAIL" + '\n')
         cfgcheck = False
      else:
         sys.stdout.write("pass" + '\n')

      sys.stdout.write("Displaying ModelId  -                           ecu:[" + modelid + ']' + '\n')

      if cfgcheck == True:

         # Why are we doing this?
         memaddrhi = [ 0x00 ]
         memaddrmid = [ 0xe1 ]
         memaddrlow = [ 0xb0 ]
         memsize = [ 0x04 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize 
         response = ecu.readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )
   
         memaddrhi = [ 0x00 ]
         memaddrmid = [ 0xe2 ]
         memaddrlow = [ 0x28 ]
         memsize = [ 0x04 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize
         response = ecu.readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )
   
         # Why is this extra 0x00 needed?
         ecu.send( [ 0x00 ] )
         ecu.recv(1)

         # Write to memory
         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7a ]
         memaddrlow = [ 0x00 ]
         memsize = [ 0x80 ]
         memvalues = []
         # Repeats 0xc6, 0x7a 0x38 0x00 32 times
         for i in range(32): 
            memvalues = memvalues + [ 0xc6, 0x7a, 0x38, 0x0 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize + memvalues
         response = ecu.writemembyaddr(request)   # Response = 0x7d + memory address
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         ecu.send( [ 0x00 ] )                          # Why is this extra 0x00 needed?
         ecu.recv(1)

         # Write to memory
         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7a ]
         memaddrlow = [ 0x80 ]    # Write starting after the previous write
         memsize = [ 0x80 ]
         memvalues = []
         # Repeats 0xc6, 0x7a 0x38 0x00 16 more times
         for i in range(16):
            memvalues = memvalues + [ 0xc6, 0x7a, 0x38, 0x0 ]
         # Then load the following hex into memory.  I don't know what this hex does yet. 
         memvalues = memvalues + [ 0x62, 0xa7, 0x81, 0x0, 0x0, 0x0, 0xf2, 0xf4, 0xce, 0xe1, 0xa9, 0x84, 0x47, 0xf8, 0xb7, 0x0, 0x2d, 0x26, 0xd7, 0x10, 0x38, 0x0, 0xf2, 0xf4, 0xc0, 0x7a, 0xf2, 0xf5, 0xc2, 0x7a, 0x2d, 0x1d, 0x88, 0x80, 0x88, 0x70, 0x88, 0x60, 0xe6, 0xf8, 0x5e, 0x0, 0xe6, 0xf7, 0x4, 0x7a, 0x8, 0x44, 0xdc, 0x5, 0x98, 0x64, 0xd7, 0x0, 0x38, 0x0, 0xb8, 0x67, 0x8, 0x72, 0x2, 0xf8, 0x1e, 0xff ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize + memvalues
         response = ecu.writemembyaddr( request )   # Response = 0x7d + memory address
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         ecu.send( [ 0x00 ] )                          # Why is this extra 0x00 needed?
         ecu.recv(1)

         # Write to memory
         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7b ]
         memaddrlow = [ 0x00 ]    # Write starting at 0x38 0x7b 0x00
         memsize = [ 0x80 ]
         # No idea what this does yet:
         memvalues = [ 0x70, 0x88, 0xed, 0xf6, 0xf2, 0xf4, 0x1c, 0xff, 0xd7, 0x10, 0x38, 0x0, 0xf6, 0xf4, 0xc0, 0x7a, 0xf6, 0xf4, 0xc2, 0x7a, 0x98, 0x60, 0x98, 0x70, 0x98, 0x80, 0xfa, 0x0, 0x66, 0x3b, 0x88, 0xb0, 0x88, 0xa0, 0x88, 0x90, 0x88, 0x80, 0x88, 0x70, 0x88, 0x60, 0xe1, 0xf, 0xf2, 0xf4, 0xca, 0xe1, 0x49, 0x81, 0x2d, 0x4, 0xf2, 0xf4, 0xce, 0xe1, 0x8, 0x41, 0x99, 0xf4, 0x49, 0xf0, 0x2d, 0x5, 0x49, 0xf3, 0x2d, 0x31, 0x49, 0xf4, 0x2d, 0x2f, 0xd, 0x6c, 0xf0, 0x9c, 0xe7, 0xf8, 0xf7, 0x0, 0xb9, 0x89, 0x8, 0x91, 0xe6, 0xfa, 0x80, 0x7c, 0xe6, 0xfb, 0x38, 0x0, 0xd7, 0x0, 0x38, 0x0, 0xf3, 0xfc, 0xc4, 0x7a, 0x67, 0xfc, 0x7f, 0x0, 0x2d, 0x11, 0xdc, 0x1b, 0x98, 0x4a, 0x98, 0x5a, 0xf1, 0xeb, 0xe1, 0xb, 0x49, 0xe2, 0x2d, 0x4, 0xdc, 0x5, 0x99, 0xd4, 0xb9, 0xd9, 0x8, 0x91 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize + memvalues
         response = ecu.writemembyaddr( request )   # Response = 0x7d + memory address
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         ecu.send( [ 0x00 ] )                          # Why is this extra 0x00 needed?
         ecu.recv(1)

         # Write to memory
         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7b ]
         memaddrlow = [ 0x80 ]    # Write starting after the previous write
         memsize = [ 0x80 ]
         # No idea what this does yet:
         memvalues = [ 0xdc, 0x5, 0x99, 0xd4, 0xb9, 0xd9, 0x8, 0x91, 0x29, 0xc1, 0x3d, 0xef, 0xf0, 0x49, 0x20, 0x4c, 0xe6, 0xf6, 0x0, 0x8, 0x74, 0xf6, 0x74, 0xe0, 0x98, 0x60, 0x98, 0x70, 0x98, 0x80, 0x98, 0x90, 0x98, 0xa0, 0x98, 0xb0, 0xdb, 0x0, 0xf2, 0xf4, 0xca, 0xe1, 0x29, 0x82, 0xf1, 0xa8, 0xe1, 0xb, 0xe6, 0xfa, 0x80, 0x7c, 0xe6, 0xfb, 0x38, 0x0, 0x49, 0xf3, 0x2d, 0x9, 0x6, 0xfa, 0x0, 0x1, 0xd7, 0x0, 0x38, 0x0, 0xf3, 0xfb, 0xc4, 0x7a, 0x47, 0xfb, 0x40, 0x0, 0x3d, 0xfe, 0xf2, 0xf4, 0xce, 0xe1, 0x8, 0x42, 0x49, 0xa3, 0x8d, 0x19, 0x99, 0xe4, 0x99, 0xd4, 0x99, 0xc4, 0xf1, 0xfe, 0x67, 0xfe, 0xbf, 0x0, 0xdc, 0x2b, 0xb9, 0xca, 0x8, 0xa1, 0xb9, 0xda, 0x8, 0xa1, 0xdc, 0xb, 0xb9, 0xea, 0x8, 0xa1, 0xe1, 0x1e, 0x67, 0xff, 0x40, 0x0, 0x3d, 0x1, 0x9, 0xe1, 0xdc, 0xb ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize + memvalues
         response = ecu.writemembyaddr( request )   # Response = 0x7d + memory address
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         ecu.send( [ 0x00 ] )                          # Why is this extra 0x00 needed?
         ecu.recv(1)

         # Write to memory
         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7c ]
         memaddrlow = [ 0x00 ]    # Write starting after the previous write
         memsize = [ 0x46 ]
         # No idea what this does yet:
         memvalues = [ 0xb9, 0xea, 0x8, 0xa1, 0x9, 0xb1, 0x29, 0xa3, 0xd, 0xe5, 0x67, 0xfb, 0x7f, 0x0, 0xd7, 0x0, 0x38, 0x0, 0xf7, 0xfb, 0xc4, 0x7a, 0xf0, 0x9c, 0xe7, 0xf8, 0xf7, 0x0, 0xb9, 0x89, 0xe0, 0x14, 0xd, 0xb7, 0xe6, 0xf4, 0xff, 0xf7, 0x64, 0xf4, 0x74, 0xe0, 0xf0, 0xe9, 0xe7, 0xf8, 0x7f, 0x0, 0xb9, 0x8e, 0x8, 0xe1, 0xe7, 0xf8, 0xb7, 0x0, 0xb9, 0x8e, 0x8, 0xe1, 0xe7, 0xf8, 0x12, 0x0, 0xb9, 0x8e, 0xe1, 0x38, 0xd, 0xa9 ] 
         request = memaddrhi + memaddrmid + memaddrlow + memsize + memvalues
         response = ecu.writemembyaddr( request )   
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         # Read back what we wrote earlier  
         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7a ]
         memaddrlow = [ 0x00 ]
         memsize = [ 0x80 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize
         response = ecu.readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7a ]
         memaddrlow = [ 0x80 ]
         memsize = [ 0x80 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize
         response = ecu.readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7b ]
         memaddrlow = [ 0x80 ]
         memsize = [ 0x80 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize
         response = ecu.readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7c ]
         memaddrlow = [ 0x00 ]
         memsize = [ 0x46 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize
         response = ecu.readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         # Write to memory
         memaddrhi = [ 0x00 ]
         memaddrmid = [ 0xe2 ]
         memaddrlow = [ 0x28 ]   
         memsize = [ 0x04 ]
         memvalues = [ 0x00, 0x3a, 0xe1, 0x00 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize + memvalues
         response = ecu.writemembyaddr( request )
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         response = ecu.testerpresent()
         if debug >= 3:  print("testerpresent(): response: " + hexlist(response))

         ecu.send( [ 0x00 ] )                          # Why is this extra 0x00 needed?
         ecu.recv(1)   

         # Tell ECU memory locations to log, based on the config and ecu file data:
         logline = loglocations(config)
         response = ecu.setuplogrecord(logline[0])
         if debug >= 3:  print("loglocations(): request: " + hexlist(logline[0]) + " response: " + hexlist(response) )
         # grab logpacketsize from loglocations() return and tack it to the end of ecu config info
         config[0] = config[0] + [ logline[1] ]

         print(".....delivered")
         if str(args.outputfile) != 'None':
            sys.stdout.write("Logging (ctrl-c to end):  ")


         # Finally, start logging records!

         headers = logheader(config)
         for line in headers:
            outfile.write(line + '\n')

         secondstolog = 10
         starttime = time.time()

         spinner = 0
         spinstr = [ '|', '/', '-', '\\' ]

         while True:
            timerstart = time.time()
            response = ecu.getlogrecord()
            if debug >= 3:  print("getrecord(): request: [ 0xb7 ] response: " + hexlist(response))

            # Pipe log output to parser, based on info pulled from the config and ecu files
            response = parselogdata(config, response, starttime)
            outfile.write( response + '\n') 


            # Just for fun
            if str(args.outputfile) != 'None':
               spinout = spinstr[spinner]
               sys.stdout.write('\b' + spinout)
               sys.stdout.flush()
               spinner = spinner + 1
               if spinner == 4: spinner = 0

            # Sleep to adjust log records per second
            samplerate = 1/int(config[0][1])
            timerfinish = time.time()
            adjust = (timerfinish-timerstart)
            if adjust < samplerate:
               time.sleep((samplerate)-(timerfinish-timerstart))

      else:
         print("Config check failed")

   # Catch ctrl-c
   except KeyboardInterrupt:
      sys.stdout.write('\r' + "Stopping".ljust(30) + '\n')

   sys.stdout.write('\r')
   sys.stdout.flush()
   
   # Wrap things up.
   outfile.flush()
   print("Logging Finished")


   
if __name__ == '__main__':

   try:
     main(debug)

   except KeyboardInterrupt:
     print("hard stop")

