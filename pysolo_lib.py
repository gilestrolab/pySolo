#!/usr/bin/env python
# ################################################################# #
#                                                                   #
# pySolo_lib                                                          #
# This file contains function of general use for the pySolo program   #
# None of the contents of this file should be modified by the user  #
# for proper functioning of the software.                           #
# Please visit the website for more information:                    #
# http://www.pysolo.net                               #
#                                                                   #
# ################################################################# #
#                                                                   #
# As of 10/31/2008 working fine with:                                #
# pySolo version: 0.3
# Python version: 2.5.2 (r252:60911, Oct  5 2008, 19:24:49) 
# [GCC 4.3.2]
# wxPython version: 2.8.8.0
# wxmpl version: 1.2.9-custom
# matplotlib version: 0.98.3
# numpy version: 1.1.1
# scipy version: 0.6.0                                                  #
#                                                                   #
# ################################################################# #


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
    out = ''
    a = len(separator)
    for i in l:
        out += str(i) + separator
    return out[:-a]

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


