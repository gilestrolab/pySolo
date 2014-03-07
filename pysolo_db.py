#!/usr/bin/env python

import os
from pysolo_path import panelPath, imgPath
from convert import c2d, c2b
os.sys.path.append(panelPath)

from default_panels import CustTableGrid, gridlib, SavePreferenceFile, FileDrop
from pysolo_lib import *
import wx.lib.calendar

class DAMlist(CustTableGrid):
    def __init__(self, *args, **kwargs):
        CustTableGrid.__init__(self, *args, **kwargs)
        self.Bind(wx.EVT_KEY_DOWN, self._OnKeyDown)

    def _OnKeyDown(self, event):
        """
        used for autocompletion
        """
        TAB_KEY = 9
        if event.GetKeyCode() == TAB_KEY:
            row = self.GetGridCursorRow()
            col = self.GetGridCursorCol()
            value = self.autoComplete(row, col)
            self.SetCellValue(row, col, value)
        event.Skip()

    def autoComplete(self, row, col):
        """
        auto complete
        """
        output = ''
        
        ct = ['','','mon1','ch1','mon2','ch2','','','mm1','dd1','mm2', 'dd2', 'yyyy','','']
        
        if ct[col] == 'ch1': #complete channel one
            output = 1

        if ct[col] == 'ch2': #complete channel two 
            output = 32

        if ct[col] == 'yyyy': #complete year
            output = datetime.date.today().year
        
        if ct[col] == 'mm1': #complete month one
            output = str(datetime.date.today().month)

        if ct[col] == 'dd1': #complete day one
            output = str(datetime.date.today().day)

        if ct[col] in ['mon2', 'mm2', 'dd2']: #auto complete end values
            output = self.table.data[row][col-2]

        return str(output)

    def rowNumber(self):
        """
        Return the number of rows that compose the table
        """
        return len(self.table.data)

    def AddTagToChecked(self, tag_name):
        """
        Add the specified tag to the cheked rows
        """
        for row in range( self.rowNumber() ):
            if self.table.data[row][1] and not self.table.data[row][14]: #if cheched and visible
                current_tags = self.table.data[row][13]
                if current_tags:
                        all_tags = set(current_tags.split(';'))
                        all_tags.discard('')
                else:
                        all_tags = set()
                all_tags.add(tag_name)
                self.table.data[row][13] = list2str(all_tags, separator=';')

    def RemoveTagFromChecked(self, tag_name):
        """
        Remove the specified tag from all checked rows
        """
        for row in range( self.rowNumber() ):
            if self.table.data[row][1] and not self.table.data[row][14]: #if cheched and visible
                all_tags = self.table.data[row][13].split(';')
                all_tags.remove(tag_name)
                self.table.data[row][13] = list2str(all_tags, ';')

    def ShowAll(self):
        """
        Show (unhide) all the rows
        """
        for row in range( self.rowNumber() ):
            if len(self.table.data[row]) == 15:
                self.table.data[row][14] = 0
            else:
                self.table.data[row].append(0)


    
    def ShowTagged(self, tag_name):
        """
        Show only the rows that have a specified tag_name
        """
        found_some = False
        self.ShowAll()
        
        if tag_name != 'All': #if we did not choose "All"
            for row in range( self.rowNumber() ):
                all_tags = self.table.data[row][13].split(';')
                if not tag_name in all_tags:
                    self.table.data[row][14] = 1 #hide
                    found_some = True

        return found_some

    def GetCheckedRows(self):
        """
        return a list containing the numbers corresponding to the checked rows
        """
        checked = []
        for row in self.table.data:
            if row[1]: checked.append(row[0]) # if the line is checked
        return checked

    def AllChecked(self):
        """
        are all the rows checked?
        """
        AllChecked = True
        for row in self.table.data:
            if not row[14]: AllChecked = AllChecked * row[1]
        return AllChecked

    def CheckAll(self, value):
        """
        Check / Uncheck all rows
        """
        for row in range( self.rowNumber() ):
            if not self.table.data[row][14]: self.table.data[row][1] = value
        
    def search(self, searchMask):
        """
        search in the table and show only the results that satisfy the query
        """

        for item in searchMask[-1]:

            if item != '' and item != '0' and item != '*':

                if  type(item) == str and item[0] == '*' and item[-1] == '*':
                    item = item[1:-1]
                    for row in range( self.rowNumber() ):
                        if item not in self.table.data[row][i]: self.table.data[row][14] = 1
                else:
                    for row in range( self.rowNumber() ):
                        if self.table.data[row][i] != item : self.table.data[row][14] = 1

            i += 1


    def ControRowsSyntax(self):
        """
        Goes through damlist and checks that all necessary values are filled in the checked rows
        """
        allFilled = True

        if ( len(self.table.data) == 0 ) or (list(zip(*self.table.data)[1]).count(True) == 0 ): allFilled = False #no row available or no row selected

        for row in self.table.data:
            if row[1]:
                for v in row[2:7]+row[8:13]:
                    if v == '': allFilled = False #at least one row has value missing

        return allFilled



    def DeleteRows(self, tobeDel):
        """
        Delete the rows specified in the tobeDel list
        """
        dl = self.table.data; self.SetData([])

        tobeDel.sort(); tobeDel.reverse()
        
        [dl.pop(int(x)-1) for x in tobeDel]
        for row in range(len(dl)): dl[row][0] = (row+1)
        
        self.SetData(dl)

    def AddRow(self, content=None, tag_name=''):
        """
        Add a new empty row. Will have the specified tag_name
        """
        #Create the new row and add it to the table
        new_id = '%s' % ( len(self.table.data)+1 )
        if content == None:
            content = [new_id, False] + [''] * 11 + [tag_name] + [False]
        self.table.AddRow([content])

    def ChangeRow(self, row, content):
        """
        Change the content of specified row
        """
        self.table.data[row] = content

    def Empty(self):
        """
        Clear empty the all table
        """
        #self.table.data = []
        self.SetData([])

    def hasValues(self):
        """
        is the table empty or has some values?
        """
        return (len(self.table.data) > 0)

    def UpdateChecked(self, content):
        """
        replace the content of all checked and visible rows
        """
        somethingChanged = False
        
        for row in range( self.rowNumber() ):
            if self.table.data[row][1] and not self.table.data[row][14]:
                for col in range (2,14):
                    if content[col]:
                        self.table.data[row][col] = content[col]
                        somethingChanged = True

        return somethingChanged

    def Update(self):
        """
        refresh and update the value of the table
        """
        self.SetData (self.table.data)
        self.doHide()

    def renumber(self):
        """
        Renumber all the list properly
        """
        for row in range(self.rowNumber()):
            self.table.data[row][0] = row+1



    def doHide(self):
        """
        Hide those rows where visible bool value is set to false
        """
        for row in range( self.rowNumber() ):
            if self.table.data[row][14]==1: self.SetRowSize(row,0)
        self.ForceRefresh()

              


class pySolo_DBFrame(wx.Frame):
    """
    This is the main frame class for the DB
    """
    def __init__(self, parent, id, title, siblingMode = False):

        wx.Frame.__init__(self, parent, id, title, (-1,-1), size=(1024,768), style = wx.DEFAULT_FRAME_STYLE )
        self.parent = parent
        self.SiblingMode = siblingMode
        self.GetOptionValues()
        self.searchResult= []
        self.MakeMenuBar()
        self.MakeTheNoteBook()
        self.updateListing()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        #Support for opening file on Drag and Drop
        allowedExtensions = dict()
        allowedExtensions['dal'] = self.OnFileOpen
        self.DropArea = FileDrop(self, allowedExtensions)
        self.SetDropTarget(self.DropArea)


    def __SetBrother__(self, brotherFrame):
           self.BrotherFrame = brotherFrame
           self.SiblingMode = True


    def MakeTheNoteBook(self):
        """
        Makes the Notebook
        """
        self.nb = wx.Notebook(self)
        self.nb.AddPage(self.PageListing(self.nb), 'Listing')
        self.nb.AddPage(self.PageBrowser(self.nb), 'Browser')
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged, self.nb)


    def GetOptionValues(self):
        """
        TODO!
        """
        self.title = 'PySolo v%s - Database' % pySoloVersion
        self.filename = ''
        self.INPUT_BOX = []
        self.BrowsingData = []
        self.chkAll = False
        self.lastSelected = -1
        self.fileIsModfied = False

        self.DAM = []
        self.DAMpath = userConfig['DAMinput'][:]
        self.dirname = userConfig['DAMoutput'][:]

    def TagPanel(self, parent):
        """
        This function creates the Tag Panel to be add to the notebook.
        Returns a Panel instance
        """
        tagpanel = wx.Panel(parent)
        self.TagList = []
        self.TagListBox = wx.ListBox(tagpanel, wx.ID_ANY, (0,0), (-1,-1), self.TagList)
        self.TagListBox.Bind (wx.EVT_LISTBOX, self.OnSelectTag)

        self.newTagBox = wx.TextCtrl(tagpanel, wx.ID_ANY)

        imageNewTag = wx.Image(imgPath+'/add_tag.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        newTagBtn = wx.BitmapButton(tagpanel, wx.ID_ANY, bitmap=imageNewTag, size = (imageNewTag.GetWidth()*1.3, imageNewTag.GetHeight()*1.3))
        newTagBtn.SetToolTipString('Add the tag typed in the lower text box to all the visible currently checked rows')
        newTagBtn.Bind(wx.EVT_BUTTON, self.OnNewTag)

        imageRemTag = wx.Image(imgPath+'/rem_tag.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        delTagBtn = wx.BitmapButton(tagpanel, wx.ID_ANY, bitmap=imageRemTag, size = (imageRemTag.GetWidth()*1.3, imageRemTag.GetHeight()*1.3))
        delTagBtn.Bind(wx.EVT_BUTTON, self.OnRemoveTag)
        delTagBtn.SetToolTipString('Remove the selected tag from all the currently visible checked rows')

        tagBtnSizer = wx.BoxSizer(wx.HORIZONTAL)
        tagBtnSizer.Add(newTagBtn, 0 ,wx.LEFT | wx.RIGHT, 1)
        tagBtnSizer.Add(delTagBtn, 0 ,wx.LEFT | wx.RIGHT, 1)

        tagsizer = wx.BoxSizer(wx.VERTICAL)
        tagsizer.Add( self.TagListBox, 1, wx.EXPAND | wx.GROW)
        tagsizer.Add( self.newTagBox, 0, wx.EXPAND | wx.GROW)
        tagsizer.Add( tagBtnSizer , 0, wx.ALL, 5)
        tagpanel.SetSizer(tagsizer)
        return tagpanel

    def PageListing(self, nb):
        """
        This function creates the Listing Panel to be add to the notebook.
        Returns a Panel instance
        """
        minpane, initpos = 130,130
        sp = wx.SplitterWindow(nb)
        sp.SplitVertically(self.TagPanel(sp), self.TableListing(sp), initpos)
        sp.SetMinimumPaneSize(minpane)
        return sp

    def resetTablesSize(self):
        """
        Set size for columns
        """
        cols_size = (30,22,38,38,38,38,100,100,38,38,38,38,42,0,0)

        self.DAMlist.SetColsSize(cols_size)
        self.DAMlist.SetRowLabelAlignment(0,0)
        self.DAMlist.SetRowLabelSize(3)

        self.searchSheet.SetColsSize(cols_size)
        self.searchSheet.SetRowLabelAlignment(0,0)
        self.searchSheet.SetRowLabelSize(3)

    def TableListing(self, parent):
        """
        This function creates the Listing Panel to be add to the notebook.
        Returns a Panel instance
        """
        tblpnl = wx.Panel(parent, wx.ID_ANY)

        colLabels = ['ID','','SM','SCh','EM','ECh','Genotype','Comment','MM','DD','MM','DD','YYYY','Tags','']
        dataTypes = [gridlib.GRID_VALUE_STRING] + [gridlib.GRID_VALUE_BOOL] + [gridlib.GRID_VALUE_STRING] * 12 + [gridlib.GRID_VALUE_BOOL]
        self.DAMlist = DAMlist(tblpnl, colLabels, dataTypes, enableEdit = True, useValueCleaner=False)
        self.DAMlist.SetData([])

        self.searchSheet = CustTableGrid(tblpnl, ['']*15, dataTypes, enableEdit = True, useValueCleaner=False)
        self.searchSheet.SetColLabelSize(5)

        self.resetTablesSize()

        tblsizer = wx.BoxSizer(wx.VERTICAL)
        lowerSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        imageAdd = wx.Image(imgPath +'/t_add.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        AddBtn = wx.BitmapButton(tblpnl, wx.ID_ANY, bitmap=imageAdd, size = (imageAdd.GetWidth()+2, imageAdd.GetHeight()+2))
        AddBtn.Bind(wx.EVT_BUTTON, self.OnAddRow)
        AddBtn.SetToolTipString('Append a new row at the end of the table')

        imageRem = wx.Image(imgPath +'/t_rem.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        RemBtn = wx.BitmapButton(tblpnl, wx.ID_ANY, bitmap=imageRem, size = (imageRem.GetWidth()+2, imageRem.GetHeight()+2))
        RemBtn.Bind(wx.EVT_BUTTON, self.OnRemRow)
        RemBtn.SetToolTipString('Remove selected row(s) from the table')


        imageDate = wx.Image(imgPath+'/t_calendar.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        CalendarBtn = wx.BitmapButton(tblpnl, wx.ID_ANY, bitmap=imageDate, size = (imageDate.GetWidth()+2, imageDate.GetHeight()+2))
        CalendarBtn.Bind(wx.EVT_BUTTON, self.OnCalendar)
        CalendarBtn.SetToolTipString('Show a calendar dialog to pick a date and fill the search mask')

        imageSearch = wx.Image(imgPath+'/t_search.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        searchBtn = wx.BitmapButton(tblpnl, wx.ID_ANY, bitmap=imageSearch, size = (imageSearch.GetWidth()+2, imageSearch.GetHeight()+2))
        searchBtn.Bind(wx.EVT_BUTTON, self.OnSearch)
        searchBtn.SetToolTipString('Search for the keys in the search mask among the currently selected tag')

        imageApply = wx.Image(imgPath+'/t_apply.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        ApplyBtn = wx.BitmapButton(tblpnl, wx.ID_ANY, bitmap=imageApply, size = (imageApply.GetWidth()+2, imageApply.GetHeight()+2))
        ApplyBtn.Bind(wx.EVT_BUTTON, self.OnApplyMods)
        ApplyBtn.SetToolTipString('Apply the values in the search mask to all the currently checked rows')

        imageCheckAll = wx.Image(imgPath+'/t_checkall.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        CheckAllBtn = wx.BitmapButton(tblpnl, wx.ID_ANY, bitmap=imageCheckAll, size = (imageCheckAll.GetWidth()+2, imageCheckAll.GetHeight()+2))
        CheckAllBtn.Bind(wx.EVT_BUTTON, self.OnCheckAll)
        CheckAllBtn.SetToolTipString('Check / Uncheck all the currently visible rows')

        imageShowAll = wx.Image(imgPath+'/t_showall.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        ShowAllBtn = wx.BitmapButton(tblpnl, wx.ID_ANY, bitmap=imageShowAll, size = (imageShowAll.GetWidth()+2, imageShowAll.GetHeight()+2))
        ShowAllBtn.Bind(wx.EVT_BUTTON, self.OnSelectTag)
        ShowAllBtn.SetToolTipString('Exit search mode and restore view')

        btnSizer.Add(AddBtn, 0 ,wx.LEFT | wx.RIGHT, 1)
        btnSizer.Add(RemBtn, 0 ,wx.LEFT | wx.RIGHT, 1)
        btnSizer.Add(wx.StaticLine(tblpnl, wx.ID_ANY, size=(1,28),style = wx.LI_VERTICAL),0,wx.LEFT | wx.RIGHT, 1)
        btnSizer.Add(wx.StaticLine(tblpnl, wx.ID_ANY, size=(1,28),style = wx.LI_VERTICAL),0,wx.LEFT | wx.RIGHT, 1)
        btnSizer.Add(searchBtn, 0 ,wx.LEFT | wx.RIGHT, 1)
        btnSizer.Add(ShowAllBtn, 0 ,wx.LEFT | wx.RIGHT, 1)
        btnSizer.Add(CheckAllBtn, 0 ,wx.LEFT | wx.RIGHT, 1)
        btnSizer.Add(wx.StaticLine(tblpnl, wx.ID_ANY, size=(1,28),style = wx.LI_VERTICAL),0,wx.LEFT | wx.RIGHT, 1)
        btnSizer.Add(wx.StaticLine(tblpnl, wx.ID_ANY, size=(1,28),style = wx.LI_VERTICAL),0,wx.LEFT | wx.RIGHT, 1)
        btnSizer.Add(CalendarBtn, 0 ,wx.LEFT | wx.RIGHT, 1)
        btnSizer.Add(ApplyBtn, 0 ,wx.LEFT | wx.RIGHT, 1)

        lowerSizer.Add(self.searchSheet, 1, wx.EXPAND | wx.GROW)
        lowerSizer.Add(btnSizer, 0, wx.EXPAND | wx.GROW)

        tblsizer.Add(self.DAMlist, 1, wx.EXPAND | wx.GROW)
        tblsizer.Add(lowerSizer, 0, wx.EXPAND | wx.GROW)

        tblpnl.SetSizer(tblsizer)
        return tblpnl

    def PageBrowser(self, nb):
        """
        Creates the Browsing panel to be add to the notebook
        Returns a Panel instance
        """

        gap = (1,1)
        labels = ('Mon', 'Start', 'End', ' ', 'Mon', 'Start', 'End', ' ', 'Mon', 'Start', 'End', '')
        panel = wx.Panel(nb)

        #creates all sizers
        mainsizer = wx.BoxSizer(wx.HORIZONTAL)
        rightsizer = wx.BoxSizer(wx.VERTICAL)
        genosizer = wx.BoxSizer(wx.HORIZONTAL)
        fgsizer = wx.FlexGridSizer(rows=5, cols=12, vgap=3, hgap=5)
        centralsizer = wx.BoxSizer(wx.HORIZONTAL)
        dgsizer = wx.FlexGridSizer(rows=4, cols=3, vgap=3, hgap=5)

        #creates the static boxes and their sizers
        MonBox = wx.StaticBox(panel, wx.ID_ANY, 'Monitors')
        monsizer = wx.StaticBoxSizer(MonBox, wx.VERTICAL)
        DayBox = wx.StaticBox(panel, wx.ID_ANY, 'Days')
        dayboxsizer = wx.StaticBoxSizer(DayBox, wx.VERTICAL)
        CommentBox = wx.StaticBox(panel,wx.ID_ANY,'Comment')
        commentboxsizer = wx.StaticBoxSizer(CommentBox, wx.VERTICAL)

        #creates the Genotype textctrl
        # self.BrowsingData[0] genotype
        self.BrowsingData.append(wx.TextCtrl(panel, wx.ID_ANY, size=(180,-1)))
        genosizer.Add (self.BrowsingData[-1], 0, wx.LEFT | wx.RIGHT, 10)
        genosizer.Add (wx.StaticText(panel, wx.ID_ANY, 'Genotype', style=wx.ALIGN_CENTER_VERTICAL),0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)

        #populate the monitor/channel start-end grid
        # self.BrowsingData[1][0 to 36] 
        for i in range (0,12):
            fgsizer.Add (wx.StaticText(panel, wx.ID_ANY, labels[i]),0, wx.ALIGN_CENTER)

        self.BrowsingData.append([])
        for mon in range(0,12):
            for txt in range (0,3):
                self.BrowsingData[1].append (wx.TextCtrl(panel, wx.ID_ANY, size=(30,-1)))
                fgsizer.Add(self.BrowsingData[1][-1])
            fgsizer.Add(gap)

        monsizer.Add(fgsizer, 0, wx.ALL, 5)

        self.BrowsingData.append([])
        for i in range (0,2):
            dgsizer.AddMany ([ wx.StaticText(panel, -1, ('From:', 'To:')[i]) ]+[gap,gap])
            self.BrowsingData[2].append ( wx.SpinCtrl(panel, -1, '', size=(45, -1)) )
            self.BrowsingData[2][-1].SetRange(1,12)
            dgsizer.Add(self.BrowsingData[2][-1])
            self.BrowsingData[2].append ( wx.SpinCtrl(panel, -1, '', size=(45, -1)) )
            self.BrowsingData[2][-1].SetRange(1,31)
            dgsizer.Add(self.BrowsingData[2][-1])
            self.BrowsingData[2].append ( wx.SpinCtrl(panel, -1, '', size=(80, -1)) )
            self.BrowsingData[2][-1].SetRange(2000,2020)
            dgsizer.Add(self.BrowsingData[2][-1])

        dayboxsizer.Add(dgsizer,0, wx.ALL, 5)

        #add the MonStaticBox and the daysStaticbox to the horizontal sizer
        centralsizer.Add(monsizer,0,wx.EXPAND | wx.ALL, 5 )
        centralsizer.Add(dayboxsizer,0,wx.EXPAND | wx.ALL ,5)

        #add the comment box
        self.BrowsingData.append (wx.TextCtrl(panel, -1,'', size=(200, 100), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER))
        commentboxsizer.Add(self.BrowsingData[-1], 0, wx.EXPAND | wx.ALL,10)

        #add the listbox on the left side of the panel
        self.BrowsingData.append(wx.ListBox(panel,wx.ID_ANY))
        self.BrowsingData[-1].InsertItems([''],0)
        self.BrowsingData[-1].Bind(wx.EVT_LISTBOX, self.OnChangeDAMentrySelection)

        #put everything in a sizer and return this panel
        rightsizer.AddMany([(1,10), genosizer, (1,5),centralsizer, (1,15),(commentboxsizer, 0, wx.EXPAND),(1,10)])
        mainsizer.Add(self.BrowsingData[-1],1,wx.EXPAND | wx.TOP | wx.BOTTOM, 15)
        mainsizer.Add(rightsizer,3, wx.ALL, 5)
        panel.SetSizer(mainsizer)
##        self.PopulateBrowser()
        return panel

    def MakeMenuBar(self):
        """
        Makes the Menu Bar
        """
        #Gives new IDs to the menu voices in the menubar
        ID_FILE_NEW = wx.NewId()
        ID_FILE_OPEN = wx.NewId()
        ID_FILE_EXPORT = wx.NewId()
        ID_FILE_IMPORT = wx.NewId()
        ID_FILE_SAVE = wx.NewId()
        ID_FILE_SAVE_AS = wx.NewId()
        ID_FILE_OPEN_RECENT = wx.NewId()
        ID_FILE_CLOSE =  wx.NewId()
        ID_FILE_EXIT =  wx.NewId()
        ID_ANAL_TYPE = wx.NewId()
        ID_ANAL_CHK = wx.NewId()
        ID_ANAL_SHOW = wx.NewId()
        ID_HELP_ABOUT =  wx.NewId()
        ID_ANAL_TEST = wx.NewId()
        ID_WIN_DB = wx.NewId()
        ID_WIN_ANAL = wx.NewId()
        ID_WIN_OPTIONS = wx.NewId()

        recent_menu = wx.Menu()
        fn_ID = []
        for fname in userConfig['RecentFiles']:
            fn_ID.append(wx.NewId())
            recent_menu. Append( fn_ID[-1], fname)
            wx.EVT_MENU(self, fn_ID[-1], partial (self.OnFileOpen, fname))

        file_menu =  wx.Menu()
        file_menu. Append(ID_FILE_NEW, '&New File', 'Create a new file')
        file_menu. Append(ID_FILE_OPEN, '&Open File', 'Open a file')
        file_menu. Append(ID_FILE_SAVE, '&Save File', 'Save current file')
        file_menu. Append(ID_FILE_SAVE_AS, '&Save as...', 'Save current file with new name')
        file_menu. AppendSeparator()
        file_menu. Append(ID_FILE_IMPORT, 'Import CSV File', 'Import list from CSV File')
        file_menu. Append(ID_FILE_EXPORT, 'Export to CSV File', 'Export List to CSV File')
        file_menu. AppendSeparator()
        file_menu. AppendMenu(ID_FILE_OPEN_RECENT, 'Open Recent Files', recent_menu)
        file_menu. Append(ID_FILE_CLOSE, '&Close File', 'Close')
        file_menu. Append(ID_FILE_EXIT, 'E&xit Program', 'Exit')

        data_type_menu = wx.Menu()
        dt_ID = []
        for data_type in userConfig['DataTypes']:
            dt_ID.append(wx.NewId())
            data_type_menu. Append( dt_ID[-1], data_type, data_type, wx.ITEM_RADIO)
            wx.EVT_MENU(self, dt_ID[-1], partial (self.OnSelectDataType, data_type))
        GUI['datatype'] = userConfig['DataTypes'][0] #default datatype


        anal_menu = wx.Menu()
        anal_menu. AppendMenu(ID_ANAL_TYPE, 'Data type', data_type_menu )
        anal_menu. Append(ID_ANAL_TEST, 'Check Raw Data Files', 'Test for the presence of raw data files')
        anal_menu. Append(ID_ANAL_CHK, 'Fetch &Raw Data', 'Fetch Raw Data for this table')
        anal_menu. AppendSeparator()
        anal_menu. Append(ID_ANAL_SHOW, 'Send Data to Analysis', 'Starts analysis window with current data')
        anal_menu.FindItemById(ID_ANAL_SHOW).Enable(self.SiblingMode)

        window_menu = wx.Menu()
        window_menu. Append(ID_WIN_DB, 'Database', 'Show the database window')
        window_menu. Append(ID_WIN_ANAL, 'Analysis', 'Show the analysis window')
        window_menu. Append(ID_WIN_OPTIONS, 'Options', 'Show the preferences window')
        window_menu.FindItemById(ID_WIN_DB).Enable(False)
        window_menu.FindItemById(ID_WIN_ANAL).Enable(self.SiblingMode)


        #Set Help Menu
        help_menu =  wx.Menu()
        help_menu. Append(ID_HELP_ABOUT, 'Abou&t')


        #Create the MenuBar
        menubar =  wx.MenuBar()

        #Populate the MenuBar
        menubar. Append(file_menu, '&File')
        menubar. Append(anal_menu, '&Analysis')
        menubar. Append(window_menu, '&Windows')
        menubar. Append(help_menu, '&Help')

        #and create the menubar
        self.SetMenuBar(menubar)
        #and the statusbar
        self.CreateStatusBar()
        self.SetStatusText('Ready.')

        #associate Events to the menubar
        wx.EVT_MENU(self, ID_FILE_NEW, self.OnFileNew)
        wx.EVT_MENU(self, ID_FILE_OPEN, partial (self.OnFileOpen, None))
        wx.EVT_MENU(self, ID_FILE_EXPORT, self.OnExportToCSV)
        wx.EVT_MENU(self, ID_FILE_IMPORT, self.OnImportFromCSV)
        wx.EVT_MENU(self, ID_FILE_SAVE, self.OnFileSave)
        wx.EVT_MENU(self, ID_FILE_SAVE_AS, self.OnFileSaveAs)
        wx.EVT_MENU(self, ID_FILE_CLOSE, self.OnFileClose)
        wx.EVT_MENU(self, ID_FILE_EXIT, self.OnFileExit)
        wx.EVT_MENU(self, ID_ANAL_CHK, partial (self.OnAnalysisLoad, False))
        wx.EVT_MENU(self, ID_ANAL_TEST, partial (self.OnAnalysisLoad, True))
        wx.EVT_MENU(self, ID_ANAL_SHOW, self.OnSendtoAnalysis)
        #wx.EVT_MENU(self, ID_WIN_DB, self.OnShowDatabase)
        wx.EVT_MENU(self, ID_WIN_ANAL, self.OnShowAnalysis)
        wx.EVT_MENU(self, ID_WIN_OPTIONS, self.OnShowOptions)
        wx.EVT_MENU(self, ID_HELP_ABOUT, self.OnAbout)

    def GetTagName(self):
        """
        Get currently selected tag name stripped from the brackets indicating the number of tagged items
        """
        sel_tag = self.TagListBox.GetSelection()
        
        if sel_tag != -1:
            tag_name = str(self.TagListBox.GetItems()[sel_tag])
            cut = tag_name.index('(') - 1
            tag_name = tag_name[:cut]
        else:
            tag_name = 'All'

        tag_name = tag_name.replace(';', '.,')

        return tag_name

    def OnSelectTag(self,event):
        """
        Will show only the row marked with the selected tag
        """

        tag_name = self.GetTagName()
        self.DAMlist.ShowTagged(tag_name)
        self.updateListing()

    def OnNewTag(self, event):
        """
        Add a new tag
        """
        
        tag_name = str(self.newTagBox.GetValue())
        tag_name = tag_name.replace(';', '\.,')

        if '(' in tag_name or ')' in tag_name:

            dlg = wx.MessageDialog(self, 'Brackets are not allowed in the tag name.', 'Error', wx.OK | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                dlg.Destroy()
            else:
                dlg.Destroy()

        if tag_name:

            #tag_name = ';'+tag_name+';'
            
            self.DAMlist.AddTagToChecked(tag_name)

            self.updateTagList()
            self.updateListing()


    def OnRemoveTag(self, event):
        """
        Remove the currently selected tag from the checked items
        """

        sel_tag = self.TagListBox.GetSelection()
        
        if sel_tag:
            tag_name = self.TagListBox.GetItems()[sel_tag]

            cut = tag_name.index('(') - 1
            tag_name = tag_name[:cut]
            
            self.DAMlist.RemoveTagFromChecked(tag_name)

            self.updateListing()
            self.updateTagList()



    def OnAddRow(self, event):
        """
        Add a new row to the table
        """

        #Get the Tagname that the new row will inherit
        tag_name = self.GetTagName()
        if tag_name == 'All': tag_name = None

        self.DAMlist.AddRow(content = None, tag_name=tag_name)


        self.resetTablesSize()

        #update the tag list if necessary
        sel = self.TagListBox.GetSelection()
        self.updateTagList(sel)

        self.DAMlist.GoToEnd()

    def OnRemRow(self, event):
        """
        Remove one or more rows from the table
        """
        del_msg = 'You need to check the lines you wish to remove first'

        tobeDel = self.DAMlist.GetCheckedRows()
        if tobeDel:
            del_msg = 'Are you sure you want to delete %s rows from the table?' % len(tobeDel)
        btnType = [wx.OK, wx.YES_NO][(tobeDel!=[])]
            
        dlgJoin = wx.MessageDialog(self, del_msg, 'Deleting rows from the table', btnType | wx.ICON_INFORMATION)
        ok_delete = (dlgJoin.ShowModal() == wx.ID_YES)
        dlgJoin.Destroy()
        
        
        if ok_delete: 
            self.DAMlist.DeleteRows(tobeDel)
            self.resetTablesSize()
            self.updateTagList()

    def OnTodayDate(self,event):
        """
        Clicking on the TodayDate the date mask is filled with the today's date
        """
        today = datetime.date.today()
        self.searchSheet.data[-1][8] = int(today.month)
        self.searchSheet.data[-1][9] = int(today.day)
        self.searchSheet.data[-1][10] = int(today.month)
        self.searchSheet.data[-1][11] = int(today.day)
        self.searchSheet.data[-1][12] = int(today.year)

    def OnApplyMods(self, event):
        """
        Clicking on the Apply button will fill all selected rows with the
        data in the search mask
        """
        searchString = self.searchSheet.GetData()[-1]
        
        somethingChanged = self.DAMlist.UpdateChecked(searchString)

        if somethingChanged:self.updateListing()

    def OnFileNew(self,event):
        """
        Creates a new DAL file
        """
        #ADD support for self.fileIsModfied
        self.filename = ''
        self.DAMlist.Empty()
        self.updateListing()
        ###self.PopulateBrowser()
        self.SetTitle( 'PySolo ' + pySoloVersion + ' - Database' )

    def OnFileOpen(self, filename=None, event=None):
        """
        Open a previously saved DAL file
        """
        joiningDAMlist = False

        if self.DAMlist.hasValues():
            dlgJoin = wx.MessageDialog(self, 'A file is already open. Do you want to join more data to the current ones?', 'Opening or joining', wx.YES_NO | wx.ICON_INFORMATION)
            joiningDAMlist = (dlgJoin.ShowModal() == wx.ID_YES)
            dlgJoin.Destroy()

        if not filename:

            wildcard = 'DAM list files (*.dal)|*.dal|All files (*.*)|*.*'
            dlg = wx.FileDialog(self, 'Open DAM list file...', defaultDir=userConfig['DAMoutput'], style=wx.OPEN, wildcard=wildcard)
            if dlg.ShowModal() == wx.ID_OK:
                self.filename = dlg.GetPath()
                dlg.Destroy()

                if not joiningDAMlist: self.DAMlist.Empty()
                self.ReadFile()
                self.SetTitle(self.title + ' -- ' + self.filename)
                self.updateListing()
                self.PopulateBrowser()

        else:
            if not joiningDAMlist: self.DAMlist.Empty()
            self.filename = filename
            self.ReadFile()
            self.SetTitle(self.title + ' -- ' + self.filename)
            self.updateListing()
            self.PopulateBrowser()


    def OnFileClose(self, event):
        """
        Closing current file
        """
        self.DAMlist.Empty()
        #self.ReadFile()
        self.SetTitle(self.title)
        self.updateListing()
        self.PopulateBrowser()
        self.updateTagList()

    def OnFileSave(self, event):
        """
        Save away the DAMlist as DAL file
        """
        
        if self.filename != '':
            # Open the file for write, write, close
            filehandle=open(os.path.join(self.dirname, self.filename),'w')
            cPickle.dump(self.DAMlist.GetData(), filehandle)
            filehandle.close()
            self.SetStatusText('File Succesfully saved.')
        else:
            self.OnFileSaveAs(None)


    def OnFileSaveAs(self, event):
        """
        Save away the DAMlist as DAL file
        """

        wildcard = 'DAM list files (*.dal)|*.dal|All files (*.*)|*.*'
        dlg = wx.FileDialog(self, 'Choose a file', self.dirname, '', wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            # Open the file for write, write, close
            self.filename=dlg.GetFilename()
            if '.dal' not in self.filename: self.filename = self.filename + '.dal'
            self.dirname=dlg.GetDirectory()
            filehandle=open(os.path.join(self.dirname, self.filename),'w')
            cPickle.dump(self.DAMlist.GetData(), filehandle)
            filehandle.close()
            self.SetStatusText('File Succesfully saved.')
        dlg.Destroy()


    def OnFileExit(self, event):
        """
        On Exit program
        """
        #add support for self.fileIsModfied
        dlg = wx.MessageDialog(self, 'Are you sure you want to exit from the program?', 'Closing', wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            dlg.Destroy()
            self.Close(True)
        else:
            dlg.Destroy()

    def OnClose(self, event):
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

    def OnSelectDataType(self, data_type = None, event = None):
        """
        We select which data type to use
        """
        #global GUI
        GUI['datatype'] = data_type

    def OnAnalysisLoad(self, checkOnlyFiles = False, evt = None):
        """
        Called when we want to load the raw data, creates the dad file and save it
        """

        self.DAM = []
        monrange = ''
        inputPath = userConfig['DAMinput'][:]

        if self.DAMlist.ControRowsSyntax():

            for row in self.DAMlist.GetData():
                if row[1]: # if the line is checked

                    if '/' not in str(row[2]) and (int(row[4]) - int(row[2]) > 0): # if we are spanning more than one monitor with the wrong syntax
                        for mon in range (int(row[2]), int(row[4])+1): monrange += str(mon)+'/'
                        mon_num = int(row[4]) - int(row[2])
                        row[3] = (str(row[3]) +'/'+'1/'*(mon_num))[0:-1]
                        row[5] = '32/'+ '32/'* (mon_num -1) + str(row[5])
                        row[2] = row[4] = monrange[0:-1]
                    
                    #we create one object for every checked line in the database. We then put objects in a list.    
                    self.DAM.append (DAMslice(row[2], row[3], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12]))
                                    #DAMslice(mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version=pySoloVersion)
                                    
            #Input format
            datatype = userConfig['DAMtype'] #Channel, Monitor, pvg_distance, pvg_beam, pvg_raw

            #TriKinetics Input Data
            if datatype == 'Monitor':
                self.LoadRawDataMonitor(inputPath, checkOnlyFiles)
            elif datatype == 'Channel' and GUI['datatype'] == 'Regular':
                self.LoadRawDataChannel(inputPath, checkOnlyFiles)
            elif datatype == 'Channel' and GUI['datatype'] == 'Video':
                print ("NOT SUPPORTED")

            #pySolo Video Input Data
            elif datatype == 'pvg_distance' or datatype == 'pvg_beam':
                self.LoadRawDataMonitor(inputPath, checkOnlyFiles)
                
             #pySolo Video Input Data RAW
            elif datatype == 'pvg_raw' and userConfig['virtual_trikinetics']:
                self.LoadRawDataVideo(inputPath, checkOnlyFiles, mode='beam')
            elif datatype == 'pvg_raw' and not userConfig['virtual_trikinetics']:
                self.LoadRawDataVideo(inputPath, checkOnlyFiles, mode='distance')                
        else:

            dlg = wx.MessageDialog(self, 'Please, check your entries.\nSome values are missing or no rows are checked.', 'Error', wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def OnSendtoAnalysis(self, event):
        """
        Called when we want to pass the currently analyse data to Anal
        """
        if not(self.DAM):
            self.BrotherFrame.Show(True)
            dlg = wx.MessageDialog(self,
             'Data Not Ready.\nYou need to load the raw data first!', 'Error.',
             wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        if self.BrotherFrame.IsActive and self.DAM:
            self.BrotherFrame.Show(True)
            self.BrotherFrame.PassData(self.DAM)


    def OnShowAnalysis(self, event):
        """
        Called when we want to pass the currently analyse data to Anal
        """

        if self.BrotherFrame.IsActive:
            self.BrotherFrame.Show(True)

    def OnShowOptions(self, event):
        """
        From Menu: Creates and shows the Option Panel
        """
        try:
            self.OptionPanel.Show(True)
        except:
            from pysolo_options import pySolo_OptionPanel
            self.OptionPanel = pySolo_OptionPanel(self)
            self.OptionPanel.Show(True)


    def OnImportFromCSV(self,event):
        """
        Import a list from a CSV file
        """
        csv = ''
        self.DAMlist.Empty()

        wildcard = 'CSV files (*.csv)|*.csv|All files (*.*)|*.*'
        dlg = wx.FileDialog(self, 'Open CSV file...', os.getcwd(), style=wx.OPEN, wildcard=wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetPath()
        try:
            filehandle = open(self.filename, 'r')
            csv = filehandle.read()
            filehandle.close()
        except cPickle.UnpicklingError:
            wx.MessageBox('%s is not a valid file.'    % self.filename, 'oops!', style=wx.OK|wx.ICON_EXCLAMATION)

            self.SetTitle(self.title + ' -- ' + self.filename)
        dlg.Destroy()

        ##TODO: check the importing from csv##
        for row in csv.split('\n')[:]:
            row_split = row.split(',')
            for i in range(len(row_split)):
                try:
                    row_split[i]=int(row_split[i])
                except:
                    pass
            self.DAMlist.AddRow(row_split)

        self.updateListing()
        self.PopulateBrowser()

    def OnCheckAll(self, event):
        """
        checks / unchecks all rows of currently visible items
        """

        AllChecked = self.DAMlist.AllChecked()

        self.DAMlist.CheckAll(not AllChecked)

        self.updateListing()

    def OnCalendar(self, event):       # test the date dialog
        months = ['January','February','March','April','May','June','July','August','September','October','November','December']

        dlg = wx.lib.calendar.CalenDlg(self)
        dlg.Centre()

        if dlg.ShowModal() == wx.ID_OK:
            result = dlg.result
            day = result[1]
            month = result[2]
            year = result[3]
            current_search = self.searchSheet.GetData()
            current_search[-1][8] = str(months.index(month)+1)
            current_search[-1][9] = str(day)
            current_search[-1][10] = str(months.index(month)+1)
            current_search[-1][11] = str(day)
            current_search[-1][12] = str(year)
            self.searchSheet.SetData(current_search)
            self.updateListing()


    def OnSearch(self,event):
        """
        Performs a search in the current DAMlist
        """

        self.OnSelectTag(None)

        i = 0
        searchMask = self.searchSheet.GetData()
        self.DAMlist.search(searchMask)
        self.updateListing()



    def OnExportToCSV(self, event):
        """
        Export current list to a CSV file
        """
        self.DAMlist.OnExportToFile(None)

    def OnChangeDAMentrySelection(self,event):
        """
        Called whenever we select a new item in the listbox of the Browser page
        """
        self.SaveDAMentry()
        self.PopulateBrowser(1)

    def OnAbout(self, event):
        """
        Shows the about dialog
        """
        about = 'pySolo - v %s\n' % pySoloVersion
        about += 'by Giorgio F. Gilestro\n'
        about += 'Visit http://www.pysolo.net for more information'
        
        dlg = wx.MessageDialog(self, about, 'About', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnPageChanged(self,event):
        """
        when the notebook page is changed the data are temporally saved in memory
        and the selected pane is refreshed
        """
        if self.nb.GetPageText(self.nb.GetSelection()) == 'Listing':
            self.SaveDAMentry()
            self.lastSelected = -1
            self.updateListing()
        if self.nb.GetPageText(self.nb.GetSelection()) == 'Browser':
            self.lastSelected = -1
            self.PopulateBrowser()

    def AutoFill(self, row, col, event):
        """
        Automatically fills the Monitor/Channel values in a smart way
        FIX THIS
        """
        col = self.AutoFillchk.GetValue()*col
        inc = int(self.AutoFillInc.GetValue())
        try:
            if col == 2 and row > 0: #autofill start monitor
                if (int(self.INPUT_BOX[row-1][5].GetValue()) == self.MaxDAMCh):
                    setThis = int(self.INPUT_BOX[row-1][4].GetValue())+1
                else:
                    setThis = self.INPUT_BOX[row-1][4].GetValue()
            elif col == 3 and row > 0: #autofill start Channel
                if (int(self.INPUT_BOX[row-1][5].GetValue()) == self.MaxDAMCh):
                    setThis = 1
                else:
                    if self.INPUT_BOX[row][2].GetValue() == self.INPUT_BOX[row-1][4].GetValue():
                        setThis = int(self.INPUT_BOX[row-1][5].GetValue())+1
            elif col == 4: #autofill end Monitor
                  setThis = self.INPUT_BOX[row][2].GetValue()
            elif (col == 5) and (inc != 0): #autofill end Channel
                if (int(self.INPUT_BOX[row][3].GetValue())+inc)<=self.MaxDAMCh:
                      setThis = int(self.INPUT_BOX[row][3].GetValue())+inc-1
                else: setThis = self.MaxDAMCh

            if (col<6) and ((row>0) or (col>=4)): self.INPUT_BOX[row][col].SetValue(str(setThis))
        except:
            pass


    def updateListing(self):
        """
        Refreshes the contents of the table
        """

        self.DAMlist.Update()
        self.searchSheet.ForceRefresh()
        self.resetTablesSize()



    def ClearBrowserPage(self):
        """
        clears off certain values from the browsing panel
        ## TODO: This should be changed to make the code more readable.
        """
        
        if not self.DAMlist.hasValues(): self.BrowsingData[4].Set([])
        
        self.BrowsingData[3].SetValue('')
        self.BrowsingData[0].SetValue('')
        for txt in self.BrowsingData[1]:
            txt.SetValue('')

    def PopulateBrowser(self,t=0):
        """
        Updates the contents of the Browser panel
        ## TODO: This should be changed to make the code more readable.
        """
        self.ClearBrowserPage()
        self.lastSelected = self.BrowsingData[-1].GetSelection()
        i = 1
        
        dl = self.DAMlist.GetData()

        if self.DAMlist.hasValues():

            if t == 0:  #means we want to refresh the listbox too
                i, filledDams = 0, []
                #Populates the listbox with the non empty genotypes
                for genotype in zip(*dl)[6]:
                    if genotype != '' :
                        filledDams.append (str(i+1)+' '+str(genotype))
                        i+=1
                self.BrowsingData[4].Set(filledDams) #.SetItems()
                i = len(filledDams)

            if i != 0:
                row = (self.lastSelected)
                if row>=0: #otherwise if row<0 means nothing is selected
                    dt = dl[row]
                    year = (len(dt[12])>4)*dt[12][5:] or dt[12]

                    self.BrowsingData[0].SetValue(str(dt[6])) #genotype

                    i, mons = 0, dt[2].split('/')
                    for mon in mons:
                        self.BrowsingData[1][i].SetValue(str(mon))
                        i+=3

                    i, chs = 1, dt[3].split('/')
                    for ch in chs:
                        self.BrowsingData[1][i].SetValue(str(ch))
                        i+=3

                    i, chs = 2, dt[5].split('/')
                    for ch in chs:
                        self.BrowsingData[1][i].SetValue(str(ch))
                        i+=3

                    self.BrowsingData[2][0].SetValue(int(dt[8]))#S MM
                    self.BrowsingData[2][1].SetValue(int(dt[9]))#S DD
                    self.BrowsingData[2][2].SetValue(int(dt[12][0:4]))#S YYYY
                    self.BrowsingData[2][3].SetValue(int(dt[10]))#E MM
                    self.BrowsingData[2][4].SetValue(int(dt[11]))#E DD
                    self.BrowsingData[2][5].SetValue(int(year))#E YY

                    self.BrowsingData[3].SetValue(str(dt[7])) #comment
            else:
                self.lastSelected = -1

    def SaveDAMentry(self):
        """
        Called from Browser panel: saves the current browsing entry
        # TODO: This should be changed to make the code more readable.
        """
        dl = self.DAMlist.GetData()
        if self.DAMlist.hasValues():
            row = (self.lastSelected)
            if row>=0: #otherwise if row<0 means nothing is selected
                dt = dl[row]

                dt[6] = str(self.BrowsingData[0].GetValue()) #genotype
                dt[7] = str(self.BrowsingData[3].GetValue()) #comment

                dt[8] = str(self.BrowsingData[2][0].GetValue()) #S MM
                dt[9] = str(self.BrowsingData[2][1].GetValue()) #S DD
                dt[10] = str(self.BrowsingData[2][3].GetValue()) #E MM
                dt[11] = str(self.BrowsingData[2][4].GetValue()) #E DD

                if self.BrowsingData[2][2].GetValue() != self.BrowsingData[2][5].GetValue():
                    dt[12] = str(self.BrowsingData[2][2].GetValue()) + '/' + str(self.BrowsingData[2][5].GetValue())
                else:
                    dt[12] = str(self.BrowsingData[2][2].GetValue())

                mons,schs,echs = '','',''
                for mon in self.BrowsingData[1][0::3]:
                    if mon.GetValue() != '': mons += str(mon.GetValue()) + '/'
                dt[2] = dt[4] = mons[:-1]

                for sch in self.BrowsingData[1][1::3]:
                    if sch.GetValue() != '': schs += str(sch.GetValue()) + '/'
                dt[3] = schs[:-1]

                for ech in self.BrowsingData[1][2::3]:
                    if ech.GetValue() != '': echs += str(ech.GetValue()) + '/'
                dt[5] = echs[:-1]

                self.DAMlist.ChangeRow(row, dt)

    def ReadFile(self):
        """
        Reads a DAL file and imports the data in the listing page
        """
        dl = self.DAMlist.GetData()
        try:
            FILE = open(self.filename, 'r')
            dl = dl + cPickle.load(FILE)
            self.DAMlist.SetData(dl)
            FILE.close()
        except cPickle.UnpicklingError:
            wx.MessageBox('%s is not a valid file.' % self.filename, 'oops!', style=wx.OK|wx.ICON_EXCLAMATION)

        self.DAMlist.renumber(); self.updateListing()
        self.updateTagList()

        self.AddRecentFile()


    def AddRecentFile(self):
        """
        Add the just opened file to the list of the most recent file names
        """
        max_no_entries_list = 5
        global userConfig
        rfl = userConfig['RecentFiles']

        #if the fname is already in the list will just move it to the top of the list
        if self.filename in rfl:
            p = rfl.index(self.filename)
            rfl[0], rfl[p] = rfl[p], rfl[0]
        #otherwise it will append it to the list
        else:
            if self.filename[-4:] == '.dal': rfl.append(self.filename)

        if len(rfl) > max_no_entries_list: rfl.pop(max_no_entries_list)

        userConfig['RecentFiles'] = rfl
        SavePreferenceFile(userConfig, customUserConfig)


    def updateTagList(self, selection=0):
        """
        Reads all tags present in the current DAMlist
        Returns a list alphabetically ordered
        """

        if self.DAMlist.hasValues():

            all_tags = []
            dl = self.DAMlist.GetData()
            all_num = 'All (%s)' % len(dl)
            for tag in (zip(*dl)[13]):
                all_tags = all_tags + str(tag).split(';')
    
            set_tags = list(set(all_tags))
            if '' in set_tags: set_tags.remove('')
            set_tags.sort()
    
            for i in range(0,len(set_tags)):
                tag_num = all_tags.count(set_tags[i])
                tag_name = set_tags[i].replace('\.,', ';')
                set_tags[i] =  '%s (%s)' %  (tag_name, tag_num)
    
            self.TagListBox.SetItems([all_num]+set_tags)
            self.TagListBox.SetSelection(selection)
            
        else:
            
            self.TagListBox.SetItems([])


    def ProgressBarDlg(self, count, msg='', max = 100):
        """
        Shows a progress bar dialog and updates it
        """
        keepGoing = True

        if count == 0:
            self.dlgPD = wx.ProgressDialog( 'Working', msg, maximum = max, parent=self, style = wx.PD_ELAPSED_TIME )
            (keepGoing, skip) = self.dlgPD.Pulse(msg)
        elif count == -1:
            (keepGoing, skip) = self.dlgPD.Pulse(msg)
        elif count == -2:
            self.dlgPD.Destroy()
        elif count > 0:
            (keepGoing, skip) = self.dlgPD.Update(count, msg)

    def LoadRawDataVideo(self, inputPath, checkFilesOnly = False, timedData=True, mode='distance'): #USER DEFINED
        """
        Takes the data from the folder where the raw data are placed
        Uses the one file one monitor syntax
        """

        year = month = day = monitor = channel = ''
        PDcount = 0
        additional_error = ''
        prev_filename = ''
        extension = userConfig['DAMextension']

        #calculate how many flies we have to analize in total
        totnum = 0
        for row in self.DAM:
            totnum += (row.totDays * row.totFlies)

        #self.ProgressBarDlg(0,'Loading Raw Data')


        for k in range(len(self.DAM)): # for every DAM

                for d in range(self.DAM[k].totDays): # for every day
                
                    progress =  ( float(PDcount) / float(totnum) ) * 100.0  
                    self.ProgressBarDlg( progress, 'Loading Raw Data.\n %s flies of %s processed.' % (PDcount, totnum) )

                    day = '%02d' % self.DAM[k].getDatesRange()[0][d]
                    month = '%02d' % self.DAM[k].getDatesRange()[1][d]
                    year = '%s' % self.DAM[k].getDatesRange()[2][d]
                    filepath = '%s/%s/%s%s/' % (year, month, month, day)
                    

                    for f in range (self.DAM[k].totFlies):
                        if PDcount < 0: break
                        
                        monitor_name = '%03d' % int(self.DAM[k].rangeChannel[1][f])
                        filename = '%s%sM%s%s' % (month, day, monitor_name, extension)
                        fullpath = os.path.join(inputPath, filepath, filename)

                        new_monitor = (filename != prev_filename); prev_filename = filename

                        if checkFilesOnly:

                            if not os.path.exists(fullpath):
                                PDcount = -1   
                                additional_error = 'Make sure the File exists and it is accessible'
                            else:
                                PDcount += 1  #if no error is encountered will increment PDcount by 1

                        else:
                            
                            if 1==1: # to set the contents to the current fly
                                
                                if new_monitor:
                                    
                                    if mode == 'distance': DAMf = c2d (fullpath)
                                    elif mode == 'beam': DAMf = c2b (fullpath)
                                    
                                    rawData = np.zeros((1440,32))
                                    c = 0; cf = 0
                                    startChannel = self.DAM[k].getChannelName(0, f)

                                    for line in DAMf.split('\n')[:-1]:
                                        try:
                                            rawData[c] = [ int(float(i)) for i in line.split('\t')[10:] ]
                                            c += 1
                                        except:
                                            print 'Error with file %s at row number %s. Wrong data type? [ %s ]' % (filename, c, line)

                                self.DAM[k].setFly(d,f, rawData[:,cf+startChannel-1])
                                cf += 1
                                PDcount += 1
                            else:
                                if PDcount > 0 and len(rawData[cf]) != 1440: additional_error = 'Not enough bins in the file.\n Only %s bins were found.' % len(content)
                                PDcount = -1

        if PDcount < 0:
            dlg = wx.MessageDialog(self, 'Error with file!\n%s\n%s' % (fullpath, additional_error), 'Error', wx.OK | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES: dlg.Destroy()
        elif PDcount > 0 and not checkFilesOnly:
            self.ProgressBarDlg(-1,'Saving Data to File...')
            self.SaveDADData()
        elif PDcount > 0 and checkFilesOnly:
            dlg = wx.MessageDialog(self, 'All files required for the analysis were found.\nYou may now proceed with fetching the raw data.' , 'All ok.', wx.OK | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES: dlg.Destroy()


        self.ProgressBarDlg(-2,'End.')


    def LoadRawDataMonitor(self, inputPath, checkFilesOnly = False, timedData=True): #USER DEFINED
        """
        Takes the data from the folder where the raw data are placed
        Uses the one file one monitor syntax
        """

        year = month = day = monitor = channel = ''
        PDcount = 0
        additional_error = ''
        prev_filename = ''
        extension = userConfig['DAMextension']

        #calculate how many flies we have to analize in total
        totnum = 0
        for row in self.DAM:
            totnum += (row.totDays * row.totFlies)

        #self.ProgressBarDlg(0,'Loading Raw Data')


        for k in range(len(self.DAM)): # for every DAM

                for d in range(self.DAM[k].totDays): # for every day
                
                    progress =  ( float(PDcount) / float(totnum) ) * 100.0  
                    self.ProgressBarDlg( progress, 'Loading Raw Data.\n %s flies of %s processed.' % (PDcount, totnum) )

                    day = '%02d' % self.DAM[k].getDatesRange()[0][d]
                    month = '%02d' % self.DAM[k].getDatesRange()[1][d]
                    year = '%s' % self.DAM[k].getDatesRange()[2][d]
                    filepath = '%s/%s/%s%s/' % (year, month, month, day)

                    for f in range (self.DAM[k].totFlies):
                        if PDcount < 0: break
                        
                        monitor_name = '%03d' % int(self.DAM[k].rangeChannel[1][f])
                        
                        filename = '%s%sM%s%s' % (month, day, monitor_name, extension)
                        fullpath = os.path.join(inputPath, filepath, filename)

                        new_monitor = (filename != prev_filename)
                        prev_filename = filename


                        if checkFilesOnly:

                            if not os.path.exists(fullpath):
                                PDcount = -1   
                                additional_error = 'Make sure the File exists and it is accessible'
                            else:
                                PDcount += 1  #if no error is encountered will increment PDcount by 1

                        else:

                            try: # to access and open the file
                                DAMf = open (fullpath, 'r')
                            except:
                                PDcount = -1
                                additional_error = 'Make sure the File exists and it is accessible'
                            
                            if 1==1: # to set the contents to the current fly
                                
                                if new_monitor:
                                    rawData = np.zeros((1440,32))
                                    c = 0; cf = 0
                                    startChannel = self.DAM[k].getChannelName(0, f)

                                    content = DAMf.readlines()
                                    for line in content:
                                        while '\n' in line: line = line.replace('\n', '') #remove newline characters
                                        while '\r' in line: line = line.replace('\r', '')
                                        try:
                                            rawData[c] = [ int(float(i)) for i in line.split('\t')[10:] ]
                                            c += 1
                                        except:
                                            print 'Error with file %s at row number %s. Wrong data type? [ %s ]' % (filename, c, line)

                                    DAMf.close()

                                self.DAM[k].setFly(d,f, rawData[:,cf+startChannel-1])
                                cf += 1
                                PDcount += 1
                            else:
                                if PDcount > 0 and len(rawData[cf]) != 1440: additional_error = 'Not enough bins in the file.\n Only %s bins were found.' % len(content)
                                PDcount = -1

        if PDcount < 0:
            dlg = wx.MessageDialog(self, 'Error with file!\n%s\n%s' % (fullpath, additional_error), 'Error', wx.OK | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES: dlg.Destroy()
        elif PDcount > 0 and not checkFilesOnly:
            self.ProgressBarDlg(-1,'Saving Data to File...')
            self.SaveDADData()
        elif PDcount > 0 and checkFilesOnly:
            dlg = wx.MessageDialog(self, 'All files required for the analysis were found.\nYou may now proceed with fetching the raw data.' , 'All ok.', wx.OK | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES: dlg.Destroy()


        self.ProgressBarDlg(-2,'End.')



    def LoadRawDataChannel(self, inputPath, checkFilesOnly = False, timedData=True): #USER DEFINED
        """
        Takes the data from the folder where the raw data are placed
        Uses the one file one channel syntax
        """

        year = month = day = monitor = channel = ''
        PDcount = 0
        additional_error = ''
        extension = userConfig['DAMextension']


        #calculate how many flies we have to analize in total
        totnum = 0
        for row in self.DAM:
            totnum += (row.totDays * row.totFlies)

        for k in range(0,len(self.DAM)):

                for d in range(self.DAM[k].totDays):
                
                    progress =  ( float(PDcount) / float(totnum) ) * 100.0
                    self.ProgressBarDlg( progress, 'Loading Raw Data.\n %s files of %s processed.' % (PDcount, totnum) )
                    day = '%02d' % self.DAM[k].rangeDays[0][d]
                    month = '%02d' % self.DAM[k].rangeDays[1][d]
                    year = '%s' % self.DAM[k].rangeDays[2][d]
                    filepath = '%s/%s/%s%s/' % (year, month, month, day)

                    for f in range (self.DAM[k].totFlies):
                        if PDcount < 0: break
                        monitor = '%03d' % int(self.DAM[k].rangeChannel[1][f])
                        channel = '%02d' % int(self.DAM[k].rangeChannel[0][f])

                        filename = '%s%sM%sC%s%s' % (month, day, monitor, channel, extension)
                        fullpath = os.path.join(inputPath, filepath, filename)

                        if checkFilesOnly:

                            if not os.path.exists(fullpath):
                                PDcount = -1   
                            else:
                                PDcount += 1  #if no error is encountered will increment PDcount by 1

                        else:

                            try: # to access and open the file
                                DAMf = open (fullpath, 'r')
                            except:
                                PDcount = -1
                                additional_error = 'Make sure the File exists and it is accessible'

                            try: # to set the contents to the current fly
                                content = DAMf.readlines()[4:] #remove 4 lines of headers, should be USERDEFINED
                                DAMf.close()
                                while '\n' in content: content = content.replace('\n', '')
                                while '\r' in content: content = content.replace('\r', '')
                                content = [int(line) for line in content] #remove newline character at the end of each line
                                self.DAM[k].setFly(d,f, content[:1440]) #1440 should be USERDEFINED
                                PDcount += 1
                            except:
                                if PDcount > 0 and len(content) != 1440: additional_error = 'Not enough bins in the file.\n Only %s bins were found.' % len(content)
                                PDcount = -1

        if PDcount < 0:
            dlg = wx.MessageDialog(self, 'Error with file!\n%s\n%s' % (fullpath, additional_error), 'Error', wx.OK | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES: dlg.Destroy()
        elif PDcount > 0 and not checkFilesOnly:
            self.ProgressBarDlg(-1,'Saving Data to File...')
            self.SaveDADData()
        elif PDcount > 0 and checkFilesOnly:
            dlg = wx.MessageDialog(self, 'All files required for the analysis were found.\nYou may now proceed with fetching the raw data.' , 'All ok.', wx.OK | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES: dlg.Destroy()


        self.ProgressBarDlg(-2,'End.')

    def SaveDADData(self):
        """
        Save away the analysed data as DAD file.
        A first big file with tmp extension is created than zipped into a smaller archive and then deleted
        """
        wildcard = 'DAM DATA files (*.dad)|*.dad|All files (*.*)|*.*'
        dlg = wx.FileDialog(self, 'Choose a file', self.dirname, '', wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            # Open the file for write, write, close
            self.DADfilename=dlg.GetFilename()
            extension = self.DADfilename.split('.')[-1]
            if extension != 'dad': self.DADfilename = '%s.dad' % self.DADfilename
            self.dirname=dlg.GetDirectory()

            filename = os.path.join(self.dirname, self.DADfilename)
            SaveDADFile(self.DAM, filename)

class MyApp(wx.App):
    def OnInit(self):
        self.DBframe = pySolo_DBFrame(None , -1, 'PySolo v%s - Database' % pySoloVersion)
        self.DBframe.Show(True)
        self.SetTopWindow(self.DBframe)
        return True


if __name__ == '__main__':

    # Run program
#    psyco.full()
    logText ('Starting pySolo db')
    app=MyApp()
    app.MainLoop()

