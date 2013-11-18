#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  check_components.py
#  
#  Copyright 2013 Giorgio Gilestro <giorgio@gilest.ro>
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

import os
print ("Python version: %s" % os.sys.version)

try:
    import wx
    print ("WX Version: %s" % wx.VERSION_STRING)
except:
    print ("could not import wx")

try:
    import scipy
    print ("scipy Version: %s" % scipy.__version__)
except:
    print ("could not import scipy")

try:
    import numpy
    print ("scipy Version: %s" % numpy.__version__)
except:
    print ("could not import numpy")
    
try:
    import matplotlib
    print ("matplotlib Version: %s" % matplotlib.__version__)
except:
    print ("could not import matplotlib")
    
try:
    import cv2
    print ("opencv Version: %s" % cv2.__version__)
except:
    print ("could not import opencv")
    
    
