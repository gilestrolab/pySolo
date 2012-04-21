#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  sleepDeprivator.py
#  
#  Copyright 2012 Giorgio Gilestro <giorgio@gilest.ro>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

from DAMrealtime import DAMrealtime
from time import sleep
import serial

use_serial = True

if use_serial: 
    ser = serial.Serial('/dev/ttyACM0', 57600)
    sleep(2)

#fullpath to a single monitor file (or to of a folder containing all monitors)
path = '/home/gg/Desktop/DAMS/'


r = DAMrealtime(path=path, folderName='videoDAM')

for fname in r.listDAMMonitors():
    command = r.deprive(fname)
    print command
    if use_serial: ser.write(command)

if use_serial: ser.close()
