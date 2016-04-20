#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       pysolo_anal.py
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
#
#        self.sp = MultiSplitterWindow
#           self.TreePanel
#           self.Notebook
#               self.Pages
#           self.sbPanel
#               self.OptSB
#               self.ExportSB


import wx, os, glob
from pysolo_path import panelPath, imgPath
os.sys.path.append(panelPath)

from pysolo_lib import pySoloVersion, GUI, userConfig, customUserConfig
from default_panels import *

#some specific wx libraries used in this frame
import wx.lib.filebrowsebutton as filebrowse
from wx.lib.splitter import MultiSplitterWindow
import wx.lib.scrolledpanel as scrolled
from wx.lib.buttons import GenBitmapToggleButton
import wx.lib.agw.customtreectrl as CT

import wx.lib.newevent
myEVT_OPTION_CHANGED, EVT_OPTION_CHANGED = wx.lib.newevent.NewEvent()


class ExportVariableSideBar(wx.Panel):
    """
    Custom Panel for the Export Variable sidebar
    """
    
    def __init__(self, parent):
        """
        create the actual panel
        """
        
        self.outputPath = userConfig['DAMoutput']
        self.defaultvarList = ['Selected Activity', 'Selected Sleep 5min', 'Selected Sleep 30min']
        self.varList = self.defaultvarList + []
        self.defaultDescription = ['Exports the matrix containing the activity (raw) data for the current selection. This is not Panel specific',
                                   'Exports the matrix containing the raw sleep data (sleep for 5mins) for the current selection. This is not Panel specific',
                                   'Exports the matrix containing the compiled sleep data (sleep for 30mins) for the current selection. This is not Panel specific']
        
        self.filename = 'filename'

        wx.Panel.__init__(self, parent, -1)
        sz_a = wx.BoxSizer(wx.VERTICAL)
        sz_a.Add ( wx.StaticText(self, wx.ID_ANY, 'Export Panel specific variables'), 0,wx.ALL, 5 )
        
        self.varListBox = wx.ListBox(self, wx.ID_ANY, (0,0), (80,150), self.defaultvarList)
        self.varListBox.Bind(wx.EVT_LISTBOX, self.pickVariable)
        sz_a.Add(self.varListBox, 0, wx.ALL | wx.GROW | wx.EXPAND, 5)

        #self.outputFolder = filebrowse.DirBrowseBUTTON(self, wx.ID_ANY, size=(-1, -1), startDirectory=userConfig['DAMoutput'],  labelText='',  BUTTONText = '[..]')
        self.filenameBox = wx.TextCtrl (self, wx.ID_ANY, 'Filename', size=(-1, -1))
        sz_a.Add(self.filenameBox, 0, wx.LEFT | wx.RIGHT | wx.GROW, 5)

        sz_b = wx.BoxSizer(wx.HORIZONTAL)
        self.outputFolder = wx.TextCtrl (self, wx.ID_ANY, '', size=(-1, -1))
        self.outputFolder.SetValue(self.outputPath)
        sz_b.Add(self.outputFolder, 6, wx.ALL | wx.GROW | wx.EXPAND, 5)

        imageBrowse = wx.Image(imgPath+'/t_search.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()        
        self.browseFolder = wx.BitmapButton(self, wx.ID_ANY, bitmap=imageBrowse, size = (imageBrowse.GetWidth()+2, imageBrowse.GetHeight()+2))
        self.browseFolder.SetToolTipString('Browse to change current outputFolder')
        self.browseFolder.Bind(wx.EVT_BUTTON, self.onBrowse)       
        sz_b.Add(self.browseFolder,1)
        
        sz_a.Add(sz_b)#, 1, wx.GROW | wx.EXPAND, 0)
        
        grid1 = wx.FlexGridSizer( 0, 1, 0, 0 )
        self.out_format = []
        self.out_format.append( wx.RadioButton( self, wx.ID_ANY, 'Binary format', name = 'binary', style = wx.RB_GROUP ) )
        self.out_format.append( wx.RadioButton( self, wx.ID_ANY, 'Text format (CSV)', name = 'text' ) )

        for radio in self.out_format:
            grid1.Add( radio, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
            #radio.Bind(wx.EVT_RadioButton, self.onFormatSelect)
        self.out_format[1].SetValue(True)
        sz_a.Add(grid1)
        
        self.description = wx.TextCtrl ( self, wx.ID_ANY, 'Description\nPick the variable you want to export then hit the export BUTTON. The variable is updated every time you select new flies from the browsing tree.', size=(-1, 100), style=wx.TE_MULTILINE | wx.TE_READONLY )
        sz_a.Add(self.description,0, wx.ALL | wx.GROW | wx.EXPAND, 5)
        
        imageExport = wx.Image(imgPath+'/t_checkall.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.ExportBTN = wx.BitmapButton(self, wx.ID_ANY, bitmap=imageExport, size = (imageExport.GetWidth()+2, imageExport.GetHeight()+2))
        self.ExportBTN.SetToolTipString('Export selected variables to file')
        self.ExportBTN.Bind(wx.EVT_BUTTON, self.onExport)
        
        sz_a.Add(self.ExportBTN,0, wx.ALL, 5)
        self.SetSizer(sz_a)

    def pickVariable(self, event):
        """
        Called when we pick a variable from the list
        """
        for n in self.varListBox.GetSelections():
            picked = self.varList[n]
            if picked not in self.defaultvarList:
                exp_var = GUI['canExport'][picked]
                description = exp_var.description
            else:
                description = self.defaultDescription[n]

            self.varname = picked
            self.description.SetValue(description)
            format, extension = self.getOutputParams()
            self.filename = self.getFilename(self.varname, extension)
            self.filenameBox.SetValue(self.filename)

    def getFilename(self, var_name, extension):
        """
        Returns a filename that is proper for the currently selected variable
        """
        
        n = 1
        fname = str(var_name).lower().replace(' ','_') + '_%02d' % n
        full_path = os.path.join(self.outputPath, fname)
        while os.path.isfile(full_path+extension):
            n+=1
            fname = fname[:-2] + '%02d' % n
            full_path = os.path.join(self.outputPath, fname)
            
        return fname

    def updateVariableList(self, currentPage):
        """
        update the list of variables in the listbox
        """
        varList = []
        for var in GUI['canExport']:
            if GUI['canExport'][var].panel == currentPage: varList.append(var)
        self.varList = self.defaultvarList + varList
        self.varListBox.Set(self.varList)
    
    def getOutputParams(self):
        """
        return the file extension based on the format chosen
        """
        if self.out_format[0].GetValue():
            format = 'binary'
            extension = '.bin'
        if self.out_format[1].GetValue():
            format = 'text'
            extension = '.csv'
        
        return format, extension

    def onExport(self, event):
        """
        Export Variables to file
        """

        format, extension = self.getOutputParams()
        fname = self.getFilename(self.varname, extension) + extension
        full_path = os.path.join(self.outputPath, fname)
        
        if self.varname in self.defaultvarList:
            success = self.ExportDefaultVariable(full_path, self.varname, format)
        else:
            success = GUI['canExport'][self.varname].exportToFile(full_path, format)

        if not success:
            wx.MessageBox('Error saving the file %s\nDisk may be full or you may not have write rights.' % full_path, 'Error!', style=wx.OK|wx.ICON_EXCLAMATION)

    def ExportDefaultVariable(self, fpath, var_name, export_format):
        """
        Export
        activity of selected flies or
        sleep5min of selected flies or
        sleep30min of selected flies

        fpath = the full path of the output file
        var_name = 'Selected Activity' || 'Selected Sleep 5min' || 'Selected Sleep 30min']
        export_format = 'binary', 'text'

        """
        allSelections = GUI['dtList']
        cDAM = GUI['cDAM']
        t0,t1 = None, None #do we want to customize these?
        use_dropout = userConfig['use_dropout'] #boolean
        min_alive = userConfig['min_sleep'] #int
        max_alive = userConfig['max_sleep'] #int
        v = [0,0,0]

        
        for n_sel, selection in enumerate(allSelections): #every selection carries a 5 digits coordinate

            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]
            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)
            # take the 3D arrays for
            # ax -> fly activity (the raw data of beam crossing)
            # s5 -> the 5mins sleep bins
            # s30 -> the sleep for 30 mins across the day
            ax_t, s5_t, s30_t = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1, status=5, use_dropout=use_dropout, min_alive=min_alive, max_alive=max_alive)  #get the S5 of the currently selected item

            if n_sel == 0:
                v[0] = ax_t
                v[1] = s5_t
                v[2] = s30_t
            else:
                v[0] = concatenate ((v[1], ax_t))
                v[1] = concatenate ((v[0], s5_t))
                v[2] = concatenate ((v[2], s30_t))
        
        #Export now
        i = ['Selected Activity', 'Selected Sleep 5min', 'Selected Sleep 30min'].index(var_name)
        f = ['binary', 'text'].index(export_format)
        separator = ['','\t'][f] #empty separator means binary, otherwise a tab will be used for text files

        unmasked_v = np.array(v[i]) #we need to unmask the array as tofile of masked arrays is not implemented yet
        unmasked_v.tofile(fpath, separator)
        return True
        
    def onBrowse(self, event):
        """
        Browse to select the output folder
        """
        dlg = wx.DirDialog(self, "Choose a directory:",
                          style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )
        if dlg.ShowModal() == wx.ID_OK: 
            self.outputPath = dlg.GetPath()
            self.outputFolder.SetValue(self.outputPath)
            
        dlg.Destroy()


class OptionSideBar(wx.Panel):
    """
    Custom Panel for the options sidebar
    """
    
    def __init__(self, parent):
        """
        create the actual panel
        """
        
        self.parent = parent
        wx.Panel.__init__(self, parent, -1)
        
        self.varType = ''
      
        OptSideBarSizer = wx.BoxSizer(wx.VERTICAL)
        OptSideBarSizer.Add ( wx.StaticText(self, wx.ID_ANY, 'Tweak Panel specific Options.'), 0,wx.ALL, 5 )

        self.OptionsTree = CT.CustomTreeCtrl(self, style= wx.TR_MULTIPLE | wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_DEFAULT_STYLE )
        self.OptionsTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelChanged)

        self.OptionsInput = wx.ComboBox ( self, -1, value='Select', pos=(-1,-1), size=(-1,-1), choices=[], style=wx.CB_DROPDOWN )
        self.OptionsInput.Bind(wx.EVT_COMBOBOX, self.onChangeInput)
        self.OptionsInput.Bind(wx.EVT_TEXT, self.onChangeInput)
        self.OptionsInfo = wx.TextCtrl ( self, -1,'', size=(-1, -1), style=wx.TE_MULTILINE | wx.TE_READONLY )
        
        OptSideBarSizer.Add(self.OptionsTree, 5, wx.EXPAND | wx.ALL, 1 )
        OptSideBarSizer.Add(self.OptionsInput, 0, wx.EXPAND | wx.ALL, 1 )
        OptSideBarSizer.Add(self.OptionsInfo, 1, wx.EXPAND | wx.ALL, 1 )
        self.SetSizer(OptSideBarSizer)

    def onSelChanged(self, event):
        """
        Called whenever the selection in the dropbox changes
        """
        if self.OptionsTree.GetSelections():
            self.lastSel = self.OptionsTree.GetSelections()[0]
        
        sel = self.lastSel
        descMsg = ''
        vv = sel.GetText()
        
        if ': ' in vv:
            self.SelVar = vv.split(': ')[0]
        else:
            self.SelVar = vv
        
        if sel.HasChildren():
            self.SelPan = self.SelVar
            msg = 'Panel: %s' % self.SelPan
            self.SelVarType = 'panel'
        else:
            self.SelPan = sel.GetParent().GetText().split(': ')[0]
            self.SelVarType = customUserConfig[self.SelPan][self.SelVar][0] #boolean | radio | text | multiple
            checked = customUserConfig[self.SelPan][self.SelVar][1]
            choices = customUserConfig[self.SelPan][self.SelVar][2]
            desc = customUserConfig[self.SelPan][self.SelVar][3]    


            descMsg = 'Panel: %s\nVar name: %s\n\n%s' % (self.SelPan, self.SelVarType,  desc)

            self.SetItemsList(checked, choices)

            if type(checked) == list and checked != []: checked = 0
            if checked == []: checked = len(choices)
            self.OptionsInput.SetSelection(0)

        self.OptionsInfo.SetValue(descMsg)

        #create and post the event
        #TOFIX: this event does not propagate upstream
        #It's needed to refresh drawing when variables are changed
        wx.PostEvent(self.parent, myEVT_OPTION_CHANGED())

    def SetItemsList(self, checked, choices):
        """
        Set the list of selectable items in the dropbox so that the ones
        selected will appear marked with an asterisk.
        """
        
        if len(choices) != 1:
            new_choices = ['Select'] + [str(i) for i in choices]
            if type(checked) != list:
                c = int(checked) + 1
                new_choices[c] = '%s (*)' % new_choices[c]
            else:
                for c in checked: 
                    c = int(c) + 1
                    new_choices[c] = '%s (*)' % new_choices[c]
        else:
            new_choices = [str(c) for c in choices]
        
        new_choices = [str(c) for c in new_choices]
        self.OptionsInput.SetItems(new_choices)


    def onChangeInput(self, event):
        """
        When we change the value of the var in the combobox
        """
        vv = ''

        if self.SelVarType == 'text':
            vv = self.OptionsInput.GetValue()
            customUserConfig[self.SelPan][self.SelVar][2] = [vv]
        else:
            sel = self.OptionsInput.GetSelection() - 1#int number

        if self.SelVarType in ['boolean', 'radio'] and sel>=0:
            customUserConfig[self.SelPan][self.SelVar][1] = sel
            vv = customUserConfig[self.SelPan][self.SelVar][2][sel]

        elif self.SelVarType == 'multiple' and sel >= 0:
            if sel in customUserConfig[self.SelPan][self.SelVar][1]:
                customUserConfig[self.SelPan][self.SelVar][1].remove(sel)
            else:
                customUserConfig[self.SelPan][self.SelVar][1].append(sel)
                
            customUserConfig[self.SelPan][self.SelVar][1].sort()
            vv = customUserConfig[self.SelPan][self.SelVar][1]
        
            
        self.onSelChanged(None)

        if vv:
            lbl = '%s: %s' % (self.SelVar, vv)
            SelItem = self.lastSel
            self.OptionsTree.SetItemText(SelItem, lbl)

    def PopulateOptionsTree(self):
        """
        Populate the options tree in the right hand side
        Every panel is a parental node
        """
        """
        option_panel = the name of the panel
        option_name = the name of the variable for the option_panel
        option_type = boolean | radio | text | multiple
        option_checked = the int number indicating the position of the chosen value in option_choices. Must be 0 if option_type = text
        option_choices = a list containing the possible choices
        option_description = the description of the option
        """

        self.OptionsTree.DeleteAllItems()
        itemData = (-1,)
        rootId = self.OptionsTree.AddRoot('Panels', data=wx.TreeItemData(itemData))
        LVL1 = []
        
        for option_panel in customUserConfig:
            LVL1.append ( self.OptionsTree.AppendItem(rootId, option_panel) )
            for option_name in customUserConfig[option_panel]:
                [option_type, option_checked, option_choices, option_description] = customUserConfig[option_panel][option_name]
                option_value = customUserConfig[option_panel].GetOptionValue(option_name)
                self.OptionsTree.AppendItem(LVL1[-1], '%s: %s' % (option_name, option_value))

class NavigationTree(CT.CustomTreeCtrl):
    """
    Custom Class defining the navigation tree
    The CustomTreeCtrl is way faster than the regular treectrl
    """

    def __init__(self, parent):

        CT.CustomTreeCtrl.__init__(self, parent, agwStyle= wx.TR_MULTIPLE |
                                                 wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_DEFAULT_STYLE )
        self.parent = parent
        self.KeyDown = ''
        self.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.onKeyDown)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelChanged)
        #self.Bind(wx.EVT_TREE_KEY_UP, self.onKeyUp)

        global GUI
        GUI['JoinTreeItems'] = False
        GUI['TreeCollapsed'] = True
        GUI['inputbox'] = ''
        GUI['currentlyDrawn'] = 0
        GUI['holdplot'] = False

    def onKeyDown(self,event):
        """
        Detects a key down event and take corresponding action
        """
        keycode =  event.GetKeyCode()
        if keycode < 256:
             self.KeyDown = chr(keycode)
             if self.KeyDown == 'A': self.DoChangeStatus(5) #active
             if self.KeyDown == 'I': self.DoChangeStatus(-5) #inactive
             if self.KeyDown == 'B': self.DoChangeStatus(1) # baseline
             if self.KeyDown == 'S': self.DoChangeStatus(2) # SD
             if self.KeyDown == 'R': self.DoChangeStatus(3) # recovery
             if self.KeyDown == 'N': self.DoChangeStatus(4) # none of above

        event.Skip()

    def onKeyUp(self, event):
        """
        Restore the pressed key record
        """
        self.KeyDown = ''
        event.Skip()

    def onSelChanged(self, event):
        """
        Before passing the click checks if there is an action to be performed
        due to a key pressed by the user
        """

        if self.KeyDown == 'H': pass

        self.KeyDown = ''
        event.Skip()


    def onContextMenu(self, event):
        """
        Creates and handles a popup menu
        """
        if not hasattr(self, 'popupID1'):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()
            self.popupID6 = wx.NewId()
            self.popupID7 = wx.NewId()
            self.popupID8 = wx.NewId()
            self.popupID9 = wx.NewId()


            self.Bind(wx.EVT_MENU, partial (self.DoChangeStatus, 1), id=self.popupID1)
            self.Bind(wx.EVT_MENU, partial (self.DoChangeStatus, 2), id=self.popupID2)
            self.Bind(wx.EVT_MENU, partial (self.DoChangeStatus, 3), id=self.popupID3)
            self.Bind(wx.EVT_MENU, partial (self.DoChangeStatus, 4), id=self.popupID4)

            self.Bind(wx.EVT_MENU, partial (self.DoChangeStatus, 5), id=self.popupID5)
            self.Bind(wx.EVT_MENU, partial (self.DoChangeStatus, -5), id=self.popupID6)
            self.Bind(wx.EVT_MENU, partial (self.DoChangeStatus, 0), id=self.popupID7)
            self.Bind(wx.EVT_MENU, partial (self.onExpandCollapseTree, 0), id=self.popupID8)
            self.Bind(wx.EVT_MENU, partial (self.onExpandCollapseTree, 1), id=self.popupID9)

        # make a menu
        menu = wx.Menu()
        menu.Append(self.popupID1, 'Mark As Baseline')
        menu.Append(self.popupID2, 'Mark As SD')
        menu.Append(self.popupID3, 'Mark As Recovery')
        menu.Append(self.popupID4, 'Mark As None')
        menu.AppendSeparator()
        menu.Append(self.popupID5, 'Mark As Active')
        menu.Append(self.popupID6, 'Mark As Inactive')
        menu.Append(self.popupID7, 'Toggle Status')
        menu.AppendSeparator()
        menu.Append(self.popupID8, 'Expand All')
        menu.Append(self.popupID9, 'Collapse All')

        self.PopupMenu(menu)
        menu.Destroy()

    def DoChangeStatus(self, status, event=None):
        """
        Changes the Status of the object associated to the selected tree item(s)
        """
        allSelections = []
        color = ('gray', 'black')
        day_type = ('BS', 'SD', 'RC', '  ')
        d, d1 = 0, -1
        f, f1 = 0, -1

        Active = (status>0)

        for SelItem in self.GetSelections():
            allSelections.append (self.GetItemPyData(SelItem).GetData())
            self.SetItemTextColour(SelItem, color[Active])

            if abs(status)!=5 and allSelections[-1][0] != 3: #if it is not a day but we are trying to modify day_status
                wx.MessageBox('only a Day can be marked in this way!', 'Error!', style=wx.OK|wx.ICon_EXCLAMATIon)
                return False

            elif abs(status)!=5 and allSelections[-1][0] == 3:
                label = self.GetItemText(SelItem)[:-2] + day_type[abs(status)-1]
                self.SetItemText(SelItem, label)

            if self.ItemHasChildren(SelItem):
                self.EnableChildren(SelItem, Active)
                #self.GetFirstChild(SelItem).SetItemTextColour(SelItem, color[status])

        for selection in allSelections:
            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]
            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)
            cSEL.setFlyStatus(ds,de,fs,fe,status)

        SetFileAsModified(self.parent)


    def onExpandCollapseTree(self, event=None, n=None):
            """
            Expand or Collapse all first nodes of the tree
            n = 0 -> expand
            n = 1 -> collapse
            """
            
            if n == None: n = not GUI['TreeCollapsed'] * 1
            action = [self.Expand, self.Collapse][n]

            root = self.GetRootItem()
            children = root.GetChildren()
            for child in children:
                action(child)
            GUI['TreeCollapsed'] = [False, True][n]

    def PopulateNavigationTree(self):
        """
        Goes through the DAM variable and populates the tree
        Every item in the tree is going to be associated to a data bearing the coordinates to identify that item
        and make the proper analysis on the notebook panel
        """

        # type    G, M, D, F
        #dt  0    1, 2, 3, 4
        #    0    G,-1,-1,-1            AVG(all flies, all mon) day by day
        #    1    G, M,-1,-1            AVG(all flies, per mon m) day by day
        #    2    G, M, D,-1            AVG(all flies, per mon m, per day d)
        #    3    G,-1, D,-1            AVG(all flies, per day d) mon per mon
        #    4    G, M, D, F            single fly per mon m, per day d
        #    5    G, M,-1, F            single fly per mon m, day by day

        self.DeleteAllItems()
        itemData = (-1,)
        rootId = self.AddRoot('DAMS', data=wx.TreeItemData(itemData))
        LVL1,LVL2,LVL3,LVL4,LVL5 = [],[],[],[],[]

        for k in range (len(LVL1),len(cDAM)):
            cSEL = cDAM[k]
            itemData = (0,k,-1,-1,-1) #type 0, entire genotype, ex: CS
            label = '%s' % cSEL.Genotype
            LVL1.append (self.AppendItem(rootId, str(cSEL.Genotype), data=wx.TreeItemData(itemData)))

        # appending Mon then DAYS, then FLIES
            for m in range (0, len(cSEL.Mon)): #add Mon
                itemData = (1,k,m,-1,-1) #type 1, whole monitor ,ex: M01 (1-32)
                mon = cSEL.getMonitorName(m)
                f, f1 = cSEL.getFliesInMon(mon)
                label = 'M%s (%s-%s)' % (mon.zfill(2), cSEL.getRangePerMon(m)[0], cSEL.getRangePerMon(m)[-1])
                LVL2.append (self.AppendItem(LVL1[-1], label, data=wx.TreeItemData(itemData)))
                if cSEL.allinStatus(mon=m): self.SetItemTextColour(LVL2[-1], 'gray')

                #appending FLIES (in a small folder) then DAYS
                itemData = (1,k,m,-1,-1) #type 1, whole monitor, ex: Channels 1-32
                label = 'Channels %s - %s' % (str(cSEL.getRangePerMon(m)[0]), str(cSEL.getRangePerMon(m)[-1]))
                LVL3.append (self.AppendItem(LVL2[-1], label, data=wx.TreeItemData(itemData)))
                if cSEL.allinStatus(mon=m): self.SetItemTextColour(LVL3[-1], 'gray')

                for f in range(0, cSEL.rangeChannel[1].count(cSEL.Mon[m])):  #add FLIES
                    itemData = (5,k,m,-1,f) #type 5, one fly per one monitor per all days, ex: 1
                    label = '%s' % cSEL.getRangePerMon(m)[f]
                    LVL4.append (self.AppendItem(LVL3[-1], label, data=wx.TreeItemData(itemData)))
                    if cSEL.allinStatus(mon=m, fly=f): self.SetItemTextColour(LVL4[-1], 'gray')

                    for d in range(cSEL.getTotalDays()):    #add DAYS
                        itemData = (4,k,m,d,f) #type 4, one fly per one monitor per one day, ex: 01/04
                        label = cSEL.getDate(d, format = 'mm/dd')#
                        LVL5.append (self.AppendItem(LVL4[-1], label, data=wx.TreeItemData(itemData)))
                        if cSEL.allinStatus(mon=m, day=d, fly=f): self.SetItemTextColour(LVL5[-1], 'gray')

                for d in range(cSEL.getTotalDays()):    #add DAYS
                    itemData = (2,k,m,d,-1) #type 2, one day per one monitor, ex: 01/04
                    label = cSEL.getDate(d, format = 'mm/dd')#
                    LVL3.append (self.AppendItem(LVL2[-1], label, data=wx.TreeItemData(itemData)))
                    if cSEL.allinStatus(mon=m, day=d): self.SetItemTextColour(LVL3[-1], 'gray')

                    for f in range(0, cSEL.rangeChannel[1].count(cSEL.Mon[m])): #add FLIES
                        itemData = (4,k,m,d,f) #type 4, one fly per one day per one mon, ex: 1
                        label = '%s' % cSEL.getRangePerMon(m)[f]
                        LVL4.append (self.AppendItem(LVL3[-1], label, data=wx.TreeItemData(itemData)))
                        if cSEL.allinStatus(mon=m, day=d, fly=f): self.SetItemTextColour(LVL4[-1], 'gray')


        # appending DAYS then Mon, then FLIES
            for d in range(cSEL.getTotalDays()): #Add Days
                itemData = (3,k,-1,d,-1) #type 3, All monitors per one day, ex: 01/04
                label = cSEL.getDate(d, format = 'mm/dd') + '   '
                LVL2.append (self.AppendItem(LVL1[-1], label, data=wx.TreeItemData(itemData)))
                if cSEL.allinStatus(day=d): self.SetItemTextColour(LVL2[-1], 'gray')
                if cSEL.allinStatus(day=d, status=1): self.SetItemText(LVL2[-1], label[:-2]+'BS')
                if cSEL.allinStatus(day=d, status=2): self.SetItemText(LVL2[-1], label[:-2]+'SD')
                if cSEL.allinStatus(day=d, status=3): self.SetItemText(LVL2[-1], label[:-2]+'RC')
                if cSEL.allinStatus(day=d, status=4): self.SetItemText(LVL2[-1], label[:-2]+'  ')


                for m in range (0, len(cSEL.Mon)): #add Mon
                    itemData = (2,k,m,d,-1) #type 2, one monitor per one day, ex: M01 (1-32)
                    label = 'M%s (%s-%s)' % ( str(cSEL.Mon[m]).zfill(2), cSEL.getRangePerMon(m)[0], cSEL.getRangePerMon(m)[-1] )
                    LVL3.append (self.AppendItem(LVL2[-1], label, data=wx.TreeItemData(itemData)))
                    if cSEL.allinStatus(mon=m, day=d): self.SetItemTextColour(LVL3[-1], 'gray')

                    for f in range(0, cSEL.rangeChannel[1].count(cSEL.Mon[m])): #add FLIES
                        itemData = (4,k,m,d,f) #type 4, one fly per one monitor per one day, ex: 1
                        label = '%s' % cSEL.getRangePerMon(m)[f]
                        LVL4.append (self.AppendItem(LVL3[-1], label, data=wx.TreeItemData(itemData)))
                        if cSEL.allinStatus(mon=m, day=d, fly=f): self.SetItemTextColour(LVL4[-1], 'gray')



#---------------------- MAIN FRAME STARTS HERE -----------------------------#

class pySolo_AnalysisFrame(wx.Frame):
    """
    This is the main frame, containing everything
    """
    def __init__(self, parent, id, title, siblingMode = False):
        global GUI, userConfig

        wx.Frame.__init__(self, parent, id, title, size=(1024,768))

        self.title = 'Pysolo v%s - Analysis' % pySoloVersion
        self.fileisModified = False
        GUI['ErrorBar'] = False
        GUI['currentData'] = []
        GUI['filename'] = ''
        GUI['dirname'] = ''
        GUI['canExport'] = dict([])
        GUI['currentPage'] = ''

        #Support for opening file on Drag and Drop
        allowedExtensions = dict()
        allowedExtensions['dad'] = self.onFileOpen
        allowedExtensions['pvf'] = self.openSingleVideoFile
        self.DropArea = FileDrop(self, allowedExtensions)
        #self.DropArea = FileDrop(self, dad = self.onFileOpen, pvf = self.openSingleVideoFile)
        
        
        self.SetDropTarget(self.DropArea)

        #GUI['dtList'] = []

        self.SiblingMode = siblingMode
        self.minpane, self.initpos = 100, 200

        #self.mainPanel = wx.Panel(self, -1)
        self.sp = MultiSplitterWindow(self)#, style=wx.SP_LIVE_UPDATE) #wx.SplitterWindow(self, -1, style = wx.SP_BORDER)

        self.MakeMenuBar()
        self.MakeTheTree() #creates self.TreePanel and contents

        self.MakeTheNotebook() #creates self.nb
        self.sidebar = self.MakeTheSideBar() #creates the sidebar on the right side


        self.sp.AppendWindow(self.TreePanel, self.initpos)
        self.sp.AppendWindow(self.nb) # contains all the panels as pages
        self.sp.AppendWindow(self.sidebar) # contains optsb and exportsb
        
        self.OptSB.Show(False)

        #self.sp.SplitVertically(self.TreePanel, self.nb, self.initpos)
        self.sp.SetMinimumPaneSize(self.minpane)

        #custom events are defined in pysolo_lib
        self.Bind(EVT_FILE_MODIFIED, self.SetfileisModified)
        self.Bind(EVT_OPTIONSB_SHOW_HIDE, self.onShowOptionsSideBar)
        self.Bind(EVT_OPTION_CHANGED, self.Refresh)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_SIZE, self.onResize)

        if len(sys.argv)>1:
            self.AnalyseArgs()

        #Preference file was not found. We set some default value then we ask the user to review them.
        if not PreferenceFileFound:
            self.onShowOptions(None)

        #automatically check for updates on the website
        if userConfig['checkUpdate']:
            self.onCheckVersion()

    def __SetBrother__(self, brotherFrame):
        self.BrotherFrame = brotherFrame
        self.SiblingMode = True

    def AnalyseArgs(self):
        """
        Check the args coming from the command line and interprete them as due
        """
        args = sys.argv
        if args.count('-c'):
            p = args.index('-c') + 1
            option_file = args[p]
            LoadPreferenceFile(option_file)

        if args.count('-o'):
            p = args.index('-o') + 1
            #GUI['filename'] = args[p]
            self.onFileOpen(filename = args[p])
            


    def MakeTheNotebook(self):
        """
        Here we create a notebook and its pages
        """

        self.nb = wx.Notebook(self.sp)
        self.GetPanels()
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.Refresh, self.nb)

    def GetPanels(self):
        """
        This function will load all the panels found in the panel directory
        """
        
        self.Pages = []
        
        PanelList = glob.glob(os.path.join(panelPath, '*.py') )
        num_of_Panels = len(PanelList) - 1 #count how many we have and subtract 1 to remove default_panels.py

        if ('Panels' in userConfig) and userConfig['Panels'] and ( num_of_Panels == len(userConfig['Panels']) ):

            # First fill the list ordered_Panels only with the Panels that we want to show
            # in the ordered we decided to give

            ordered_Panels = ['']*num_of_Panels
            for cPanel in userConfig['Panels']:
                position = userConfig['Panels'][cPanel][0]
                if userConfig['Panels'][cPanel][1]:
                    ordered_Panels[position] = cPanel

            #then go through the list and load the panels
            for cPanel in ordered_Panels:
                if cPanel != '':
                    NewPanel = __import__(cPanel)
                    self.Pages.append (NewPanel.Panel(self.nb))
                    if self.Pages[-1].isCompatible():
                        self.nb.AddPage(self.Pages[-1], self.Pages[-1].name)
 
        else:
            # if we have no preference variable yet or if we are adding a new panel, fill
            # the variable. New panels are added as visible as default

            for f in PanelList:
                _,f = os.path.split(f)
                module_name, ext = os.path.splitext(f) # Handles no-extension files, etc.
                if ext == '.py' and module_name != 'default_panels': # Important, ignore .pyc/other files.
                    NewPanel = __import__(module_name)
                    self.Pages.append (NewPanel.Panel(self.nb))
                    if self.Pages[-1].isCompatible():
                        self.nb.AddPage(self.Pages[-1], self.Pages[-1].name)
                    # for every panel check if an entry already exists in the user
                    # config variable and if it does not add a new one, last position
                    # and visible
                    if not (module_name in userConfig['Panels']):
                        position = len(userConfig['Panels'])
                        userConfig['Panels'][module_name] = [position, True]

    def MakeTheSideBar(self):
        """
        We create an option panel that will sit on the right side to modify panel specific parameters
        """

        sbPanel = MultiSplitterWindow(self.sp)
        sbPanel.SetOrientation(wx.VERTICAL)
        sbPanel.SetMinimumPaneSize(300)
        #sbPanel.SetSashSize(30)
        self.OptSB = OptionSideBar(sbPanel)
        self.OptSB.PopulateOptionsTree()
        self.ExportSB = ExportVariableSideBar(sbPanel)
        
        sbPanel.AppendWindow(self.OptSB,300)
        sbPanel.AppendWindow(self.ExportSB)

        return sbPanel
        
        

    def MakeTheTree(self):
        """
        Creates the tree
        """
        self.TreePanel = wx.Panel(self.sp, -1)

        TreeSizer = wx.BoxSizer(wx.VERTICAL)

        self.Tree = NavigationTree(self.TreePanel)
        self.Tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.Refresh)

        imageJoin = wx.Image(imgPath+'/t_hold.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        JoinBtn = GenBitmapToggleButton(self.TreePanel, wx.ID_ANY, bitmap=imageJoin, size = (imageJoin.GetWidth()+2, imageJoin.GetHeight()+2))
        JoinBtn.SetToolTipString('Join different selections of the tree in one virtual item')
        JoinBtn.Bind(wx.EVT_BUTTON, self.onJoinTreeItems)

        imageExpand = wx.Image(imgPath+'/t_apply.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        ExpandBtn = GenBitmapToggleButton(self.TreePanel, wx.ID_ANY, bitmap=imageExpand, size = (imageExpand.GetWidth()+2, imageExpand.GetHeight()+2))
        ExpandBtn.SetToolTipString('Expand / Collapse all tree items')
        ExpandBtn.Bind(wx.EVT_BUTTON, self.Tree.onExpandCollapseTree)

        TreeBTNSizer = wx.BoxSizer(wx.HORIZONTAL)
        TreeBTNSizer.Add(JoinBtn, 0, wx.ALL, 5)
        TreeBTNSizer.Add(ExpandBtn, 0, wx.ALL, 5)
        
        #BTNsizer.Add(TreeBTNSizer,0, wx.LEFT | wx.RIGHT, 5)
        
        TreeSizer.Add(self.Tree, 1, wx.EXPAND | wx.UP, 1 )
        TreeSizer.Add(TreeBTNSizer, 0)

        self.TreePanel.SetSizer(TreeSizer)


    def MakeMenuBar(self):
        """
        Creates the menubar
        """

        #Gives new IDs to the menu voices in the menubar
        ID_FILE_OPEN = wx.NewId()
        ID_FILE_SAVE = wx.NewId()
        ID_FILE_SAVE_AS = wx.NewId()
        ID_FILE_CLOSE =  wx.NewId()
        ID_FILE_EXIT =  wx.NewId()
        ID_TOOLS_OPTS = wx.NewId()
        ID_TOOLS_GRAPH = wx.NewId()
        ID_TOOLS_FILTER = wx.NewId()
        ID_COLORS = wx.NewId()
        ID_TOOLS_ERRBAR = wx.NewId()
        ID_TOOLS_UPDATE = wx.NewId()
        ID_WIN_DB = wx.NewId()
        ID_WIN_ANAL = wx.NewId()
        ID_WIN_OPTIonS = wx.NewId()
        ID_HELP_ABOUT =  wx.NewId()
        ID_SingleColor = []

        filemenu =  wx.Menu()
        filemenu. Append(ID_FILE_OPEN, '&Open File', 'Open a file')
        filemenu. Append(ID_FILE_SAVE, '&Save File', 'Save current file')
        filemenu. Append(ID_FILE_SAVE_AS, '&Save as...', 'Save current data in a new file')
        filemenu. Append(ID_FILE_CLOSE, '&Close File', 'Close')
        filemenu. AppendSeparator()
        filemenu. Append(ID_FILE_EXIT, 'E&xit Program', 'Exit')

        window_menu = wx.Menu()
        window_menu. Append(ID_WIN_DB, 'Database', 'Show the database window')        
        window_menu. Append(ID_WIN_ANAL, 'Analysis', 'Show the analysis window')
        window_menu. Append(ID_WIN_OPTIonS, 'Options', 'Show the preferences window') 
        window_menu.FindItemById(ID_WIN_ANAL).Enable(False)
        window_menu.FindItemById(ID_WIN_DB).Enable(self.SiblingMode)

        #Set Help Menu
        helpmenu =  wx.Menu()
        helpmenu. Append(ID_HELP_ABOUT, 'Abou&t')

        #Set the Drawing Options
        toolmenu = wx.Menu()
        toolmenu. Append(ID_TOOLS_OPTS, '&Options', 'Save Figures and change preferences')

        GUI['UseColor'] = 'Automatic'
        colormenu = wx.Menu()
        for color_name in ['Automatic'] + userConfig['plotting_colors_name']:
            ID_SingleColor.append(wx.NewId())
            colormenu. Append (ID_SingleColor[-1], color_name, color_name, wx.ITEM_RADIO )
            wx.EVT_MENU(self, ID_SingleColor[-1], partial(self.onChooseColor, color_name))

        sub_tool_menu = wx.Menu()

        sub_tool_menu. Append(ID_TOOLS_ERRBAR, 'Show &Error Bars', 'Show / Unshow Error Bars on Graph', wx.ITEM_CHECK)
        sub_tool_menu. Append(ID_TOOLS_FILTER, 'Use Activity Filter', 'Use the user defined filter for active/inactive flies', wx.ITEM_CHECK)
        sub_tool_menu.Check(ID_TOOLS_FILTER, True)

        sub_tool_menu. AppendMenu(ID_COLORS, 'Use Color', colormenu)


        toolmenu. AppendMenu(ID_TOOLS_GRAPH, '&Graphs', sub_tool_menu)
        toolmenu. Append(ID_TOOLS_UPDATE, 'Search for &Update')

        #Create the MenuBar
        menubar =  wx.MenuBar(style = wx.SIMPLE_BORDER)

        #Populate the MenuBar
        menubar. Append(filemenu, '&File')
        menubar. Append(toolmenu, '&Tools')
        menubar. Append(window_menu, '&Windows')
        menubar. Append(helpmenu, '&Help')

        #and create the menubar
        self.SetMenuBar(menubar)
        #and the statusbar
        self.CreateStatusBar()
        self.SetStatusText('Ready.')

        #associate Events to the menubar
        wx.EVT_MENU(self, ID_FILE_OPEN, partial (self.onFileOpen, None))
        wx.EVT_MENU(self, ID_FILE_SAVE, self.onFileSave)
        wx.EVT_MENU(self, ID_FILE_SAVE_AS, self.onFileSaveAs)
        wx.EVT_MENU(self, ID_FILE_CLOSE, self.onFileClose)
        wx.EVT_MENU(self, ID_FILE_EXIT, self.onFileExit)
        wx.EVT_MENU(self, ID_TOOLS_OPTS, self.onShowOptions)
        wx.EVT_MENU(self, ID_TOOLS_ERRBAR, self.onGraphErrBar)
        wx.EVT_MENU(self, ID_TOOLS_FILTER, self.onActivityFilter)
        wx.EVT_MENU(self, ID_TOOLS_UPDATE, partial (self.onCheckVersion, automatic=False))
        wx.EVT_MENU(self, ID_WIN_DB, self.onShowDatabase)
        #wx.EVT_MENU(self, ID_WIN_ANAL, self.onShowAnalysis)
        wx.EVT_MENU(self, ID_WIN_OPTIonS, self.onShowOptions)
        wx.EVT_MENU(self, ID_HELP_ABOUT, self.onAbout)

#----------------------------------------- EVENTS -----------------------------------------------------------#

    def openSingleVideoFile(self, filename):
        """
        Used to import a coords file from the legacy version of pySolo video plugin
        """
        global cDAM

        aborted = False
        if cDAM:
            JoiningFiles = True
            self.fileisModified = True
        else:
            JoiningFiles = False
            self.fileisModified = False

        GUI['filename'] = filename
        self.ProgressBarDlg(0, 'Importing a pySolo video file. Please Wait.')
        full_filename = os.path.join(GUI['dirname'], GUI['filename'])

        wx.BeginBusyCursor()
        
        vDAM = videoSlice()
        vDAM.loadSingleFile(full_filename, use_virtual_trikinetics=userConfig['virtual_trikinetics'], min_act=userConfig['min_distance'])

        if vDAM:
            cDAM = cDAM + [vDAM]
            self.ProgressBarDlg(70, 'Populating the Tree.')
            self.Tree.PopulateNavigationTree()
            self.ProgressBarDlg(-1, 'Done.')
            if not JoiningFiles:
                self.title = 'PySolo v%s - Analysis -- %s' % (pySoloVersion, full_filename)
            else:
                self.title = 'PySolo v%s - Analysis -- New File' % (pySoloVersion)
            self.SetTitle(self.title)

        else:

            self.ProgressBarDlg(-1, 'Error.')
            wx.MessageBox('%s is not a valid file.'    % filename, 'Error!', style=wx.OK|wx.ICon_EXCLAMATIon)

        wx.EndBusyCursor()
        
    def onJoinTreeItems(self, event):
        """
        Allow multiple selection of items without updating the panel status.
        """
        GUI['JoinTreeItems'] = not(GUI['JoinTreeItems'])
        if GUI['JoinTreeItems'] == False:
            self.Refresh(event)

    def onFileOpen(self, filename=None, event=None):
        """
        This event is called when the user selects the Open voice in the File Menu. It will prompt for the open file dialog and
        pass the filename to the LOADDADZIPData function
        """
        global cDAM

        aborted = False
        if cDAM:
            JoiningFiles = True
            self.fileisModified = True
        else:
            JoiningFiles = False
            self.fileisModified = False

        if not filename:
            wildcard = 'DAD files (*.dad)|*.dad|All files (*.*)|*.*'
            dlg = wx.FileDialog(self, 'Open DAD Analisys file...', defaultDir=userConfig['DAMoutput'],  style=wx.OPEN, wildcard=wildcard)

            if dlg.ShowModal() == wx.ID_OK:
                filename = GUI['filename']=str(dlg.GetFilename())
                GUI['dirname']=str(dlg.GetDirectory())
                dlg.Destroy()
            else:
                aborted = True


        if filename != None and not aborted:
            GUI['filename'] = filename
            self.ProgressBarDlg(0, 'Loading File. Please Wait.')
            full_filename = os.path.join(GUI['dirname'], GUI['filename'])

            wx.BeginBusyCursor()
            nDAM = LoadDADFile(full_filename)

            if nDAM:

                cDAM = cDAM + nDAM
                self.ProgressBarDlg(70, 'Populating the Tree.')
                self.Tree.PopulateNavigationTree()
                self.ProgressBarDlg(-1, 'Done.')
                if not JoiningFiles:
                    self.title = 'PySolo v%s - Analysis -- %s' % (pySoloVersion, full_filename)
                else:
                    self.title = 'PySolo v%s - Analysis -- New File' % (pySoloVersion)
                self.SetTitle(self.title)

            else:

                self.ProgressBarDlg(-1, 'Error.')
                wx.MessageBox('%s is not a valid file.'    % filename, 'Error!', style=wx.OK|wx.ICon_EXCLAMATIon)

            wx.EndBusyCursor()


    def onFileSave(self, event=None):
        """
        Save the current file
        """

        if GUI['filename']:

            filename = os.path.join(GUI['dirname'], GUI['filename'])

            wx.BeginBusyCursor()
            SuccessSaving = SaveDADFile(cDAM, filename)
            wx.EndBusyCursor()

            if SuccessSaving:
                self.fileisModified = False
                self.title = self.title.replace('(*)', '')
                self.SetTitle(self.title)
            else:
                wx.MessageBox('Error saving the file %s.\nDisk may be full or you may not have write rights.'    % filename, 'Error!', style=wx.OK|wx.ICon_EXCLAMATIon)

        else:

            self.onFileSaveAs(None)
        
    def onFileSaveAs(self, event):
        """
        Save the file with another name
        """
        wildcard = 'DAD files (*.dad)|*.dad|All files (*.*)|*.*'
        dlg = wx.FileDialog(self, 'Choose a file', userConfig['DAMoutput'], '', wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            GUI['filename']=dlg.GetFilename()
            GUI['dirname']=dlg.GetDirectory()
            self.onFileSave()
        dlg.Destroy()

    def onFileClose(self,event):
        """
        Closes the current File
        """
        if self.fileisModified:
            msg = 'The file has been modified.\n Are you sure you want to close it without saving?'
        else:
            msg = 'Do you want to close this file?'

        global cDAM
        dlg = wx.MessageDialog(self, msg, 'Closing', wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            dlg.Destroy()
            cDAM = []
            GUI['dirname'], GUI['filename'] = '', ''
            self.Tree.DeleteAllItems()
            self.title = 'PySolo v%s - Analysis' % pySoloVersion
            self.SetTitle(self.title)
            self.getOpenPanel().ClearEverything()
        else:
            dlg.Destroy()

    def onFileExit(self, event):
        """
        This event is called when the user selects the Exit voice in the file dialog. Prompt for confirmation before quitting
        """
        if self.fileisModified:
            dlg = wx.MessageDialog(self, 'File has been modified.\nDo you want to Exit anyhow?', 'Closing', wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                dlg.Destroy()
                self.Close(True)
            else:
                dlg.Destroy()
        else:
            self.Close(True)

    def onClose(self, event):
        """
        Hides or Closes the frame according to which modality the program is running
        """
        if not self.SiblingMode:
            self.Destroy()
        elif self.SiblingMode and self.BrotherFrame.IsShown():
            self.Show(False)
        else:
            self.Destroy()
            self.BrotherFrame.Destroy()

    def onResize(self, event):
        """
        When we resize the frame
        """
        XSize = self.Size[0]
        isOSBVisible = self.OptSB.IsShown()
        SashPos = isOSBVisible * (XSize - 400) or (XSize - 200 )
        self.sp.SetSashPosition(1, SashPos)
        event.Skip()


    def onShowDatabase(self, event):
        """
        Called when we want to Show the Database
        """

        if self.BrotherFrame.IsActive:
            self.BrotherFrame.Show(True)

    def onCheckVersion(self, event=None, automatic=True):
        """
        Check online for a newer version
        """
        wx.BeginBusyCursor()
        new_version = CheckUpdatedVersion()
        wx.EndBusyCursor()

        if new_version:
            message = 'You are running version %s.\n A newer version (%s) of PySolo is available on the website!' % (pySoloVersion, new_version)
        else:
            message = 'You are already running the latest version (%s)!' % pySoloVersion

        if new_version or (not new_version and not automatic):
            dlg = wx.MessageDialog(self, message , 'Searching for updates', wx.OK | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_OK: dlg.Destroy()

    def onAbout(self, event):
        """
        Shows the about dialog
        """
        about = 'pySolo - v %s\n' % pySoloVersion
        about += 'by Giorgio F. Gilestro\n'
        about += 'Visit http://www.pysolo.net for more information'
        
        dlg = wx.MessageDialog(self, about, 'About', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()


    def onShowOptions(self, event):
        """
        From Menu: Creates and shows the Option Panel
        """
        try:
            self.OptionPanel.Show(True)
        except:
            from pysolo_options import pySolo_OptionPanel
            self.OptionPanel = pySolo_OptionPanel(self)
            self.OptionPanel.Show(True)
            
    def onShowOptionsSideBar(self, event):
        """
        Show/Hide the Options Side bar on the right end side
        """
        XSize = self.Size[0]
        isVisible = not self.OptSB.IsShown()
        self.OptSB.Show(isVisible)
        SashPos = isVisible * (XSize - 400) or (XSize-self.initpos-5)
        self.sp.SetSashPosition(1, SashPos)


    def onGraphErrBar(self, event):
        """
        From Menu: When Errorbars are set true/false
        """
        global GUI
        GUI['ErrorBar'] = event.IsChecked()
        self.Refresh()

    def onActivityFilter(self, event):
        """
        From Menu: When the Activity Filter is set true/false
        """
        global GUI
        GUI['ActivityFilter'] = event.IsChecked()
        self.Refresh()
        
        
    def onChooseColor(self, color_name, event):
        """
        The user decides the color to be used for drawing
        """
        GUI['UseColor'] = color_name

    def getOpenPanel(self):
        """
        Get the name of the currently open notebook page
        """
        CurPage = self.nb.GetPageText( self.nb.GetSelection() )

        for Panel in self.Pages:
            if CurPage == Panel.name: return Panel


    def Refresh(self, event=None):
        """
        Checks what is the currently selected notebook page and draws data only there
        """

        #if we are not building a joint group then proceeds
        if not GUI['JoinTreeItems']:

            wx.BeginBusyCursor()

            if event:
                ChangingPage = (event.GetEventType() == wx.EVT_NOTEBOOK_PAGE_CHANGED.typeId)
            else:
                ChangingPage = True
                

            evtdata = []
            GUI['cDAM'] = cDAM

            #get all the selections from the tree and put them in a list
            for SelItem in self.Tree.GetSelections():
                evtdata.append (self.Tree.GetItemPyData(SelItem).GetData())

            if GUI['holdplot'] and not ChangingPage:
                GUI['currentData'].append ( evtdata )
            elif not GUI['holdplot'] and not ChangingPage:
                GUI['currentData'] = [evtdata]

            #Refresh the currently open notebook page
            self.getOpenPanel().RefreshAll(ChangingPage)
            currentPage = self.nb.GetPageText(self.nb.GetSelection())
            GUI['currentPage'] = currentPage


            #Close all children in the options tree
            for child in self.OptSB.OptionsTree.GetRootItem().GetChildren():
                self.OptSB.OptionsTree.Collapse(child)

            #then try to open the page corresponding to the current panel
            try:
                self.OptSB.OptionsTree.Expand(self.OptSB.OptionsTree.FindItem(self.OptSB.OptionsTree.GetRootItem(), currentPage))
                self.ExportSB.updateVariableList(currentPage)
            except:
                pass

            wx.EndBusyCursor()

        if event != None: event.Skip()


    def ProgressBarDlg(self, count, msg='', max = 100):
        """
        Creates and updates a progress bar dialog
        count: 0 will create the dialog, -1 will destroy it, x will update value to x
        msg = shows this message on the progressbardlg
        max = maximum value possible
        """
        keepGoing = True

        if count == 0:
            self.dlgPD = wx.ProgressDialog( 'Working', msg, maximum = max, parent=self, style = wx.PD_ELAPSED_TIME )
            (keepGoing, skip) = self.dlgPD.Pulse(msg)

        elif count == -1:
            self.dlgPD.Destroy()
        else:
            (keepGoing, skip) = self.dlgPD.Update(count, msg)


    def PassData(self, DAMData):
        """
        Receives the DAMdata passed from the DB brother frame. No need to load the data from disk again
        """
        global cDAM
        cDAM = DAMData
        self.Tree.PopulateNavigationTree()

    def SetfileisModified(self, event):
        """
        Set the flag to indicate that we have modified the file from its original version.
        """
        if not self.fileisModified:
            self.fileisModified = event.Modified
            self.title += '(*)'
            self.SetTitle(self.title)

cDAM = []

class MyApp(wx.App):
    def OnInit(self):
        self.ANAL_frame = pySolo_AnalysisFrame(None , -1, 'PySolo v%s - Analysis' % pySoloVersion )
        self.ANAL_frame.Show(True)
        self.SetTopWindow(self.ANAL_frame)
        return True
 


if __name__ == '__main__':

    # Run program
    #logText ('Starting pySolo anal')
    app=MyApp()
    app.MainLoop()



