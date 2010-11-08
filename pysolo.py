#!/usr/bin/env python
import wx, os
#os.sys.stdout = open('screen.txt','w',0); os.sys.stderr = open('errors.txt','w',0)

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



