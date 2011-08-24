#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       pysolo.py
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

import wx, os
#os.sys.stdout = open('pysolo_screen.txt','w',0); os.sys.stderr = open('pysolo_errors.txt','w',0)

class MySplashScreen(wx.SplashScreen):
    def __init__(self):
        from pysolo_path import imgSplash
        bmp = wx.Image(imgSplash).ConvertToBitmap()
        wx.SplashScreen.__init__(self, bmp,
                                 wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                                 4000, None, -1)

class MyApp(wx.App):
    def OnInit(self):

        # SplashScreen
        splash = MySplashScreen()
        splash.Show(True)

        #pySolo_DBFrame
        from pysolo_db import pySolo_DBFrame
        self.DBframe = pySolo_DBFrame(None, -1, "PySolo - Database", siblingMode = True)
        self.DBframe.Show(True)

        #pySolo_AnalysisFrame
        from pysolo_anal import pySolo_AnalysisFrame
        self.AnalFrame = pySolo_AnalysisFrame(None, -1, "PySolo - Data Analysis", siblingMode = True)
        self.AnalFrame.Show(False)

        self.AnalFrame.__SetBrother__(self.DBframe)
        self.DBframe.__SetBrother__(self.AnalFrame)

        self.SetTopWindow(self.DBframe)
        return True


if __name__ == '__main__':

    # Run program
    app=MyApp()
    app.MainLoop()



