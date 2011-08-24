#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       pysolo_lib.py
#       
#       Copyright 2011 Giorgio Gilestro <giorgio@gilest.ro>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.


import os, cPickle, datetime
from urllib import urlopen
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
from numpy.ma import *

import wx.lib.newevent
myEVT_FILE_MODIFIED, EVT_FILE_MODIFIED = wx.lib.newevent.NewCommandEvent()

from pysolo_path import imgPath
from pysolo_slices import *
from pysolo_sleep_fun import *

from pysolo_options import userConfig, customUserConfig
GUI = dict()

def logText(text):
    """
    Log message in the logfile
    """
    now = datetime.datetime.today()
    text = '%04d/%02d/%02d\t%02d:%02d\t%s\n' % (now.year, now.month, now.day, now.hour, now.minute, text)
    try:
        logFile = open ('pySolo.log', 'a')
    except:
        print 'Could not open the log file.\nMake sure you have enough priviledge.'
    logFile.write(text)
    logFile.close()      


class partial: #AKA curry
    """
    This functions allows calling another function upon event trigger and pass arguments to it
    ex buttonA.Bind (wx.EVT_BUTTON, partial(self.Print, 'Hello World!'))
    """

    def __init__(self, fun, *args, **kwargs):
        self.fun = fun
        self.pending = args[:]
        self.kwargs = kwargs.copy()

    def __call__(self, *args, **kwargs):
        if kwargs and self.kwargs:
            kw = self.kwargs.copy()
            kw.update(kwargs)
        else:
            kw = kwargs or self.kwargs

        return self.fun(*(self.pending + args), **kw)

def SetFileAsModified(target):
    """
    Starts an EVENT telling around that the file has been
    modified from its original form
    """
    #create the event
    evt = myEVT_FILE_MODIFIED(wx.NewId(), Modified=True)
    #post the event
    wx.PostEvent(target, evt)

def list2str(l, separator=' + '):
    """
    Takes the items in a list and expand them in a string
    where items are separated by 'separator'
    """
    return separator.join ( [str(el) for el in l] )

def CheckUpdatedVersion():
    """
    Check for an updated version of the program online
    """
    webaddress = 'http://www.pysolo.net/last_version.txt'
    try:
        version = urlopen(webaddress).read().rstrip('\n')
        if len(version) > 10: version = '0.0.0'
    except:
        version = '0.0.0'
        
    if version > pySoloVersion:
        return version
    else:
        return False


def SaveDADFile(cDAM, filename):
    """
    Saves away the content of the DAM memory in a DAD file
    """

    try:
        filename = str(filename)
        if '.dad' not in filename: filename = filename + '.dad'
        tmpFileName = '%s.tmp' % filename
        tmpFileHandle = open (tmpFileName, 'wb')

        headerlist = []
        for sDAM in cDAM:
            newHeader = sDAM.getHeader()
            headerlist.append(newHeader)

        cPickle.dump(headerlist, tmpFileHandle)

        for sDAM in cDAM:
            sDAM.saveRawData(tmpFileHandle)

        tmpFileHandle.close()

        zipArchive = ZipFile(filename, 'w', compression = ZIP_DEFLATED)
        zipArchive.write(tmpFileName)
        zipArchive.close()
        os.remove(tmpFileName)
        success = True
    except:
        success = False

    return success

def LoadDADFile(filename):
    """
    Open the zipped file and copies its contents in the DAM variable (DAM is a list of DAMslice)
    """
    cDAM = []
    filename = str(filename)
##    try:
    if True:
        #extract the content of the zip file into a .tmp file
        ZipDamFile = ZipFile (filename, 'r')
        tmpfilename = ZipDamFile.namelist()[0]

        damFile = open (filename+'.tmp', 'wb')
        damFile.write( ZipDamFile.read(tmpfilename) )
        damFile.close()
        ZipDamFile.close()

        tmpFileName = filename+'.tmp'
        damFile = file (tmpFileName, 'rb')

        headerlist = cPickle.load(damFile)

        for header in headerlist:
            sliceType, heads = header[0], header[1]
            cDAM.append (sliceType(*heads))
            cDAM[-1].loadRawData(damFile)

        damFile.close()
        os.remove(tmpFileName)
        success = cDAM

##    except:
##
##        success = False

    return success


