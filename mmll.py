#!/usr/bin/python

'''
the Most Minimal Linux Logger
Copyright 2013 Ted Richardson.
Distributed under the terms of the GNU General Public License (GPL)
See LICENSE for licensing information.


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
import sys, time, threading, Queue, argparse, re
from pylibftdi import Device, BitBangDevice  # This may need to be installed separately

debug = 0   # Default debug value.  Can be overridden from the command line.

# Set up serial port globally
ser = Device(mode='b', lazy_open=True)

def parseconfigfile(pf):
   listout = []
   # cfglistout: ECUfile, Samples, Version, Connect, Communicate, LogSpeed,
   #       ...   HWNumber, SWNumber, PartNumber, SWVersion, EngineId
   cfglistout = [ '', '', '', '', '', '', '', '', '', '', '' ]
   cfgfile = open(pf)
   for line in cfgfile:
      lineout = []
      firstfield = ""
      secondfield = ""
      cfgout = line.replace('\t'," ").strip()

      if cfgout != '':  # if the line isn't empty
         if cfgout.strip()[0] != '[':  # if the field doesn't start w '['
            firstfieldlen = cfgout.find(';')  # find if there's a ";"
            if firstfieldlen != 0:  # if the ";" isn't first
               if firstfieldlen != -1:   # if there is a ";" somewhere
                  parseline = cfgout[:firstfieldlen].strip()  # pull up to ";"
               else:
                  parseline = cfgout.strip()  # is there isn't a ";" pull whole line

               secondfieldstart = parseline.find(' ')
               if secondfieldstart != -1:
                  firstfield = parseline[:secondfieldstart]
                  secondfield = parseline[secondfieldstart:].strip()
                  if secondfield[0] == "=":
                     secondfield = secondfield[1:].strip()
                  secondfieldlen = secondfield.find(' ')
                  if secondfieldlen > 0:
                     secondfield = secondfield[:secondfieldlen].strip()
               else:
                  firstfield = parseline
                  secondfield = ""
               lineout = [ firstfield ] + [ secondfield ]
               if lineout[0] == 'ECUCharacteristics':
                  cfglistout[0] = lineout[1]
               elif lineout[0] == 'SamplesPerSecond':
                  cfglistout[1] = lineout[1]
               else:
                  listrecord = geteculine(cfglistout[0], lineout[0])

                  # Cleanup curly brackets around aliases
                  if listrecord[1][0] == '{':
                     listrecord[1] = listrecord[1][1:]
                  if listrecord[1][-1] == '}':
                     listrecord[1] = listrecord[1][:len(listrecord)]

                  if len(lineout) >= 2:
                     if lineout[1] != "":
                        listrecord[1] = lineout[1]
                  listout = listout + [ listrecord ]

   ecufile = open(cfglistout[0])
   for line in ecufile:
      lineout = []
      firstfield = ""
      secondfield = ""
      cfgout = line.replace('\t'," ").strip()

      if cfgout != '':  # if the line isn't empty
         if cfgout.strip()[0] != '[':  # if the field doesn't start w '['
            firstfieldlen = cfgout.find(';')  # find if there's a ";"
            if firstfieldlen != 0:  # if the ";" isn't first
               if firstfieldlen != -1:   # if there is a ";" somewhere
                  parseline = cfgout[:firstfieldlen].strip()  # pull up to ";"
               else:
                  parseline = cfgout.strip()  # is there isn't a ";" pull whole$

               secondfieldstart = parseline.find(' ')
               if secondfieldstart != -1:
                  firstfield = parseline[:secondfieldstart]
                  secondfield = parseline[secondfieldstart:].strip()
                  if secondfield[0] == "=":
                    secondfield = secondfield[1:].strip()
                  secondfieldlen = secondfield.find(';')
                  if secondfieldlen > 0:
                     secondfield = secondfield[:secondfieldlen].strip()
               else:
                  firstfield = parseline
                  secondfield = ""
               lineout = [ firstfield ] + [ secondfield ]

               if lineout[0] == 'Version':
                  cfglistout[2] = lineout[1]
               elif lineout[0] == 'Connect':
                  cfglistout[3] = lineout[1]
               elif lineout[0] == 'Communicate':
                  cfglistout[4] = lineout[1]
               elif lineout[0] == 'LogSpeed':
                  cfglistout[5] = lineout[1]
               elif lineout[0] == 'HWNumber':
                  cfglistout[6] = lineout[1][1:-1]
               elif lineout[0] == 'SWNumber':
                  cfglistout[7] = lineout[1][1:-1]
               elif lineout[0] == 'PartNumber':
                  cfglistout[8] = lineout[1][1:-1]
               elif lineout[0] == 'SWVersion':
                  cfglistout[9] = lineout[1][1:-1]
               elif lineout[0] == 'EngineId':
                  cfglistout[10] = lineout[1][1:-1]

   listout = [ cfglistout ] + listout
   cfgfile.close()
   return listout

def geteculine(gf, value):
   varinfo = []
   match = False
   ecufile = open(gf)
   for line in ecufile:
      if line[:len(value)] == value:
         varinfo = re.split(',',line)
         #insert alias from CFG file
         for i in range(len(varinfo)):
            varinfo[i] = varinfo[i].strip()
         break
   ecufile.close()
   return varinfo

def printconfig(config):
   # Print out the config info
   print("Note:  Only using Connect, and Logspeed so far.")  
   print("       Connect must only be 'SLOW-0x11' and not all baud rates are supported yet")
   print("       Sample Rate is ignored as program is too slow anyway.")
   print()
   print("From Config Files:")
   print("ECU File    : " + config[0][0] )
   print("Sample Rate : " + config[0][1] )
   print("Version     : " + config[0][2] ) 
   print("Connect     : " + config[0][3] ) 
   print("Communicate : " + config[0][4] )
   print("LogSpeed    : " + config[0][5] )
   print("HWNumber    : " + config[0][6] )
   print("SWNumber    : " + config[0][7] )
   print("PartNumber  : " + config[0][8] )
   print("SWVersion   : " + config[0][9] )
   print("EngineID    : " + config[0][10] )

def bbang(bba):
   # Take the one-byte address to "bit bang" and bang the port
   bbser = BitBangDevice()
   bbser.open()
   bbser.direction = 0x01
   bbser.port = 1
   time.sleep(.5)
   bbser.port = 0
   outstr = "><"
   sys.stdout.write('\r' + outstr)
   sys.stdout.flush()
   time.sleep(.2)
   bbbitmask = 1
   for i in range(8):
      if (bba[0] & bbbitmask) > 0:
         outbit = 1
      else:
         outbit = 0   
      bbser.port = outbit
      outstr = ">" + str(outbit) + outstr[1:] 
      sys.stdout.write('\r' + outstr)
      sys.stdout.flush()
      bbbitmask = bbbitmask * 2
      time.sleep(.2)
   bbser.port = 1
   sys.stdout.write("\n")
   bbser.close()

def waitfor(wf):
   # This was used for debugging and really is only used for the init at this point.
   # wf should be a list with the timeout in the last element
   isfound = False
   idx = 0
   foundlist = []
   capturebytes = []
   to = wf[-1]
   timecheck = time.time()
   while (time.time() <= (timecheck+to)) & (isfound == False): 
      try:
         recvbyte = recvqueuegetraw(1)
         if recvbyte != "":
            recvdata = ord(recvbyte)
            capturebytes = capturebytes + [ recvdata ]
            if recvdata == wf[idx]: 
               foundlist = foundlist + [ recvdata ]
               idx = idx + 1
            else: 
               foundlist = []
               idx = 0
            if idx == len(wf)-1:
               isfound = True
      except:
         print('error')
         break
   return [ isfound, foundlist, capturebytes ]

def dumpqueue():
   # Used for debugging.  Just keeps dumping reads.
   while True:
      try:
         recvdata = recvqueueget(1)
      except:
         break

def sendqueueadd(sendlist):
   # Puts every byte in the sendlist into the sendqueue for service by thread
   for i in sendlist:
      ser.write(chr(i))

def recvqueuegetraw(bytes):
   recvdata = ser.read(bytes)
   return recvdata


def recvqueueget(bytes):
   isread = False
   while isread == False:
      recvbyte = ser.read(bytes)
      if recvbyte != "":
         recvdata = recvbyte
         isread = True
   return recvdata      

def sendcommand(sendlist):
   # Wraps raw KWP command in a length byte and a checksum byte and hands it to sendqueueadd()
   sendlist = [ len(sendlist) ] + sendlist 
   sendlist = sendlist + [ checksum(sendlist) ] 
   sendqueueadd(sendlist)
   cmdval = commandvalidate(sendlist)

def commandvalidate(command):
   # Every KWP command is echoed back.  This clears out these bytes.
   commandvalidate = True
   for i in range( len(command) ):
      recvdata = recvqueueget(1)
      if ord(recvdata) != command[i]:
         commandvalidate = commandvalidate & False
   return commandvalidate   

def checksum(checklist):
   # Calculates the simple checksum for the KWP command bytes.
   checksum = 0
   for i in checklist:
      checksum = checksum + i
   checksum = (checksum & 0xFF) % 0xFF
   return checksum

def getresponse():
   # gets a properly formated KWP responce from a command and returns the data. 
   debugneeds = 4
   numbytes = 0x00
   while numbytes == 0x00:     # This is a hack because sometimes responses have leading 0x00's.  Why?  This removes them.
      numbytes = ord(recvqueueget(1))
   getresponse = [ numbytes ]
   if debug >= debugneeds: print("Get bytes: " + hex(numbytes))
   for i in range( numbytes ):
      recvdata = ord(recvqueueget(1))
      if debug >= debugneeds: print("Get byte" + str(i) + ": " + hex(recvdata))
      getresponse = getresponse + [ recvdata ]
   checkbyte = recvqueueget(1)
   if debug >= debugneeds: print(getresponse)
   if debug >= debugneeds: print("GR: " + hex(ord(checkbyte)) + "<-->" + hex(checksum(getresponse))) 
   return (getresponse + [ ord(checkbyte) ])
   

def readecuid(paramdef):
   # KWP2000 command to pull the ECU ID
   debugneeds = 4
   reqserviceid = [ 0x1A ]
   sendlist = reqserviceid + paramdef
   if debug >= debugneeds: print( sendlist )
   sendcommand(sendlist)
   response = getresponse()
   if debug >= debugneeds: print(response)
   return response

def stopcomm():
   # KWP2000 command to tell the ECU that the communications is finished
   stopcommunication = [ 0x82 ]
   sendlist = stopcommunication
   sendcommand(sendlist)
   response = getresponse()
   return response

def startdiagsession(bps):
   # KWP2000 setup that sets the baud for the logging session
   startdiagnosticsession = [ 0x10 ]
   setbaud = [ 0x86 ]  #Is this the actual function of 0x86?
#   if bps == 10400:
#      bpsout = 0x5f
#   if bps == 14400:
#      bpsout = 0x60
#   if bps == 19200:
#      bpsout = 0x61
   if bps == 38400:
      bpsout = 0x50
   if bps == 56000:
      bpsout = 0x63
   if bps == 57600:
      bpsout = 0x64
#   if bps == 125000:
#      bpsout = 0x65
   sendlist = startdiagnosticsession + setbaud + [ bpsout ]
   sendcommand(sendlist)
   response = getresponse()
   ser.baudrate = bps
   time.sleep(1)
   return response

def accesstimingparameter():
   # KWP2000 command to access timing parameters
   accesstiming_setval = [ 0x083, 0x03 ]
   p2min = [ 0x00 ]
   p2max = [ 0x01 ]
   p3min = [ 0x00 ]
   p3max = [ 0x14 ]
   p4min = [ 0x00 ]
   accesstiming = accesstiming_setval + p2min + p2max + p3min + p3max + p4min
   sendlist = accesstiming
   sendcommand(sendlist)
   response = getresponse()
   return response

def readmembyaddr(readvals):
   # Function to read an area of ECU memory.
   debugneeds = 4
   rdmembyaddr = [ 0x23 ]
   sendlist = rdmembyaddr + readvals
   if debug >= debugneeds: print("readmembyaddr() sendlist: " + hexlist(sendlist) )
   sendcommand(sendlist)
   response = getresponse()
   if debug >= debugneeds: print("readmembyaddr() response: " + hexlist(response) )
   return response

def writemembyaddr(writevals):
   # Function to write to an area of ECU memory.
   debugneeds = 4
   wrmembyaddr = [ 0x3D ]
   sendlist = wrmembyaddr + writevals
   if debug >= debugneeds: print("writemembyaddr() sendlist: " + hexlist(sendlist) )
   sendcommand(sendlist)
   response = getresponse()
   if debug >= debugneeds: print("writemembyaddr() response: " + hexlist(response) )
   return response

def testerpresent():
   # KWP2000 TesterPresent command
   tp = [ 0x3E ]
   sendlist = tp
   sendcommand(sendlist)
   response = getresponse()
   return response

def getrecord():
   # Command to request the actual logging record
   gr = [ 0xb7 ]
   sendlist = gr
   starttime = time.time()
   sendcommand(sendlist)
   response = getresponse()
   return response

def textlist(tl):
   # Outputs a list of bytes as their ASCII characters.
   debugneeds = 4
   textresponse = ""
   for i in range(len(tl)-4):
      textresponse = textresponse + chr(tl[i+3])
   if debug >= debugneeds: print( "textlist() response: " + textresponse )
   return textresponse

def hexlist(hl):
   # Outputs a list of bytes in hex
   hexlist = "[ "
   for i in range(len(hl)):
      hexlist = hexlist + hex( hl[i] )
      if i < ( len(hl) - 1 ):
         hexlist = hexlist + ", "
   hexlist = hexlist + " ]"
   return hexlist

def dumpsendhexstring(dumpstring):
   # Takes a list of characters as a string, turns every two characters into a hex byte and sends it.  
   for i in range(len(dumpstring)/2):
      sendqueueadd([ int('0x'+dumpstring[i*2:(i*2)+2],16) ])

def logheader(config):
   #  Creates headers for the log file from the config files.
   headers = [ '' ]
   headers = headers + [ ''.ljust(83,chr(0x23)) ]
   headers = headers + [ 'Logfile created by ME7-Logger Clone: ' + sys.argv[0] ]
   headers = headers + [ '' ]
   headers = headers + [ 'Used EcuDefinition file: ' + config[0][0] ]
   headers = headers + [ '' ]
   headers = headers + [ 'ECU identified with following data:' ]
   headers = headers + [ 'HWNumber    = ' + config[0][6] ]
   headers = headers + [ 'SWNumber    = ' + config[0][7] ]
   headers = headers + [ 'PartNumber  = ' + config[0][8] ]
   headers = headers + [ 'SWVersion   = ' + config[0][9] ]
   headers = headers + [ 'EngineId    = ' + config[0][10] ]
   headers = headers + [ 'VAGHWNumber = ' ]
   headers = headers + [ 'ModelId     = ' + config[0][11] ]
   headers = headers + [ '' ]
   headers = headers + [ 'Log packet size: ' + str(config[0][12]) + ' bytes' ]
   headers = headers + [ 'Logging with:    ' + config[0][1] + ' samples/second  * Disabled *' ]
   headers = headers + [ 'Used speed is:   ' + config[0][5] + ' baud' ]
   headers = headers + [ 'Used mode is:    ' + config[0][4] + '                 * Disabled *']

   t = time.localtime(time.time())
   timestamp = str(t[2]).rjust(2,'0') + '.' + str(t[1]).rjust(2,'0') + '.' + str(t[0]) + ' ' 
   timestamp = timestamp + str(t[3]).rjust(2,'0') + ':' + str(t[4]).rjust(2,'0') + ':' + str(t[5]).rjust(2,'0')  
   headers = headers + [ 'Log started at:  ' + timestamp ]
   headers = headers + [ '' ]

   header1 = "TimeStamp, "
   header2 = "sec.ms, "
   header3 = "Time, "
   for i in range(1,len(config)):
      header1 = header1 + config[i][0]
      unit = config[i][5]
      if unit[0] == '{':
         unit = unit[1:]
      if unit[-1] == '}':
         unit = unit[:-1] 
      header2 = header2 + unit
      header3 = header3 + config[i][1]
      if i < len(config)-1:
         header1 = header1 + ', '
         header2 = header2 + ', '
         header3 = header3 + ', '
   headers = headers + [ header1 ] + [ header2 ] + [ header3 ]
   return headers

def loglocations(config):
   # Parses the config info and creates the byte list to tell the ECU the memory locations to log.
   response = []
   sendlist = [ 0xb7 ]                           # is 0xB7 the "locator?"
   sendlist = sendlist + [ 0x03 ]                # Number of bytes per field ?

   logpacketsize = 0 
   for i in range(1,len(config)):
      addrstring = config[i][2]
      size = config[i][3]
      if ( size == '1' ):                        # one byte or two 
         sendlist = sendlist + [ int(addrstring[:4],16) ]
      elif (size == '2' ):
         sendlist = sendlist + [ ( int(addrstring[:4],16) + 0x40 ) ]
      sendlist = sendlist + [ int(('0x' + addrstring[4:6]), 16) ]
      sendlist = sendlist + [ int(('0x' + addrstring[6:8]), 16) ]
      logpacketsize = logpacketsize + int(size)
   sendcommand(sendlist)
   response = getresponse()
   return [ sendlist, response, logpacketsize ]
 
 
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
         byteconv = hex(bytes[j])[2:].ljust(2,'0') + byteconv 
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

      ecuconnect = False
     
      while ecuconnect == False:
         print("Attempting ECU connect: " + config[0][3] )
         ser.close()
         time.sleep(1)

         #Bit bang the K-line to start the handshake (byte, baudrate)
         bbseq = [ 0x11 ]
         bbang(bbseq)
   
         #Switch to serial communication
         ser.open()
         ser.ftdi_fn.ftdi_set_line_property(8, 1, 0)
         ser.baudrate = 10400
         ser.flush()
 

         # Wait for ECU response to bit bang
         waithex = [ 0x55, 0xef, 0x8f, 1 ]
         waitfor(waithex)

         # Wait a bit 
         time.sleep(.026)

         # Send 0x70
         sendqueueadd([ 0x70 ])

         # 0xee means that we're talking to the ECU
         waithex = [ 0xee, 1 ]
         response = waitfor(waithex)
         if response[0] == True:
             ecuconnect = True
         else:
             print("ECU Connect Failed.  Retrying.")

      print("....sealed")

      print("Connected at 14400")
      response = readecuid([ 0x94 ])
      swnumber = textlist(response)
      # Insert software number checking here
 
      response = startdiagsession(int(config[0][5]))
      if debug >= 3:  print("startdiagsession(" + config[0][5] +") response: " + hexlist(response) )
      print("Connected at " + config[0][5] )

      response = accesstimingparameter()
      if debug >= 3:  print("accesstimingparameter() response: " + hexlist(response) )
 
      print("Timing Set, reading and preparing memory")

      # I don't know how this is used.  Is it really ECU Scaling?
      ecuid_0x81 = readecuid([ 0x81 ])
      if debug >= 3:  print("ecuid_0x81 =" + hexlist(ecuid_0x81) )

      response = readecuid([ 0x94 ])
      swnumber = textlist(response)
      if debug >= 3:  print("SWNumber =" + swnumber)

      response = readecuid([ 0x92 ])
      hwnumber = textlist(response)
      if debug >= 3:  print("HWNumber =" + hwnumber)

      response = readecuid([ 0x9b ])
      partraw = textlist(response)
      if debug >= 3:  print("partraw  =" + partraw)
      partnumber = partraw[:12]
      swversion = partraw[12:16]
      engineid = partraw[26:42]
      modelid = partraw[42:]
      # Now that we know it, tacking ModelId on the end of the ecu config info
      config[0] = config [0] + [ modelid ]

      #I don't know how this is used.
      ecuid_0x9c = readecuid([ 0x9c ])
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
         response = readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )
   
         memaddrhi = [ 0x00 ]
         memaddrmid = [ 0xe2 ]
         memaddrlow = [ 0x28 ]
         memsize = [ 0x04 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize
         response = readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )
   
         # Why is this extra 0x00 needed?
         sendqueueadd( [ 0x00 ] )
         recvqueueget(1)

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
         response = writemembyaddr( request )   # Response = 0x7d + memory address
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         sendqueueadd( [ 0x00 ] )                          # Why is this extra 0x00 needed?
         recvqueueget(1)

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
         response = writemembyaddr( request )   # Response = 0x7d + memory address
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         sendqueueadd( [ 0x00 ] )                          # Why is this extra 0x00 needed?
         recvqueueget(1)

         # Write to memory
         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7b ]
         memaddrlow = [ 0x00 ]    # Write starting at 0x38 0x7b 0x00
         memsize = [ 0x80 ]
         # No idea what this does yet:
         memvalues = [ 0x70, 0x88, 0xed, 0xf6, 0xf2, 0xf4, 0x1c, 0xff, 0xd7, 0x10, 0x38, 0x0, 0xf6, 0xf4, 0xc0, 0x7a, 0xf6, 0xf4, 0xc2, 0x7a, 0x98, 0x60, 0x98, 0x70, 0x98, 0x80, 0xfa, 0x0, 0x66, 0x3b, 0x88, 0xb0, 0x88, 0xa0, 0x88, 0x90, 0x88, 0x80, 0x88, 0x70, 0x88, 0x60, 0xe1, 0xf, 0xf2, 0xf4, 0xca, 0xe1, 0x49, 0x81, 0x2d, 0x4, 0xf2, 0xf4, 0xce, 0xe1, 0x8, 0x41, 0x99, 0xf4, 0x49, 0xf0, 0x2d, 0x5, 0x49, 0xf3, 0x2d, 0x31, 0x49, 0xf4, 0x2d, 0x2f, 0xd, 0x6c, 0xf0, 0x9c, 0xe7, 0xf8, 0xf7, 0x0, 0xb9, 0x89, 0x8, 0x91, 0xe6, 0xfa, 0x80, 0x7c, 0xe6, 0xfb, 0x38, 0x0, 0xd7, 0x0, 0x38, 0x0, 0xf3, 0xfc, 0xc4, 0x7a, 0x67, 0xfc, 0x7f, 0x0, 0x2d, 0x11, 0xdc, 0x1b, 0x98, 0x4a, 0x98, 0x5a, 0xf1, 0xeb, 0xe1, 0xb, 0x49, 0xe2, 0x2d, 0x4, 0xdc, 0x5, 0x99, 0xd4, 0xb9, 0xd9, 0x8, 0x91 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize + memvalues
         response = writemembyaddr( request )   # Response = 0x7d + memory address
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         sendqueueadd( [ 0x00 ] )                          # Why is this extra 0x00 needed?
         recvqueueget(1)

         # Write to memory
         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7b ]
         memaddrlow = [ 0x80 ]    # Write starting after the previous write
         memsize = [ 0x80 ]
         # No idea what this does yet:
         memvalues = [ 0xdc, 0x5, 0x99, 0xd4, 0xb9, 0xd9, 0x8, 0x91, 0x29, 0xc1, 0x3d, 0xef, 0xf0, 0x49, 0x20, 0x4c, 0xe6, 0xf6, 0x0, 0x8, 0x74, 0xf6, 0x74, 0xe0, 0x98, 0x60, 0x98, 0x70, 0x98, 0x80, 0x98, 0x90, 0x98, 0xa0, 0x98, 0xb0, 0xdb, 0x0, 0xf2, 0xf4, 0xca, 0xe1, 0x29, 0x82, 0xf1, 0xa8, 0xe1, 0xb, 0xe6, 0xfa, 0x80, 0x7c, 0xe6, 0xfb, 0x38, 0x0, 0x49, 0xf3, 0x2d, 0x9, 0x6, 0xfa, 0x0, 0x1, 0xd7, 0x0, 0x38, 0x0, 0xf3, 0xfb, 0xc4, 0x7a, 0x47, 0xfb, 0x40, 0x0, 0x3d, 0xfe, 0xf2, 0xf4, 0xce, 0xe1, 0x8, 0x42, 0x49, 0xa3, 0x8d, 0x19, 0x99, 0xe4, 0x99, 0xd4, 0x99, 0xc4, 0xf1, 0xfe, 0x67, 0xfe, 0xbf, 0x0, 0xdc, 0x2b, 0xb9, 0xca, 0x8, 0xa1, 0xb9, 0xda, 0x8, 0xa1, 0xdc, 0xb, 0xb9, 0xea, 0x8, 0xa1, 0xe1, 0x1e, 0x67, 0xff, 0x40, 0x0, 0x3d, 0x1, 0x9, 0xe1, 0xdc, 0xb ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize + memvalues
         response = writemembyaddr( request )   # Response = 0x7d + memory address
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         sendqueueadd( [ 0x00 ] )                          # Why is this extra 0x00 needed?
         recvqueueget(1)

         # Write to memory
         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7c ]
         memaddrlow = [ 0x00 ]    # Write starting after the previous write
         memsize = [ 0x46 ]
         # No idea what this does yet:
         memvalues = [ 0xb9, 0xea, 0x8, 0xa1, 0x9, 0xb1, 0x29, 0xa3, 0xd, 0xe5, 0x67, 0xfb, 0x7f, 0x0, 0xd7, 0x0, 0x38, 0x0, 0xf7, 0xfb, 0xc4, 0x7a, 0xf0, 0x9c, 0xe7, 0xf8, 0xf7, 0x0, 0xb9, 0x89, 0xe0, 0x14, 0xd, 0xb7, 0xe6, 0xf4, 0xff, 0xf7, 0x64, 0xf4, 0x74, 0xe0, 0xf0, 0xe9, 0xe7, 0xf8, 0x7f, 0x0, 0xb9, 0x8e, 0x8, 0xe1, 0xe7, 0xf8, 0xb7, 0x0, 0xb9, 0x8e, 0x8, 0xe1, 0xe7, 0xf8, 0x12, 0x0, 0xb9, 0x8e, 0xe1, 0x38, 0xd, 0xa9 ] 
         request = memaddrhi + memaddrmid + memaddrlow + memsize + memvalues
         response = writemembyaddr( request )   
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         # Read back what we wrote earlier  
         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7a ]
         memaddrlow = [ 0x00 ]
         memsize = [ 0x80 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize
         response = readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7a ]
         memaddrlow = [ 0x80 ]
         memsize = [ 0x80 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize
         response = readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7b ]
         memaddrlow = [ 0x80 ]
         memsize = [ 0x80 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize
         response = readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         memaddrhi = [ 0x38 ]
         memaddrmid = [ 0x7c ]
         memaddrlow = [ 0x00 ]
         memsize = [ 0x46 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize
         response = readmembyaddr( request )
         if debug >= 3:  print("readmembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         # Write to memory
         memaddrhi = [ 0x00 ]
         memaddrmid = [ 0xe2 ]
         memaddrlow = [ 0x28 ]   
         memsize = [ 0x04 ]
         memvalues = [ 0x00, 0x3a, 0xe1, 0x00 ]
         request = memaddrhi + memaddrmid + memaddrlow + memsize + memvalues
         response = writemembyaddr( request )
         if debug >= 3:  print("writemembyaddr(): request: " + hexlist(request) + " response: " + hexlist(response) )

         response = testerpresent()
         if debug >= 3:  print("testerpresent(): response: " + hexlist(response))

         sendqueueadd( [ 0x00 ] )                          # Why is this extra 0x00 needed?
         recvqueueget(1)   

         # Tell ECU memory locations to log, based on the config and ecu file data:
         response = loglocations(config)
         if debug >= 3:  print("loglocations(): request: " + hexlist(response[0]) + " response: " + hexlist(response[1]) )
         # grab logpacketsize from loglocations() return and tack it to the end of ecu config info
         config[0] = config[0] + [ response[2] ]

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
            response = getrecord()
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
               time.sleep((samplerate)-(timerfinish-timerstart))	                  # I'd love to do this but it's too slow already!

      else:
         print("Config check failed")

   # Catch ctrl-c
   except KeyboardInterrupt:
      sys.stdout.write('\r' + "Stopping".ljust(30) + '\n')

   sys.stdout.write('\r')
   sys.stdout.flush()
   
   # Shut down the thread and wrap things up.
   # controlqueue.put(["end"])
   # time.sleep(1)
   
   outfile.flush()
   
   print("Logging Finished")


   
if __name__ == '__main__':

   try:
     main(debug)

   except KeyboardInterrupt:
     print("hard stop")

