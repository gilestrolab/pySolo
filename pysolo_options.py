#!/usr/bin/env python
# All the classes here are used in the option panel

import wx, os, cPickle

from pysolo_slices import pySoloVersion
from pysolo_path import optPath

import wx.lib.filebrowsebutton as filebrowse
from wx.lib.masked.numctrl import NumCtrl
import wx.lib.colourselect as csel
import wx.lib.masked as masked

class pySoloOption(dict):
        
    
    def AddOption(self, option_name, option_type, option_checked, option_choices, option_description):
        '''
        Called in from the panel code, will add a new variable option_name of type option_type. Default value
        will be at position option_checked of the list option_choices and option_description is used to describe
        the variable in the option Frame

        option_name = the name of the variable for the current panel
        option_type = boolean | radio | text | multiple
        option_checked = the int number indicating the position of the chosen value in option_choices. Must be 0 if option_type = text
        option_choices = a list containing all the possible choices
        '''
        
        option_name = str(option_name)
        ot = ['boolean', 'radio', 'text', 'multiple']
        if option_type not in ot:
            raise 'option_type must be one of the following: %s' % ot
        
        if option_type == 'text':
            option_checked = 0
            if type(option_choices) != list: option_choices = [option_choices]

        option_choices = [str(i) for i in option_choices]
        self[option_name] = [option_type, option_checked, option_choices, option_description]

    def GetOption(self, option_name):
        '''
        Retrieve Selected value of a custom Panel variable
        If boolean will return True or False
        If radio or check will return the value in the list option_choices
        If text will return the text value as string.
        '''

        option_type = self[option_name][0]
        option_choices = self[option_name][2]

        option_checked = self[option_name][1]

        if option_type == 'multiple':
            value = [option_choices[v] for v in option_checked]

        elif option_type == 'boolean': #for boolean first choice is always True, second choice always False
            value = (int(option_checked) == 0)
            
        elif option_type == 'text' and type(option_choices) != list:
            value = option_choices
            
        else:
            value = option_choices[int(option_checked)]

        return value

    def GetOptionValue(self, option_name):
        '''
        alias of GetOption
        '''
        return self.GetOption(option_name)

    def GetOptionType(self, option_name):
        '''
        return option type
        '''
        return self[option_name][0]
    
    def GetOptionDescription(self, option_name):
        '''
        return option description
        '''
        return self[option_name][3]

    def SetOption(self, n):
        '''
        '''



def LoadPreferenceFile(filename = 'pysolo.opt'):
    '''
    LoadPreferenceFile(filename = 'pysolo.opt')
    Retrieves all user preferences from a binary file called filename
    Returns three values:
    PreferenceFileFound as boolean
    userConfig, customUserConfig as dictionaries
    '''

    filename = os.path.join(optPath, filename)
    
    try:
        preferenceFile = open (filename, 'r')
        userConfig, customUserConfig = cPickle.load(preferenceFile)
        preferenceFile.close()
        PreferenceFileFound = True

    except:
        #logText ('Configuration file was not found. Using default values')
        userConfig = dict()
        customUserConfig = dict()
        #Here all the default values for all the userConfig Variables
        userConfig['plotting_colors'] = ['#333333', '#0066cc', '#33cc33', '#cc0033', '#ffcc00', '#990099', '#660000', '#999999', '#99ccff', '#ccff99', '#ffcc99', '#ffff00', '#ff99cc', '#666666', '#336633', '#663366', '#ffff99', '#466086', '#ff8040', '#989e67']
        userConfig['plotting_colors_name'] = ['Dark Grey', 'Blue', 'Green', 'Red', 'Yellow', 'Purple', 'Brown', 'Light Grey', 'Light Blue', 'Light Green', 'Light Pink', 'Bright Yellow', 'Pink', 'Grey', 'Dark Green', 'Dark Purple', 'Light Yellow', 'Blue Marine', 'Dark Orange', 'Olive Green']
        userConfig['DAMoutput'] = '/'

        userConfig['DAMinput'] = '/'
        userConfig['DAMextension'] = '.txt'

        userConfig['DAMtype'] = 'Channel' #Other possible choices are Monitor and Custom
        userConfig['Canvas'] = 'wxmpl'
        userConfig['FigureSize'] = (10, 6)#canvas size in inches
        userConfig['Panels'] = dict()
        
        userConfig['DataTypes'] = ['Regular', 'TANK', 'Video']
        userConfig['RecentFiles'] = []
        userConfig['crosshair'] = False
        userConfig['use_std'] = True 
        userConfig['use_dropout'] = True
        userConfig['min_sleep'] = 0
        userConfig['max_sleep'] = 1400
        userConfig['virtual_trikinetics'] = True
        userConfig['min_distance'] = 300
        userConfig['max_distance'] = 1000
        userConfig['dpi'] = 250
        userConfig['checkUpdate'] = False

        preferenceFile = open ('pysolo.opt', 'w')
        toDump = userConfig.copy(), customUserConfig.copy()
        cPickle.dump (toDump, preferenceFile)
        preferenceFile.close()
        PreferenceFileFound = False
      

    userConfig['option_file'] = filename
    return PreferenceFileFound, userConfig, customUserConfig

PreferenceFileFound, userConfig, customUserConfig = LoadPreferenceFile()

def SavePreferenceFile(userConfig, customUserConfig):
    '''
    Saves all the user preferences in a binary file
    the name of the file is stored in the userConfig dictionary
    returns a boolean on whether the operation was successful
    '''
    try:
        filename = userConfig['option_file']
        preferenceFile = open (filename, 'w')
        toDump = (userConfig, customUserConfig)
        cPickle.dump (toDump, preferenceFile)
        preferenceFile.close()
        return True
    except:
        return False

class partial: #AKA curry
    '''
    This functions allows calling another function upon event trigger and pass arguments to it
    ex buttonA.Bind (wx.EVT_BUTTON, partial(self.Print, 'Hello World!'))
    '''

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

def CopyDict(inDict):
    '''
    This function is required because of a bug in the shallow copy
    function of a dictionary in python.
    The original copy() function would not make a shallow copy of those
    dictionary keys that are of type "list"
    '''
    return inDict
    outDict = dict()

    for key in inDict:
        if type(inDict[key]) == list:
            outDict[key] = inDict[key][:]
        elif type(inDict[key]) == dict:
            outDict[key] = CopyDict(inDict[key])
        else:
            outDict[key] = inDict[key]

    return outDict

def color_hex2dec(col_list):
    '''
    Takes the list of colors indicated as hex values and return
     a list of colors as tuple of integer values
    '''
    hex_tuples = []
    for color in col_list:
        red, green, blue = int(color[1:3],16), int(color[3:5],16), int(color[5:],16)
        hex_tuples.append((red, green, blue))
    return hex_tuples




class OptionsFilesFolderPanel(wx.ScrolledWindow):
        '''
        Creates the panel that allow choosing general options
        '''
        def __init__(self,  parent,  user_config,  customuser_config):

            self.temp_userconfig = user_config
            self.temp_customuserconfig = customuser_config

            wx.ScrolledWindow.__init__(self,  parent)
            sz1 = wx.BoxSizer(wx.VERTICAL)

            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items = []

            items.append ( wx.StaticText(self, -1, '\nSelect the DAM Folder.') )
            items[-1].SetFont(titleFont)
            items.append (  wx.StaticText(self, -1, 'The folder should contain the raw data as output of the DAM monitor.\nFiles should be arranged in a hierarchy of folders of type: \\yyyy\\mm\\dd\\\n') )
            items.append ( filebrowse.DirBrowseButton(self, -1, size=(400, -1), changeCallback = partial(self.dbbCallback, 'DAMinput'), startDirectory=self.temp_userconfig['DAMinput']  ))
            items[-1].SetValue(self.temp_userconfig['DAMinput'])
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ))

            items.append ( wx.StaticText(self, -1, '\nSelect the Output Folder.') )
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'The folder where the .DAL and .DAD files are going to be saved.') )
            items.append ( filebrowse.DirBrowseButton(self, -1, size=(400, -1), changeCallback = partial(self.dbbCallback, 'DAMoutput'), startDirectory=self.temp_userconfig['DAMoutput'] ) )
            items[-1].SetValue(self.temp_userconfig['DAMoutput'])
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ))

            items.append ( wx.StaticText(self, -1, '\nSelect the extension of the input files.') )
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'What is the extension of the file containing the raw data? Default is ".txt".\nLeave blank for none.' ))
            items.append ( wx.TextCtrl (self, -1, size=(100,-1), name='Select your extension' ) ) 
            items[-1].Bind( wx.EVT_TEXT, partial(self.dbbCallback, 'DAMextension') )
            items[-1].SetValue(self.temp_userconfig['DAMextension'])
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ))

            # Group of radio controls:

            items.append (  wx.StaticText(self, -1, '\nSelect RAW Data structure.') )
            items[-1].SetFont(titleFont)
            items.append (  wx.StaticText(self, -1, 'Select the version of the input type file.\n') )

            grid1 = wx.FlexGridSizer( 0, 1, 0, 0 )
            self.DAM_version_radio = []
            self.DAM_version_radio.append( wx.RadioButton( self, -1, 'Trikinetics - Channel Files', name = 'Channel', style = wx.RB_GROUP ) )
            self.DAM_version_radio.append( wx.RadioButton( self, -1, 'Trikinetics - Monitor Files', name = 'Monitor' ) )
            self.DAM_version_radio.append( wx.RadioButton( self, -1, 'pySolo Video - Distance', name = 'pvg_distance' ) )
            self.DAM_version_radio.append( wx.RadioButton( self, -1, 'pySolo Video - Virtual Beam Split', name = 'pvg_beam' ) )
            self.DAM_version_radio.append( wx.RadioButton( self, -1, 'pySolo Video - Raw Data', name = 'pvg_raw' ) )
            
            #not active yet
            #self.DAM_version_radio[-1].Enable(False)

            for radio in self.DAM_version_radio:
                grid1.Add( radio, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
                radio.Bind(wx.EVT_RADIOBUTTON, partial(self.OnGroupSelect, 'DAMtype', bool=False ))
            ck = ['Channel', 'Monitor', 'pvg_distance', 'pvg_beam', 'pvg_raw'].index(self.temp_userconfig['DAMtype'])
            self.DAM_version_radio[ck].SetValue(True)

            items.append (grid1)
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ))

            # Group of radio controls:
            items.append (  wx.StaticText(self, -1, '\nAutomatically check for updates on start.') )
            items[-1].SetFont(titleFont)
            items.append (  wx.StaticText(self, -1, 'Do this only if your computer is always connected to the Internet.\n') )

            grid1 = wx.FlexGridSizer( 0, 1, 0, 0 )
            self.checkUpdate_radio = []
            self.checkUpdate_radio.append( wx.RadioButton( self, -1, 'Yes', name = 'checkUpdate', style = wx.RB_GROUP ) )
            self.checkUpdate_radio.append( wx.RadioButton( self, -1, 'No', name = 'no_checkUpdate' ) )

            for radio in self.checkUpdate_radio:
                grid1.Add( radio, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
                radio.Bind(wx.EVT_RADIOBUTTON, partial(self.OnGroupSelect, 'checkUpdate', bool=True ))
            ck = not self.temp_userconfig['checkUpdate']
            self.checkUpdate_radio[ck].SetValue(True)

            items.append (grid1)
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ))


            sz1.AddMany (items)
            self.SetSizer(sz1)
            sz1.Fit(self)

        def dbbCallback(self, key, event):
            self.temp_userconfig[key] = event.GetString()

        def OnGroupSelect( self, key, event=None, bool=False ):
            if bool:
                self.temp_userconfig[key] = (event.EventObject.GetName() == key)
            else:
                self.temp_userconfig[key] = event.EventObject.GetName()
                

class OptionsVideoPanel(wx.ScrolledWindow):
        '''
        Create the panel to choose basic options about Video
        '''
        def __init__(self, parent, user_config, customuser_config):

            self.temp_userconfig = user_config
            self.temp_customuserconfig = customuser_config

            wx.ScrolledWindow.__init__(self,  parent)
            sz1 = wx.BoxSizer(wx.VERTICAL)

            items = []
            items.append ( wx.StaticText(self, -1, '\nActivity computation system.') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'Activity of the flies can be computed on the basis of the distance they walk\nor using a virtual TriKinetic Monitor System. In the second case, the video data will be analized counting how many times\nthe flies have crossed an imaginary line that runs in the middle of the recording area, emulating the IR system.'))
            #sz1.AddMany (items)

            grid1 = wx.FlexGridSizer( 0, 1, 0, 0 )
            self.use_vtm_radio = []
            self.use_vtm_radio.append( wx.RadioButton( self, -1, 'Use virtual Trikinetics Monitor System', name = 'virtual_trikinetics', style = wx.RB_GROUP  ) )
            self.use_vtm_radio.append( wx.RadioButton( self, -1, 'Use distance', name = 'no_virtual_trikinetics') )

            for radio in self.use_vtm_radio:
                grid1.Add( radio, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
                radio.Bind(wx.EVT_RADIOBUTTON, partial(self.OnGroupSelect, 'virtual_trikinetics'))
            ck = not self.temp_userconfig['virtual_trikinetics']    
            self.use_vtm_radio[ck].SetValue(True)

            items.append (grid1)
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ) )
            
            items.append ( wx.StaticText(self, -1, '\nMinimum and Maximum distances to be called movement.') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'Tweak the values here to define the the minimum and maximum distance (in pixel) for the movement range.\nDetected movements that will have a smaller or bigger threshold will be considered noise and ignored.\nThis setting depends on the quality of your acquisition and on your desire to detect small fly movements'))
            
            grid2 = wx.BoxSizer(wx.HORIZONTAL)
            mins = str(self.temp_userconfig['min_distance'])
            maxs = str(self.temp_userconfig['max_distance'])
            min_sleep = masked.TextCtrl(self , -1, mins, mask = "####")
            max_sleep = masked.TextCtrl(self , -1, maxs, mask = "####")
            min_sleep.Bind(wx.EVT_TEXT, partial(self.OnChangeSleepValues, 'min_distance'))
            max_sleep.Bind(wx.EVT_TEXT, partial(self.OnChangeSleepValues, 'max_distance'))
            grid2.Add(min_sleep, 0, wx.RIGHT, 3)
            grid2.Add(max_sleep, 0, wx.LEFT, 3)
            items.append(grid2)

            sz1.AddMany (items)
            self.SetSizer(sz1)
            sz1.Fit(self)

        def OnChangeSleepValues(self, key, event):
            try:
                self.temp_userconfig[key] = int( n )
            except:
                pass

        def OnGroupSelect( self, key, event ):
            self.temp_userconfig[key] = (event.EventObject.GetName() == key)

            

class OptionsSleepPanel(wx.ScrolledWindow):
        '''
        Create the panel to choose basic options about sleep
        '''
        def __init__(self,  parent,  user_config,  customuser_config):

            self.temp_userconfig = user_config
            self.temp_customuserconfig = customuser_config

            wx.ScrolledWindow.__init__(self,  parent)
            sz1 = wx.BoxSizer(wx.VERTICAL)

            items = []
            items.append ( wx.StaticText(self, -1, '\nUse dropout flies.') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'A dropout fly is a fly that died during the course of the experiment, for instance during the last days.\nHere you can decide on whether you want to include in your experiments.\nNB: this option will not affect the behaviour of all the panels\n'))
            #sz1.AddMany (items)

            grid1 = wx.FlexGridSizer( 0, 1, 0, 0 )
            self.use_dropout_radio = []
            self.use_dropout_radio.append( wx.RadioButton( self, -1, 'Use dropout flies', name = 'use_dropout', style = wx.RB_GROUP ) )
            self.use_dropout_radio.append( wx.RadioButton( self, -1, 'Do not use dropout flies', name = 'no_dropout' ) )

            for radio in self.use_dropout_radio:
                grid1.Add( radio, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
                radio.Bind(wx.EVT_RADIOBUTTON, partial(self.OnGroupSelect, 'use_dropout'))
            ck = not self.temp_userconfig['use_dropout']    
            self.use_dropout_radio[ck].SetValue(True)

            items.append (grid1)
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ) )
            
            items.append ( wx.StaticText(self, -1, '\nSleep limits.') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'Enter the min and max values that are to be used to determine which flies to use.\nOnly flies that slept more than the minimum value and less than then maximum are taken.\nValues have to be entered in minutes (24H = 1440minutes)\n'))
            
            grid2 = wx.BoxSizer(wx.HORIZONTAL)
            mins = str(self.temp_userconfig['min_sleep'])
            maxs = str(self.temp_userconfig['max_sleep'])
            min_sleep = masked.TextCtrl(self , -1, mins, mask = "####")
            max_sleep = masked.TextCtrl(self , -1, maxs, mask = "####")
            min_sleep.Bind(wx.EVT_TEXT, partial(self.OnChangeSleepValues, 'min_sleep'))
            max_sleep.Bind(wx.EVT_TEXT, partial(self.OnChangeSleepValues, 'max_sleep'))
            grid2.Add(min_sleep, 0, wx.RIGHT, 3)
            grid2.Add(max_sleep, 0, wx.LEFT, 3)
            items.append(grid2)

            sz1.AddMany (items)
            self.SetSizer(sz1)
            sz1.Fit(self)

        def OnChangeSleepValues(self, key, event):
            try:
                self.temp_userconfig[key] = int( event.EventObject.GetValue() )
            except:
                pass
            

        def OnGroupSelect( self, key, event ):
            self.temp_userconfig[key] = (event.EventObject.GetName() == key)


class OptionsGraphPanel(wx.ScrolledWindow):
        '''
        Create the panel to choose basic options about graphs
        '''
        def __init__(self,  parent,  user_config,  customuser_config):

            self.temp_userconfig = user_config
            self.temp_customuserconfig = customuser_config

            wx.ScrolledWindow.__init__(self,  parent)
            sz1 = wx.BoxSizer(wx.VERTICAL)

            desc = []
            desc.append ( wx.StaticText(self, -1, '\nDefault Figure size.') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            desc[-1].SetFont(titleFont)
            desc.append ( wx.StaticText(self, -1, 'Choose default size for all the figures.\nSize can be changed for every figure from their context menu.\n'))
            sz1.AddMany (desc)

            actual_size = self.temp_userconfig['FigureSize']
            inputsizer = wx.BoxSizer(wx.HORIZONTAL)
            self.fig_size_textctrl_x = NumCtrl (self, -1, size = (80,-1), value = actual_size[0], allowNegative = False, fractionWidth = 0, autoSize = False)
            self.fig_size_textctrl_y = NumCtrl (self, -1, size = (80,-1), value = actual_size[1], allowNegative = False, fractionWidth = 0, autoSize = False)
            self.fig_size_textctrl_x.Bind(wx.EVT_LEAVE_WINDOW, partial (self.OnUpdateSize, 'x'))
            self.fig_size_textctrl_y.Bind(wx.EVT_LEAVE_WINDOW, partial (self.OnUpdateSize, 'y'))
            self.fig_size_select_mu = wx.Choice(self, -1, choices = ['in', 'cm', 'mm', 'px'] )
            self.fig_size_select_mu.SetSelection(0)
            self.fig_size_select_mu.Bind(wx.EVT_CHOICE, self.OnChangeMeasureUnit)

            inputsizer.Add (self.fig_size_textctrl_x, 0, wx.ALL, 1)
            inputsizer.Add (self.fig_size_textctrl_y, 0, wx.ALL, 1)
            inputsizer.Add (self.fig_size_select_mu, 0, wx.ALL, 1)

            sz1.Add(inputsizer, 0, wx.ALL, 3)
            sz1.Add (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5  )

            #Define default dpi size when exporting to file
            desc = []
            desc.append (  wx.StaticText(self, -1, '\nDefault dpi of exported images.') )
            desc[-1].SetFont(titleFont)
            desc.append (  wx.StaticText(self, -1, 'You may export images as bitmap files (tif, rgb).\nSelect here the default resolution at export time\n') )

            def_dpi = str(self.temp_userconfig['dpi'])
            txt_dpi = masked.TextCtrl(self , -1, def_dpi, mask = "###", name='DPI')
            txt_dpi.Bind(wx.EVT_TEXT, partial(self.OnChangeDPI, 'dpi'))
            desc.append(txt_dpi)
            sz1.AddMany (desc)
            sz1.Add (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5  )


            # Group of radio controls:
            desc = []
            desc.append (  wx.StaticText(self, -1, '\nSelect the graphical interface.') )
            desc[-1].SetFont(titleFont)
            desc.append (  wx.StaticText(self, -1, 'The interactive interface is the default one.\nSelect the second one only in case the first one does not work.\nA restart is needed to see changes.\n') )

            grid1 = wx.FlexGridSizer( 0, 1, 0, 0 )
            self.canvas_type = []
            self.canvas_type.append( wx.RadioButton( self, -1, 'Interactive', name = 'wxmpl', style = wx.RB_GROUP ) )
            self.canvas_type.append( wx.RadioButton( self, -1, 'Not interactive', name = 'wx' ) )

            for radio in self.canvas_type:
                grid1.Add( radio, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
                radio.Bind(wx.EVT_RADIOBUTTON, self.OnCanvasSelect)
            ck = (self.temp_userconfig['Canvas'] == 'wx')*1
            self.canvas_type[ck].SetValue(True)

            desc.append (grid1)
            radio_sizer = wx.BoxSizer(wx.VERTICAL)
            radio_sizer.AddMany(desc)

            sz1.Add(radio_sizer, 0, wx.ALL, 3)

            self.SetSizer(sz1)
            sz1.Fit(self)

        def OnChangeDPI(self, key, event):
            value = event.EventObject.GetValue()
            try:
                self.temp_userconfig[key] = int(value)
            except:
                pass

        def OnChangeMeasureUnit(self, event):
            '''
            We update the value in the textbox when we change measure unit
            '''
            dpi = 96
            x = self.temp_userconfig['FigureSize'][0]
            y = self.temp_userconfig['FigureSize'][1]

            #conv_fact = (1, dpi*(1/2.54), dpi*(1/25.4), dpi)
            conv_fact = (1, 2.54, 25.4, dpi)   #in, cm, mm, px

            fra_width = (0, 2, 0, 2)
            mu = self.fig_size_select_mu.GetCurrentSelection()

            self.fig_size_textctrl_x.SetFractionWidth(fra_width[mu])
            self.fig_size_textctrl_y.SetFractionWidth(fra_width[mu])

            self.fig_size_textctrl_x.SetValue( x * conv_fact[mu])
            self.fig_size_textctrl_y.SetValue( y * conv_fact[mu] )

        def OnUpdateSize(self, ax, event):
            '''
            Size is always stored as inches but
            can be entered in different units (px, mm, cm)
            '''
            dpi = 96.0
            #conv_fact = (1, dpi*(1/2.54), dpi*(1/25.4), dpi)   #px, cm, mm, in
            conv_fact = (1, 1/2.54, 1/25.4, 1/dpi)   #in, cm, mm, px

            mu = self.fig_size_select_mu.GetCurrentSelection()

            if ax == 'x':
                size = (self.fig_size_textctrl_x.GetValue() * conv_fact[mu] , self.temp_userconfig['FigureSize'][1] )
            elif ax == 'y':
                size = (self.temp_userconfig['FigureSize'][0], self.fig_size_textctrl_y.GetValue() * conv_fact[mu] )

            self.temp_userconfig['FigureSize'] = size

        def OnCanvasSelect( self, event ):
            self.temp_userconfig['Canvas'] = event.EventObject.GetName()
            
class StyleGraphPanel(wx.ScrolledWindow):
        '''
        Creates the Panel for choosing the graphic style
        '''
        def __init__(self,  parent,  user_config,  customuser_config):

            self.temp_userconfig = user_config
            self.temp_customuserconfig = customuser_config

            wx.ScrolledWindow.__init__(self, parent)
            sz1 = wx.BoxSizer(wx.VERTICAL)

            items = []
            items.append ( wx.StaticText(self, -1, '\nUse crosshair.') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'Use a crosshair styled mouse cursor to navigate the graphs\nIt will work only in interactive mode. Restart of pySolo is required.'))
            #sz1.AddMany (items)

            grid1 = wx.FlexGridSizer( 0, 1, 0, 0 )
            self.DAM_version_radio = []
            self.DAM_version_radio.append( wx.RadioButton( self, -1, 'Use crosshair', name = 'crosshair', style = wx.RB_GROUP ) )
            self.DAM_version_radio.append( wx.RadioButton( self, -1, 'Do not use crosshair', name = 'no_crosshair' ) )

            for radio in self.DAM_version_radio:
                grid1.Add( radio, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
                radio.Bind(wx.EVT_RADIOBUTTON, partial(self.OnGroupSelect, 'crosshair'))
            ck = not self.temp_userconfig['crosshair']    
            self.DAM_version_radio[ck].SetValue(True)

            items.append (grid1)
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ) )

            items.append ( wx.StaticText(self, -1, '\nUse standard deviation or standard error.') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'Here you can choose whether to display standard error\nor deviation as error bar in graphs.\nNote that it will not work on all panels but only those that support this.\n'))
            #sz1.AddMany (items)

            grid2 = wx.FlexGridSizer( 0, 1, 0, 0 )
            self.error_kind_radio = []
            self.error_kind_radio.append( wx.RadioButton( self, -1, 'Use standard deviation', name = 'use_std', style = wx.RB_GROUP ) )
            self.error_kind_radio.append( wx.RadioButton( self, -1, 'Use standard error', name = 'use_stde' ) )

            for radio in self.error_kind_radio:
                grid2.Add( radio, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
                radio.Bind(wx.EVT_RADIOBUTTON, partial(self.OnGroupSelect, 'use_std'))
            ck = not self.temp_userconfig['use_std']    
            self.error_kind_radio[ck].SetValue(True)

            items.append (grid2)
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ) )

            sz1.AddMany (items)
            self.SetSizer(sz1)
            sz1.Fit(self)
            
        def OnGroupSelect( self, key,event ):
            self.temp_userconfig[key] = (event.EventObject.GetName() == key)
            



class OptionsColourPanel(wx.ScrolledWindow):
        '''
        Creates the Panel for choosing the plotting colors and their names
        '''
        def __init__(self,  parent,  user_config,  customuser_config):

            self.temp_userconfig = user_config
            self.temp_customuserconfig = customuser_config

            wx.ScrolledWindow.__init__(self, parent)
            sz1 = wx.BoxSizer(wx.VERTICAL)

            items = []

            items.append ( wx.StaticText(self, -1, '\nSelect the color sequence.') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'You can pick up to 20 different colors to be used to draw independent lines on the graph.\n Please specify a name for the color too.\n'))
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ) )

            sz1.AddMany (items)

            buttonSizer = wx.FlexGridSizer(5, 8) # sizer to contain all the example buttons
            self.colourBtns = []

            plotcol_dec = color_hex2dec(self.temp_userconfig['plotting_colors'])
            hm = len(plotcol_dec)

            label_l = self.temp_userconfig['plotting_colors_name']
            color_l = plotcol_dec
            size_l = [(80,-1)]*hm
            name_l = range(1,hm+1)

            buttonData = zip(name_l, color_l, size_l, label_l)

            # build each button and save a reference to it
            for name, color, size, label in buttonData:
                b = csel.ColourSelect(self, -1, label, color, size = size)
                b.Bind(csel.EVT_COLOURSELECT, self.OnSelectColour)
                self.colourBtns.append(b)

                buttonSizer.AddMany([
                    (wx.StaticText(self, -1, str(name)), 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
                    (b, 0, wx.ALL, 3),
                    ])

            sz1.Add(buttonSizer, 0, wx.ALL, 3)

            self.SetSizer(sz1)
            sz1.Fit(self)

        def OnSelectColour (self, event):
            '''
            After we have selected a colour we need to give it a name
            '''

            def dec2hex(color):
                red, green, blue = list(color)
                red = '%X' % red
                green = '%X' % green
                blue = '%X' % blue
                return '#' + str(red).zfill(2) + str(green).zfill(2) + str(blue).zfill(2)

            color_value = dec2hex(event.GetValue())
            color_name_dlg = wx.Dialog(self, wx.ID_ANY, 'Pick colour name', size=(200,160), style=wx.DEFAULT_DIALOG_STYLE )

            sizer = wx.BoxSizer(wx.VERTICAL)
            box = wx.BoxSizer(wx.HORIZONTAL)
            btnsizer = wx.BoxSizer(wx.HORIZONTAL)

            label = wx.StaticText(color_name_dlg, -1, 'Please, give a name to this colour')
            sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 2)

            label = wx.StaticText(color_name_dlg, -1, 'Name: ')
            box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 2)

            txtColorName = wx.TextCtrl(color_name_dlg, -1, color_value, size=(80,-1))
            box.Add(txtColorName, 1, wx.ALIGN_CENTRE|wx.ALL, 2)

            sizer.Add(box, 2, wx.GROW|wx.ALL, 2)

            line = wx.StaticLine(color_name_dlg, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
            sizer.Add(line, 0, wx.GROW|wx.RIGHT|wx.TOP, 1)

            btn = wx.Button(color_name_dlg, wx.ID_OK)
            btn.SetDefault()
            btnsizer.Add(btn, 0)

            btn = wx.Button(color_name_dlg, wx.ID_CANCEL)
            btnsizer.Add(btn, 0)

            sizer.Add(btnsizer, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

            color_name_dlg.SetSizer(sizer)

            # this does not return until the dialog is closed.
            val = color_name_dlg.ShowModal()

            if val == wx.ID_OK:            #identifies which button gave rise to the event
                n = 0
                for btn in self.colourBtns:
                    if btn.GetId() == event.GetId():
                        self.colourBtns[n].SetLabel(txtColorName.GetValue())
                        #The following three rows are added to correct a bug with this class
                        #New versions of ColourSelect should not need them anymore
                        bmp = self.colourBtns[n].MakeBitmap()
                        self.colourBtns[n].SetBitmap(bmp)
                        self.colourBtns[n].SetBitmapHover(bmp)

                        self.temp_userconfig['plotting_colors'][n] = color_value
                        self.temp_userconfig['plotting_colors_name'][n] = txtColorName.GetValue()
                    n += 1
            else:
                pass

            color_name_dlg.Destroy()

class OptionsInformationPanel(wx.ScrolledWindow):
        '''
        Creates a Panel showing some information about the system
        '''
        def __init__(self,  parent,  user_config,  customuser_config):

            self.temp_userconfig = user_config
            self.temp_customuserconfig = customuser_config

            wx.ScrolledWindow.__init__(self, parent)
            sz1 = wx.BoxSizer(wx.VERTICAL)

            items = []

            items.append ( wx.StaticText(self, -1, '\nInformation.') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'Here some information about your system.\n'))
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ) )

            from os import name as os_name
            from sys import version as sys_version
            from wxmpl import __version__ as wxmpl_version
            from matplotlib import __version__ as mpl_version
            from numpy import __version__ as numpy_version
            from scipy import __version__ as scipy_version

            information = 'OS type: %s\n' % (os_name)
            information += 'pySolo version: %s\n' % (pySoloVersion)
            information += 'Python version: %s\n' % (sys_version)
            information += 'wxPython version: %s\n' % (wx.__version__)
            information += 'wxmpl version: %s\n' % (wxmpl_version)
            information += 'matplotlib version: %s\n' % (mpl_version)
            information += 'numpy version: %s\n' % (numpy_version)
            information += 'scipy version: %s\n' % (scipy_version)
            items.append ( (wx.TextCtrl (self, -1, information, size=(200,150), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER), 0, wx.GROW | wx.EXPAND | wx.ALL, 10))

            from pysolo_lib import GUI
            items.append ( wx.StaticText(self, -1, '\nGUI variable (for debugging).') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'Here the content of the GUI variable.\n'))
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ) )
            
            infoGui = ''
            for key in GUI:
                infoGui += '%s:\t%s\n' % (key, GUI[key])
            items.append ( (wx.TextCtrl (self, -1, infoGui, size=(200,150), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER), 0, wx.GROW | wx.EXPAND | wx.ALL, 10))


            items.append ( wx.StaticText(self, -1, '\nuserConfig variable (for debugging).') )
            titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            items[-1].SetFont(titleFont)
            items.append ( wx.StaticText(self, -1, 'Here the content of the userConfig variable.\n'))
            items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ) )
            
            infoUC = ''
            for key in self.temp_userconfig:
                infoUC += '%s:\t%s\n' % (key, self.temp_userconfig[key])
            items.append ( (wx.TextCtrl (self, -1, infoUC, size=(200,150), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER), 0, wx.GROW | wx.EXPAND | wx.ALL, 10))

            
            sz1.AddMany (items)
            self.SetSizer(sz1)
            sz1.Fit(self)



class OptionsChoicePanel(wx.ScrolledWindow):

    def __init__(self,  parent,  user_config,  customuser_config):


        self.temp_userconfig = user_config
        self.temp_customuserconfig = customuser_config

        wx.ScrolledWindow.__init__(self,  parent)

        sz1 = wx.BoxSizer(wx.VERTICAL)

        titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
        items = []

        items.append ( wx.StaticText(self, -1, '\nSelect order and visibility of custom Panels.') )
        items[-1].SetFont(titleFont)
        items.append (  wx.StaticText(self, -1, 'Here is a list of installed custom panels.\nPlease select which ones you want to visualize and their relative order.\nRestart the program to make your changes effective.') )
        items.append ( (wx.StaticLine(self), 0, wx.EXPAND|wx.ALL, 5 ))


        self.chkListBox = wx.CheckListBox(self, -1, choices = [])
        self.UpdateCheckListBox()
        self.chkListBox.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckItemInListBox)

        items.append ( (self.chkListBox, 0, wx.ALL, 5) )

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnUp = wx.Button(self, -1, 'up')
        btnUp.Bind(wx.EVT_BUTTON, partial(self.MoveItemInList, -1))
        btnDown = wx.Button(self, -1, 'down')
        btnDown.Bind(wx.EVT_BUTTON, partial(self.MoveItemInList, +1))
        btnSizer.Add(btnUp, 0, wx.ALL, 1)
        btnSizer.Add(btnDown, 0, wx.ALL, 1)
        items.append (btnSizer)

        sz1.AddMany (items)
        self.SetSizer(sz1)
        sz1.Fit(self)

    def UpdateCheckListBox(self):
        '''
        Update content and order of check list box containing the list of panels
        '''
        customPanelList = [''] * len(self.temp_userconfig['Panels'])
        checkPanelList = [False] * len(self.temp_userconfig['Panels'])

        for aPanel in self.temp_userconfig['Panels']:
            position = self.temp_userconfig['Panels'][aPanel][0]
            customPanelList[position] = aPanel
            checkPanelList[position] = self.temp_userconfig['Panels'][aPanel][1]

        self.chkListBox.SetItems(customPanelList)

        n = 0
        for toCheck in checkPanelList:
            self.chkListBox.Check(n, toCheck)
            n+=1

    def OnCheckItemInListBox(self, event):
        '''
        When we check/uncheck item in the list box set panel flag visible / invisible
        '''
        index_c = event.GetSelection()
        items = self.chkListBox.GetItems()
        check_value = event.GetEventObject().IsChecked(index_c)

        self.temp_userconfig['Panels'][items[index_c]][1] = check_value

    def MoveItemInList(self, pos, event):
        '''
        Move items in the checklistbox up or down.
        '''
        index = self.chkListBox.GetSelection()
        items = self.chkListBox.GetItems()

        if  0 <= ( index + pos ) < len(items):
            selection = items[index]
            target = items[index+pos]

            self.temp_userconfig['Panels'][selection][0] = index+pos
            self.temp_userconfig['Panels'][target][0] = index

            self.UpdateCheckListBox()
            self.chkListBox.SetSelection(index+pos)


class pySolo_OptionPanel(wx.Frame):
    '''
    This class defines the Option Frame
    '''

    def __init__(
            self, parent, ID=-1, title='Option Panel', pos=wx.DefaultPosition,
        size=(640,480), style=wx.DEFAULT_FRAME_STYLE
            ):

        wx.Frame.__init__(self, parent, ID, title, pos, size, style)
        
        self.temp_userconfig = CopyDict(userConfig)
        self.temp_customuserconfig = CopyDict(customUserConfig)


        pp = wx.Panel(self, -1)
        self.optpane = wx.Treebook(pp, -1, style= wx.BK_DEFAULT)

        # These are the default panels laying in a tree-like fashion
        optList = [['Files and Folders'], ['Sleep options'],['Video options'], ['Graphs', 'Style', 'Colours'], ['Custom Panels Options'], ['Information']]

        # Here we add to position two of the list, under Custom Panels Option, every needed customPanel
        for panName in self.temp_customuserconfig:
            optList[3].append(panName)

        # Now make a bunch of panels for the list book
        for optCategory in optList:
            # The first item of the list is the main Panel
            tbPanel = self.makePanel(self.optpane, optCategory[0])
            self.optpane.AddPage(tbPanel, optCategory[0])

            for optName in optCategory[1:]:
                # All the following ones are children
                tbPanel = self.makePanel(self.optpane, optName)
                self.optpane.AddSubPage(tbPanel, optName)

        #self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGED, self.OnPageChanged)

        btSave = wx.Button(pp, wx.ID_SAVE)
        btCancel = wx.Button(pp, wx.ID_CANCEL)
        btSave.Bind(wx.EVT_BUTTON, self.OnSaveOptions)
        btCancel.Bind(wx.EVT_BUTTON, self.OnCancelOptions)
        self.Bind(wx.EVT_CLOSE, self.OnCancelOptions)


        btSz = wx.BoxSizer(wx.HORIZONTAL)
        btSz.Add (btCancel)
        btSz.Add (btSave)

        sz = wx.BoxSizer(wx.VERTICAL)
        sz.Add (self.optpane, 1, wx.EXPAND)
        sz.Add (btSz, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        pp.SetSizer(sz)

        # This is a workaround for a sizing bug on Mac...
        wx.FutureCall(100, self.AdjustSize)


        for i in range(0,len(self.optpane.Children)-1):
            self.optpane.ExpandNode(i)

    def CopyUserConfigVariables(self):
        '''
        Makes a local copy of userConfig and customUserConfig
        to be used as chached copy until we hit the Save button
        '''
#        self.temp_userconfig = dict()
#        self.temp_customuserconfig = dict()
        self.temp_userconfig = CopyDict(userConfig)
        self.temp_customuserconfig = CopyDict(customUserConfig)


    def AdjustSize(self):
        '''
        Apparently this is needed as workaround for a sizing bug on Mac.
        '''
        self.optpane.GetTreeCtrl().InvalidateBestSize()
        self.optpane.SendSizeEvent()

    def OnSaveOptions(self, event):
        '''
        Called when we hit the Save button
        Will copy the temporary stored variables to the real one and save it
        away to file
        '''

        customUserConfig = CopyDict(self.temp_customuserconfig)
        userConfig = CopyDict(self.temp_userconfig)
        try:
            SavePreferenceFile(userConfig, customUserConfig)
        except:
            wx.MessageBox('Error writing the preference file.\nThe file could be open by another process or the disk could be full.', 'oops!', style=wx.OK|wx.ICON_EXCLAMATION)

        self.Destroy()

    def OnCancelOptions(self, event):
        '''
        Called when we hit the Cancel button
        Will empty the temporary stored variables and exit
        '''
        self.temp_userconfig = dict()
        self.temp_customuserconfig = dict()
        self.Destroy()


    def makePanel(self, parent, PanelTitle, custom=False):
        '''
        This function is creating all the panels needed in the tree-book
        It can distinguish between default panels and panels that are
        linked to the installed plugins
        '''

        tp = wx.Panel(parent, -1,  style = wx.TAB_TRAVERSAL)

        if PanelTitle == 'Files and Folders':
            #self.MakeFilesFolderPanel(self.virtualw)
            self.virtualw = OptionsFilesFolderPanel(tp,  self.temp_userconfig,  self.temp_customuserconfig)

        elif PanelTitle == 'Sleep options':
            #self.MakeFilesFolderPanel(self.virtualw)
            self.virtualw = OptionsSleepPanel(tp,  self.temp_userconfig,  self.temp_customuserconfig)

        elif PanelTitle == 'Video options':
            #self.MakeFilesFolderPanel(self.virtualw)
            self.virtualw = OptionsVideoPanel(tp,  self.temp_userconfig,  self.temp_customuserconfig)
            
        elif PanelTitle == 'Graphs':
            #self.GraphoptionsPanel(self.virtualw)
            self.virtualw = OptionsGraphPanel(tp,  self.temp_userconfig,  self.temp_customuserconfig)

        elif PanelTitle == 'Style':
            self.virtualw = StyleGraphPanel(tp, self.temp_userconfig,  self.temp_customuserconfig)

        elif PanelTitle == 'Colours':
            #self.MakeColourPanel(self.virtualw)
            self.virtualw = OptionsColourPanel(tp,  self.temp_userconfig,  self.temp_customuserconfig)

        elif PanelTitle == 'Custom Panels Options':
            #self.MakeChoicePanels(self.virtualw)
            self.virtualw = OptionsChoicePanel(tp,  self.temp_userconfig,  self.temp_customuserconfig)

        elif PanelTitle == 'Information':
            #self.MakeInformationPanel(self.virtualw)
            self.virtualw = OptionsInformationPanel(tp,  self.temp_userconfig,  self.temp_customuserconfig)

        elif PanelTitle:
            self.virtualw = wx.ScrolledWindow(tp)
            self.MakeCustomPanel(self.virtualw, PanelTitle)

        #self.virtualw = wx.ScrolledWindow(tp)
        self.virtualw.SetScrollRate(20,20)
        TreeBookPanelSizer = wx.BoxSizer()
        TreeBookPanelSizer.Add(self.virtualw,  1, wx.GROW | wx.EXPAND, 0)

        #self.virtualw.FitInside()

        tp.SetSizer(TreeBookPanelSizer)
        return tp

#--- Here follow the non standard panels ---#

    def MakeCustomPanel(self, p, PanelTitle):
        '''
        Here we create a new panel for every plug-in that needs to have
        user defined options. There are four kind of available options

        radio
        text
        multiple choice
        boolean

        '''

        sz1 = wx.BoxSizer(wx.VERTICAL)

        titleFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
        items = []

        for option in self.temp_customuserconfig[PanelTitle]:
            option_type = self.temp_customuserconfig[PanelTitle][option][0]
            option_checked = self.temp_customuserconfig[PanelTitle][option][1]
            option_choices = self.temp_customuserconfig[PanelTitle][option][2]
            option_description = self.temp_customuserconfig[PanelTitle][option][3]

            items.append ( wx.StaticText(p, -1, '\nSet value of the variable: %s' % option))
            items[-1].SetFont(titleFont)
            items.append (  wx.StaticText(p, -1, option_description) )

            if option_type == 'radio' or option_type == 'boolean': #for boolean first choice is always True, second choice always False

                grid1 = wx.FlexGridSizer( 0, 1, 0, 0 )
                radio_list = []
                r = 0

                for radio in option_choices:
                    if r == 0:
                        radio_list.append( wx.RadioButton( p, -1, radio, name = str(r), style = wx.RB_GROUP) )
                    else:
                        radio_list.append( wx.RadioButton( p, -1, radio, name = str(r)) )

                    radio_list[-1].Bind(wx.EVT_RADIOBUTTON, partial(self.SaveRadioValue, self.temp_customuserconfig[PanelTitle][option]))

                    grid1.Add( radio_list[-1], 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )

                    if int(option_checked) == r :
                        radio_list[-1].SetValue(1)
                    else:
                        radio_list[-1].SetValue(0)
                    r += 1

                items.append (grid1)
                items.append ( (wx.StaticLine(p), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ))

            elif option_type == 'text': #for boolean first choice is always True, second choice always False

                items.append ( wx.TextCtrl (p,-1, value=option_choices[0]))
                items[-1].Bind (wx.EVT_LEAVE_WINDOW, partial (self.SaveTextValue, self.temp_customuserconfig[PanelTitle][option]) )
                items.append ( (wx.StaticLine(p), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ))

            elif option_type == 'multiple': #for boolean first choice is always True, second choice always False

                grid1 = wx.FlexGridSizer( 0, 1, 0, 0 )
                checkbox_list = []
                c = 0

                for checkbox in option_choices:

                    checkbox_list.append ( wx.CheckBox (p, -1, str(checkbox), name=str(c)) )
                    checkbox_list[-1].Bind(wx.EVT_CHECKBOX, partial(self.SaveCheckBoxValue, self.temp_customuserconfig[PanelTitle][option], c))

                    grid1.Add( checkbox_list[-1], 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )

                    if c in option_checked:
                        checkbox_list[-1].SetValue(1)
                    else:
                        checkbox_list[-1].SetValue(0)

                    c += 1

                items.append (grid1)
                items.append ( (wx.StaticLine(p), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5 ))


        sz1.AddMany (items)
        p.SetSizer(sz1)
        sz1.Fit(p)


    def SaveTextValue(self, uc, event):
        uc = event.EventObject.GetValue()

    def SaveRadioValue(self, uc, event):
        uc[1] = int(event.EventObject.GetName())

    def SaveCheckBoxValue(self, uc, c, event):
        ch = str(1*event.IsChecked())
        uc[1] = uc[1][:c] + ch + uc[1][c+1:]

#------------------------------------------------------#





class MyApp(wx.App):
    def OnInit(self):
        self.options_frame =  pySolo_OptionPanel(None)
        self.options_frame.Show(True)
        return True


if __name__ == '__main__':


    # Run program
    app=MyApp()
    app.MainLoop()
