mmll
====

the Most Minimal Linux Logger

Copyright 2013 Ted Richardson.
Distributed under the terms of the GNU General Public License (GPL)
See LICENSE.txt for licensing information.

<pre>
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
</pre>

Notes:

This is a very basic logger for Bosch ME7 ECU's, common in many Volkswagen 
and Audi cars from the late 1990's to the early 2000's. There are many, many 
cars for which this won't work.  I'm sorry if your car is one of them.

This is a very early version.  Bugs are to be expected.

I wrote it as a companion tool to ME7Logger, for 
those who want to mess around with logging from a Linux host.  

ME7Logger can be found at: 
http://nefariousmotorsports.com/forum/index.php?topic=837.0title=

mmll.py requires the same configuration files that you use to log with ME7L.
Even though many ME7L options aren't supported, many users should be able to 
simply copy their ME7L cfg and ecu files into a directory and start logging 
from there.

Because I was shooting for minimal KWP2000 functionality, only the following 
communication config is currently supported:

FTDI only - ** Requires pylibftdi  **

ecu file:
Connect     = SLOW-0x11
Communicate = HM0
LogSpeed    = 38400, 56000, or 57600 

cfg file:
SamplesPerSecond - Different host systems will have different max values.

The log file output is also "cloned" from ME7Logger as this was the easiest
way to provide instant compatibility for the logs to be graphed with ECUxPlot.

ECUxPlot can be found at:
http://nyet.org/cars/ECUxPlot/


Your results may vary.  

--
trichard3000

+++++

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

