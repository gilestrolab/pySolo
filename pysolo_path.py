#!/usr/bin/env python
import os

#This part is to decide whether we are running a .deb package or not
debian=False
if debian:
    cPath = '/opt/pysolo/'
    optPath = os.environ['HOME']    
else:
    cPath = os.path.dirname(os.sys.argv[0])
    optPath = cPath    

imgPath = os.path.join (cPath, 'img')
imgSplash = os.path.join(imgPath, 'splash.png')
panelPath = os.path.join (cPath, 'panels')
