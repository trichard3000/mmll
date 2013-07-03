#!/usr/bin/python

'''
me7lconfig.py
- a module with several functions to interact with the ME7Logger config files

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

#from __future__ import print_function
import sys, time, re


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
   headers = headers + [ 'Logging with:    ' + config[0][1] + ' samples/second' ]
   headers = headers + [ 'Used speed is:   ' + config[0][5] + ' baud' ]
   headers = headers + [ 'Used mode is:    ' + config[0][4] + '              * Disabled *']

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
   sendlist = []                          
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
   return [ sendlist, logpacketsize ]
 
 
def main():
   print('loading ' + sys.argv[0])
   
if __name__ == '__main__':

   try:
     main()

   except KeyboardInterrupt:
     print("Ctrl-c")

