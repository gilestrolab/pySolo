# -*- coding: utf-8 -*-
#
#       default_panels.py
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

import sys
sys.path.append('..')
from pysolo_lib import *
from pysolo_options import pySoloOption, PreferenceFileFound, SavePreferenceFile, userConfig, customUserConfig

import wx
import wx.grid as gridlib
from wx.lib.buttons import GenBitmapToggleButton
import wx.lib.masked as masked


import wxmpl
import matplotlib as mpl

import wx.lib.newevent
myEVT_OPTIONSB_SHOW_HIDE, EVT_OPTIONSB_SHOW_HIDE = wx.lib.newevent.NewCommandEvent()


class FileDrop(wx.FileDropTarget):
    '''
    Added to support opening of files on Drag and Drop
    file_extension is the extension of the file that we want to open
    '''
    def __init__(self, parent, allowedExtensions):
        wx.FileDropTarget.__init__(self)
        self.parent = parent
        self.allowedExtensions = allowedExtensions
        self.all_extensions = [ext for ext in allowedExtensions]

    def getFileExtension(self, filename):
        '''
        returns the extension of the filename
        '''
        ext = filename.split('.')[-1]
        return ext

    def OnDropFiles(self, x, y, filenames):
        '''
        On this event take filenames as a list containing the filenames to be open
        and process the files one by one.
        Only control we make on the file is that they have the right extension!
        '''
        for name in filenames:
            f_ext = self.getFileExtension(name)
            if f_ext in self.all_extensions:
                self.allowedExtensions[f_ext](filename=name)


#--- CLASS DEFINING THE TABLES ---#

class customDataTable(gridlib.PyGridTableBase):
    def __init__(self, colLabels, dataTypes, useValueCleaner=True):
        gridlib.PyGridTableBase.__init__(self)
        #self.log = log
        self.useValueCleaner = useValueCleaner
        self.colLabels = colLabels
        self.dataTypes = dataTypes
        self.data = [['']*len(self.dataTypes)]

    #--------------------------------------------------
    # required methods for the wxPyGridTableBase interface

    def GetNumberRows(self):
        try:
            return len(self.data)
        except:
            return 0

    def GetNumberCols(self):
        return len (self.colLabels)
##        try:
##            return len(self.data[0])
##        except:
##            return len(self.data)

    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col]
        except IndexError:
            return True

    def Reset(self, colLabels, dataTypes):
        '''
        Re-initialise the table
        reset(colLabels, dataTypes)
        '''
        n_col = self.GetNumberCols()-len(colLabels)
        if n_col > 0:
            self.GetView().ProcessTableMessage(
                        gridlib.GridTableMessage(self,
                        gridlib.GRIDTABLE_NOTIFY_COLS_DELETED,
                        1, n_col ))

            self.colLabels = colLabels
            self.dataTypes = dataTypes

        self.ClearTable()


    def ClearTable(self):
        '''
        Clear the table
        '''
        self.GetView().ProcessTableMessage(
                gridlib.GridTableMessage(self,
                gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED,
                0, self.GetNumberRows() ))
        self.data = []


    def GetValue(self, row, col):
        '''
        (row, col)
        Get value at given coordinates
        '''
        try:
            return self.data[row][col]
        except IndexError:
            return ''

    def InsertColumn(self, col_pos, col_type=gridlib.GRID_VALUE_FLOAT+':6,2', col_label=''):
        '''
        Add one grid column before col_pos, with type set to col_type and label col_label
        '''
        def transpose(whole_table):
            return map(lambda *row: list(row), *whole_table)

        empty_col = [''] * self.GetNumberCols()

        if self.GetNumberRows() > 0:
            t_data = transpose(self.data)
            t_data.insert(col_pos, empty_col)
            self.data = transpose(t_data)

        self.dataTypes.insert(col_pos, col_type)
        self.colLabels.insert(col_pos, col_label)


        self.GetView().ProcessTableMessage(
                gridlib.GridTableMessage(self,
                gridlib.GRIDTABLE_NOTIFY_COLS_INSERTED,
                col_pos, 1         ))

    def Sort(self, bycols, descending=False):
        '''
        sort the table by multiple columns
            bycols:  a list (or tuple) specifying the column numbers to sort by
                   e.g. (1,0) would sort by column 1, then by column 0
            descending: specify sorting order
        '''

        import operator

        table = self.data

        for col in reversed(bycols):
            table = sorted(table, key=operator.itemgetter(col))

        if descending:
           table.reverse()

        self.data = table

        msg=wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        self.GetView().ProcessTableMessage(msg)


    def AddRow (self, rows):
        '''
        Add one or more rows at the bottom of the table / sheet
        row can be an array of values or a 2-dimenstional array of rows and values
        '''

        rows = self.cleanFromMask(rows)

        if type(rows[0]) == list:
            n_rows = len (rows)
            for row in rows: self.data.append(row)
        else:
            self.data.append(rows)
            n_rows = 1

        self.GetView().ProcessTableMessage(
                gridlib.GridTableMessage(self,
                gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                n_rows         ))


    def RemRow (self, rows):
        '''
        Remove one or more rows
        '''

        [self.data.pop(int(x)-1) for x in rows]
        
        self.GetView().ProcessTableMessage(
                gridlib.GridTableMessage(self,
                gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED,
                len(rows)         ))
       

    def SetData(self, data=None):
        '''
        Set the whole content of the table to data
        '''
        data = self.cleanFromMask(data)
        self.ClearTable()
        self.data = data
        n_rows = self.GetNumberRows()
        self.GetView().ProcessTableMessage(
                gridlib.GridTableMessage(self,
                gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                n_rows ))

        self.GetView().ProcessTableMessage(
                gridlib.GridTableMessage(None,
                gridlib.GRIDTABLE_REQUEST_VIEW_GET_VALUES))

    def SetRow (self, row, data):
        data = self.cleanFromMask(data)
        try:
            self.data[row] = data
        except:
            self.AddRow(data)

    def SetValue(self, row, col, value):
        '''
        (row, col, value)
        Set Value for cell at given coordinates
        '''
        try:
            self.data[row][col] = value
        except IndexError:
            # add a new row
            self.data.append([''] * self.GetNumberCols())
            self.SetValue(row, col, value)

            # tell the grid we've added a row
            self.GetView().ProcessTableMessage(
                    gridlib.GridTableMessage(self,
                    gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED,
                    1                    ) )
    #--------------------------------------------------
    # Some optional methods

    def GetColLabelValue(self, col):
        '''
        Called when the grid needs to display labels
        '''
        return self.colLabels[col]

 

    def GetTypeName(self, row, col):
        '''
        Called to determine the kind of editor/renderer to use by
        default, doesn't necessarily have to be the same type used
        natively by the editor/renderer if they know how to convert.
        '''
        return self.dataTypes[col]


    def CanGetValueAs(self, row, col, typeName):
        '''
        Called to determine how the data can be fetched and stored by the
        editor and renderer.  This allows you to enforce some type-safety
        in the grid.
        '''
        colType = self.dataTypes[col].split(':')[0]
        if typeName == colType:
            return True
        else:
            return False

    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)

    def cleanFromMask(self, l):
        '''
        Goes through the list l and make sure it doesn't contain
        any masked value
        '''
        if self.useValueCleaner:
            try:
                if type(l[0]) == list:

                    for r in range(len(l)):
                        l[r] = self.cleanFromMask(l[r])
                else:

                    for c in range (len(l)):
                        if np.ma.getmask(l[c]): l[c] = '--'
                        if type(l[c]) != str and l[c] >= 999999: l[c] = '--'
            except:
                pass

        return l


class CustTableGrid(gridlib.Grid):
    '''
    This class describes a CustomGrid. Data are handled thorough a table but
    functions for the table are proxied from here
    '''
    def __init__(self, parent, colLabels, dataTypes, enableEdit = False, useValueCleaner=True):

        gridlib.Grid.__init__(self, parent, -1)
        self.table = customDataTable(colLabels, dataTypes, useValueCleaner)
        self.SetTable(self.table, True)
        self.EnableEditing(enableEdit)
        self.SetColMinimalAcceptableWidth(0)
        self.SetRowMinimalAcceptableHeight(0)
        self.checkableItems = self.table.dataTypes.count('bool') > 0

        self.sortedColumn=1
        self.sortedColumnDescending=False
        self.CtrlDown = False

        # we draw the column headers
        # code based on original implementation by Paul Mcnett
        #wx.EVT_PAINT(self.GetGridColLabelWindow(), self.OnColumnHeaderPaint)

        self.SetRowLabelSize(30)
        self.SetMargins(0,0)
        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.OnSort)
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.OnContextMenu)
        #self.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnLeftClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        #self.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.OnLeftDClick)

    def OnColumnHeaderPaint(self, evt):
        w = self.GetGridColLabelWindow()
        dc = wx.PaintDC(w)
        clientRect = w.GetClientRect()
        font = dc.GetFont()

        # For each column, draw it's rectangle, it's column name,
        # and it's sort indicator, if appropriate:
        #totColSize = 0
        totColSize = -self.GetViewStart()[0]*self.GetScrollPixelsPerUnit()[0] # Thanks Roger Binns
        for col in range(self.GetNumberCols()):
            dc.SetBrush(wx.Brush("WHEAT", wx.TRANSPARENT))
            dc.SetTextForeground(wx.BLACK)
            colSize = self.GetColSize(col)
            rect = (totColSize,0,colSize,32)
            dc.DrawRectangle(rect[0] - (col<>0 and 1 or 0), rect[1],
                             rect[2] + (col<>0 and 1 or 0), rect[3])
            totColSize += colSize

            if col == self.sortedColumn:
                font.SetWeight(wx.BOLD)
                # draw a triangle, pointed up or down, at the
                # top left of the column.
                left = rect[0] + 3
                top = rect[1] + 3

                dc.SetBrush(wx.Brush("WHEAT", wx.SOLID))
                if self.sortedColumnDescending:
                    dc.DrawPolygon([(left,top), (left+6,top), (left+3,top+4)])
                else:
                    dc.DrawPolygon([(left+3,top), (left+6, top+4), (left, top+4)])
            else:
                font.SetWeight(wx.NORMAL)

            dc.SetFont(font)
            dc.DrawLabel("%s" % self.GetTable().colLabels[col],
                     rect, wx.ALIGN_CENTER | wx.ALIGN_TOP)

    def Clear(self, *args, **kwargs):
        '''
        Clear the table empty
        '''
        self.table.ClearTable(*args, **kwargs)
        self.AutoSizeColumns()


    def Reset(self, *args, **kwargs):
        '''
        Reinitialize the table
        '''

        self.table.Reset(*args, **kwargs)
        self.AutoSizeColumns()

    def InsertCol (self, *args, **kwargs):
        '''
        (self, col_pos, col_type=gridlib.GRID_VALUE_FLOAT+':6,2', col_label='')
        Add one grid column before col_pos, with type set to col_type and label col_label
        '''

        self.table.InsertColumn (*args, **kwargs)
        self.AutoSizeColumns()


    def SetColsSize(self, cols_size):
        '''
        '''
        for col in range(len(cols_size)):
            self.SetColSize(col, cols_size[col])

    def GetData (self):
        '''
        Return a bidimensional array with a copy
        of the data in the spreadsheet
        '''
        all_data = self.table.data
        for row in range(len(all_data)):
            for col in range (len(all_data[row])):
                try:
                    all_data[row][col] = all_data[row][col].strip()
                except:
                    pass

        return all_data

    def SetData(self, *kargs, **kwargs):
        '''
        (data)
        Set the data of the table to the given value
        data is a bidimensional array
        '''
        self.table.SetData(*kargs, **kwargs)
        self.AutoSizeColumns()

    def GoToEnd(self):
        '''
        Go to the end of the table
        '''
        while self.MovePageDown():
            pass
        
    def AddRow(self, *kargs, **kwargs):
        '''
        Add one or more rows at the bottom of the table / sheet
        row can be an array of values or a 2-dimenstional array of rows and values
        '''

        self.table.AddRow(*kargs, **kwargs)
        self.AutoSizeColumns()
        #row = self.GetNumberRows()
        #self.GoToEnd()

    def RemRow(self, *kargs, **kwargs):
        '''
        Add one or more rows at the bottom of the table / sheet
        row can be an array of values or a 2-dimenstional array of rows and values
        '''

        self.table.RemRow(*kargs, **kwargs)
        self.AutoSizeColumns()
        row = self.GetNumberRows()

    def GetNumberRows(self, *kargs, **kwargs):
        '''
        Return the number of Rows
        '''
        return self.table.GetNumberRows ()

    def GetNumberCols(self, *kargs, **kwargs):
        '''
        Return the number of cols
        '''
        return self.table.GetNumberCols ()

    def HideCol(self, col):
        '''
        (col)
        Hide the specified column by setting its size to 0
        '''
        self.SetColSize(col, 0)

    def OnKeyUp(self, event):
        '''
        Records whether the Ctrl Key is up or down
        '''
        if event.GetKeyCode() == 308:
            self.CtrlDown = False
        event.Skip()

    def OnKeyDown(self, event):
        '''
        Responds to the following keys:
        Enter -> Jumps to next cell
        Ctrl-C -> Copy selected cells
        '''

        if event.GetKeyCode() == 308:
            self.CtrlDown = True
            event.Skip()

        if self.CtrlDown and event.GetKeyCode() == 67:
            self.OnCopySelected(event)
            event.Skip()

        if event.GetKeyCode() != wx.WXK_RETURN:
            event.Skip()
            return

        if event.ControlDown():   # the edit control needs this key
            event.Skip()
            return

        self.DisableCellEditControl()

        while 1 == 1:
            success = self.MoveCursorRight(event.ShiftDown())
            size_of_current_col = self.GetColSize(self.GetGridCursorCol())
            if size_of_current_col != 0 or not success: break

        if not success:
            newRow = self.GetGridCursorRow() + 1

            if newRow < self.GetTable().GetNumberRows():
                self.SetGridCursor(newRow, 0)
                self.MakeCellVisible(newRow, 0)
            else:
                #Add a new row here?
                pass

    def OnLeftClick(self, event):
        '''
        On mouse click checks if the cell contain a checkbox and if it does
        will change its status
        '''
        self.ForceRefresh()

    def OnSort(self, event):
        '''
        Clicking on the label of the columns sorts data in one order, a second click reverses the order.
        '''
        col = event.GetCol()
        if col >= 0:
            if col==self.sortedColumn:
                self.sortedColumnDescending=not self.sortedColumnDescending
            else:
                self.sortedColumn=col
                self.sortedColumnDescending=False

            sorting_order = range(self.GetNumberCols())
            sorting_order.pop(col)
            sorting_order = [col] + sorting_order

            self.table.Sort( sorting_order, self.sortedColumnDescending)
            self.Refresh()


    def OnContextMenu(self, event):
        '''
        Creates and handles a popup menu
        '''
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.OnCopyAll, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnCopyRow, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnCopyCol, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.OnCopySelected, id=self.popupID4)
            self.Bind(wx.EVT_MENU, self.OnExportToFile, id=self.popupID5)


        # make a menu
        menu = wx.Menu()
        menu.Append(self.popupID1, "Copy All")
        menu.Append(self.popupID2, "Copy Current Row")
        menu.Append(self.popupID3, "Copy Current Column")
        menu.Append(self.popupID4, "Copy Selected")
        menu.Append(self.popupID5, "Export All to file")

        #Add this voice only if the table has checkable items
        if self.checkableItems:
            self.popupID6 = wx.NewId()
            self.popupID7 = wx.NewId()
            self.Bind(wx.EVT_MENU, partial(self.OnCheckUncheckItems, True ), id=self.popupID6)
            self.Bind(wx.EVT_MENU, partial(self.OnCheckUncheckItems, False ), id=self.popupID7)
            menu.AppendSeparator()
            menu.Append(self.popupID6, "Check Selected")
            menu.Append(self.popupID7, "Uncheck Selected")
            #menu.Append(self.popupID8, "Remove Selected")


        self.PopupMenu(menu)
        menu.Destroy()

    def OnCopyCol(self, event):
        '''
        Copy to clipboard the content of the entire currently
        selected column, including the column label
        '''
        self.SelectCol(self.GetGridCursorCol())
        content = wx.TextDataObject()
        content.SetText(self.DataToCSV('\t', onlySel = True))
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(content)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Unable to open the clipboard", "Error")

    def OnCopyRow(self, event):
        '''
        Copy to clipboard the content of the entire currently
        selected row
        '''
        self.SelectRow(self.GetGridCursorRow())
        content = wx.TextDataObject()
        content.SetText(self.DataToCSV('\t', onlySel = True))
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(content)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Unable to open the clipboard", "Error")

    # I do this because I don't like the default behaviour of not starting the
    # cell editor on double clicks, but only a second click.
    def OnLeftDClick(self, evt):
        if self.CanEnableCellControl():
            self.EnableCellEditControl()

    def OnCopyAll(self, event):
        '''
        Copy the all table to clipboard
        '''
        content = wx.TextDataObject()
        content.SetText(self.DataToCSV('\t'))
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(content)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Unable to open the clipboard", "Error")

    def OnCopySelected(self, event):
        '''
        Copy selected cells to system clipboard
        '''
        content = wx.TextDataObject()
        content.SetText(self.DataToCSV('\t', onlySel = True))
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(content)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Unable to open the clipboard", "Error")

    def OnExportToFile(self, event):
        '''
        Save away the content of the grid as CSV file
        '''
        wildcard = 'CSV files (*.csv)|*.csv|All files (*.*)|*.*'
        dlg = wx.FileDialog(self, 'Choose a file', '', '', wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dirname=dlg.GetDirectory()
            filehandle=open(os.path.join(dirname, filename),'w')
            filehandle.write(self.DataToCSV(','))
            filehandle.close()
        dlg.Destroy()

    def DataToCSV(self, separator=',', onlySel = False):
        '''
        Convert the data in the grid to CSV value format (or equivalent)
        '''
        csv = ''
        r, c = 0, 0

        all_content = [self.table.colLabels] + self.table.data

        for row in all_content:
            c = 0
            notEmptyLine = ''
            for cell in row:
                if not(onlySel) or self.IsInSelection(r-1, c):
                    csv += str(cell)+separator
                    notEmptyLine = '\n'
                c+=1
            csv += notEmptyLine
            r +=1
        return csv

    def OnCheckUncheckItems(self, check_value, event):
        '''
        Check uncheck all checkable items in the selected rows
        '''
        c = self.table.dataTypes.index('bool')
        r = 0

        for row in self.table.data:
            if self.IsInSelection(r,c):
                self.table.SetValue(r,c, check_value)
            r += 1
        self.ForceRefresh()


#--- CLASS DEFINING THE PANELS ---#

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

class MyWXCanvas(FigureCanvas):
    '''
    This is the wxmpl canvas where the matplotlib plotting happens.
    '''
    def __init__(self, parent, size):
        self.parent = parent

        self.figure = Figure(figsize=size, dpi=96, facecolor='w', edgecolor='k')

        FigureCanvas.__init__(self, parent, -1, self.figure)
#        self.figure.set_facecolor('white')
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)
        #self.draw()

    def get_figure(self):
        return self.figure

    def _get_canvas_xy(self, evt):
        """
        Returns the X and Y coordinates of a wxPython event object converted to
        matplotlib canavas coordinates.
        """
        return evt.GetX(), int(self.figure.bbox.height - evt.GetY())

    def _onLeftButtonDown(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} left-click event handler,
        dispatching the event to the associated C{PlotPanelDirector}.
        """
        x, y = self._get_canvas_xy(evt)
        #self.director.leftButtonDown(evt, x, y)

    def _onLeftButtonUp(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} left-click-release event handler,
        dispatching the event to the associated C{PlotPanelDirector}.
        """
        x, y = self._get_canvas_xy(evt)
        #self.director.leftButtonUp(evt, x, y)
        print x,y


    def clear(self):
        '''
        Clear the contents of the canvas
        '''
        self.get_figure().clear()
        

    def redraw(self, plotfunction, *args, **kwargs):
        '''
        Update the contents of the canvas
        '''

        if not(GUI['holdplot']): self.get_figure().clear()
        #GUI['currentData'].append([plotfunction, args, kwargs])

        plotfunction(self.get_figure(),*args, **kwargs)
        self.draw()

    def OnContextMenu(self, event):
        '''
        Creates and handles a popup menu
        '''
        #event.Skip()
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.OnCopyFigure, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnPrintFigure, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnSaveFigure, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.OnResize, id=self.popupID4)
            self.Bind(wx.EVT_MENU, partial(self.OnZoomOut, event), id=self.popupID5)


        # make a menu
        menu = wx.Menu()
        menu.Append(self.popupID1, "Copy figure")
        menu.Append(self.popupID2, "Print figure")
        menu.Append(self.popupID3, "Save figure")
        menu.AppendSeparator()
        menu.Append(self.popupID4, "Change figure size")
        menu.Append(self.popupID5, "Zoom out")

        self.PopupMenu(menu)
        menu.Destroy()

#    def OnZoomOut(self, event):
#        pass

    def OnCopyFigure(self, event=None):
        '''
        Copy content of canvas to clipboard
        '''
        self.Copy_to_Clipboard()

    def OnPrintFigure(self, event=None):
        '''
        TO DO
        '''
        self.Printer_Print(event=event)
##        self.printData = wx.PrintData()
##        #self.printData = wx.PrintData( printer.GetPrintDialogData().GetPrintData() )
##        self.printData.SetPaperId(wx.PAPER_LETTER)
##        self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)
##        PrintingWindow = wxmpl.FigurePrinter(self, self.printData)
##        fig = self.get_figure()
##        PrintingWindow.previewFigure(fig)

    def OnSaveFigure(self, event=None):
        '''
        Save the current Figure as file: the output formats supported
        is deduced by the extension to filename.
        Possibilities are: eps, jpeg, pdf, png, ps, svg
        '''

##        wildcard = 'png files (*.png)|*.png|eps files (*.eps)|*.eps|PDF files (*.pdf)|*.pdf|postscript files (*.ps)|*.ps'
        wildcard = self._get_imagesave_wildcards()[0]

        dirname = '.'
        dlg = wx.FileDialog(self, 'Choose a file', dirname, '', wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dirname=dlg.GetDirectory()
            self.get_figure().savefig(str(os.path.join(dirname, filename)), dpi=250)
        dlg.Destroy()

    def OnResize(self, event=None):
        '''
        Set the size of the plotting canvas
        size is a tuple of pixels
        '''

        current_size = self.GetSize()
        dlg = wx.TextEntryDialog(self, 'Pick a new size (in pixel) for the current figure', defaultValue = '%s' % current_size)
        if dlg.ShowModal() == wx.ID_OK:
            new_size = dlg.GetValue().replace('(', '')
            new_size = new_size.replace('(', '')
            new_size = new_size.replace(')', '')
            new_size = new_size.replace(' ', '')
            new_size = new_size.split(',')
            new_size = (int(new_size[0]), int(new_size[1]))
            try:
                self.SetSize(new_size)
                self.parent.SetVirtualSize(new_size)
                ###self.virtualw.SetScrollbars(20, 20, size[0]/20, size[1]/20)
            except:
                wx.MessageBox('There was an error with the size you entered.\nCheck the format please!', 'Error!', style=wx.OK|wx.ICON_EXCLAMATION)


    def onPoint(self,event):
       '''
       Called by the EVT_POINT of wxmpl. Generates a pick_event
       '''
       event.axes.pick(event)

    def onPick(self,event):
       '''
       Called upon a pick_event
       '''
       print 'You picked %s' % event.ind

    def OnZoomOut(self, MouseEvent, commandEvent):
       self._onRightButtonUp(MouseEvent)

    def onKeyPick(self, event):
       if event.key=='p' and event.axes is not None:
           event.axes.pick(event)



class MyWxMPLCanvas(wxmpl.PlotPanel):
    '''
    This is the wxmpl canvas where the matplotlib plotting happens.
    '''
    def __init__(self, parent, size, dpi=250):
        self.parent = parent

        self.use_wxmpl = True
        self.dpi = dpi

        if self.use_wxmpl:
            wxmpl.PlotPanel.__init__(self, parent, -1, size = size)
            wxmpl.EVT_POINT(self, self.GetId(), self.onPoint)
            self.mpl_connect('pick_event', self.onPick)
            #self.mpl_connect('key_press_event', self.onKeyPick)
            self.set_crosshairs(userConfig['crosshair'])

        else:
            
            self.figure = Figure()
            dpi = 96
            FigureCanvas.__init__(self, parent, -1, self.figure)
    #        self.figure.set_edgecolor('black')
            self.figure.set_facecolor('white')


        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)
        #self.draw()
        #self.Show()

    '''
    def get_figure(self):
        if not self.use_wxmpl:
            return self.figure

    def _get_canvas_xy(self, evt):
        """
        Returns the X and Y coordinates of a wxPython event object converted to
        matplotlib canavas coordinates.
        """
        return evt.GetX(), int(self.figure.bbox.height - evt.GetY())

    def _onLeftButtonDown(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} left-click event handler,
        dispatching the event to the associated C{PlotPanelDirector}.
        """
        x, y = self._get_canvas_xy(evt)
        #self.director.leftButtonDown(evt, x, y)

    def _onLeftButtonUp(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} left-click-release event handler,
        dispatching the event to the associated C{PlotPanelDirector}.
        """
        x, y = self._get_canvas_xy(evt)
        #self.director.leftButtonUp(evt, x, y)
        print x,y
    '''

    def clear(self):
        '''
        Clear the contents of the canvas
        '''
        self.get_figure().clear()
        

    def redraw(self, plotfunction, *args, **kwargs):
        '''
        Update the contents of the canvas
        '''

        if not(GUI['holdplot']): self.get_figure().clear()
        #GUI['currentData'].append([plotfunction, args, kwargs])

        plotfunction(self.get_figure(),*args, **kwargs)
        self.draw()

    def OnContextMenu(self, event):
        '''
        Creates and handles a popup menu
        '''
        #event.Skip()
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.OnCopyFigure, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnPrintFigure, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnSaveFigure, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.OnResize, id=self.popupID4)
            self.Bind(wx.EVT_MENU, partial(self.OnZoomOut, event), id=self.popupID5)


        # make a menu
        menu = wx.Menu()
        menu.Append(self.popupID1, "Copy figure")
        menu.Append(self.popupID2, "Print figure")
        menu.Append(self.popupID3, "Save figure")
        menu.AppendSeparator()
        menu.Append(self.popupID4, "Change figure size")
        menu.Append(self.popupID5, "Zoom out")

        self.PopupMenu(menu)
        menu.Destroy()

#    def OnZoomOut(self, event):
#        pass

    def OnCopyFigure(self, event=None):
        '''
        Copy content of canvas to clipboard
        '''
        self.Copy_to_Clipboard()

    def OnPrintFigure(self, event=None):
        '''
        TO DO
        '''
        self.Printer_Print(event=event)
##        self.printData = wx.PrintData()
##        #self.printData = wx.PrintData( printer.GetPrintDialogData().GetPrintData() )
##        self.printData.SetPaperId(wx.PAPER_LETTER)
##        self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)
##        PrintingWindow = wxmpl.FigurePrinter(self, self.printData)
##        fig = self.get_figure()
##        PrintingWindow.previewFigure(fig)

    def OnSaveFigure(self, event=None):
        '''
        Save the current Figure as file: the output formats supported
        is deduced by the extension to filename.
        Possibilities are: eps, jpeg, pdf, png, ps, svg
        '''

##        wildcard = 'png files (*.png)|*.png|eps files (*.eps)|*.eps|PDF files (*.pdf)|*.pdf|postscript files (*.ps)|*.ps'
        wildcard = self._get_imagesave_wildcards()[0]

        dirname = '.'
        dlg = wx.FileDialog(self, 'Choose a file', dirname, '', wildcard, wx.SAVE | wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetFilename()
            dirname=dlg.GetDirectory()
            self.get_figure().savefig(str(os.path.join(dirname, filename)), dpi=self.dpi)
        dlg.Destroy()

    def OnResize(self, event=None):
        '''
        Set the size of the plotting canvas
        size is a tuple of pixels
        '''

        current_size = self.GetSize()
        dlg = wx.TextEntryDialog(self, 'Pick a new size (in pixel) for the current figure', defaultValue = '%s' % current_size)
        if dlg.ShowModal() == wx.ID_OK:
            new_size = dlg.GetValue().replace('(', '')
            new_size = new_size.replace('(', '')
            new_size = new_size.replace(')', '')
            new_size = new_size.replace(' ', '')
            new_size = new_size.split(',')
            new_size = (int(new_size[0]), int(new_size[1]))
            try:
                self.SetSize(new_size)
                self.parent.SetVirtualSize(new_size)
                ###self.virtualw.SetScrollbars(20, 20, size[0]/20, size[1]/20)
            except:
                wx.MessageBox('There was an error with the size you entered.\nCheck the format please!', 'Error!', style=wx.OK|wx.ICON_EXCLAMATION)


    def onPoint(self,event):
       '''
       Called by the EVT_POINT of wxmpl. Generates a pick_event
       '''
       event.axes.pick(event)

    def onPick(self,event):
       '''
       Called upon a pick_event
       '''
       print 'You picked %s' % event.ind

    def OnZoomOut(self, MouseEvent, commandEvent):
       self._onRightButtonUp(MouseEvent)

    def onKeyPick(self, event):
       if event.key=='p' and event.axes is not None:
           event.axes.pick(event)



class TimeLimits(wx.BoxSizer):
    '''This class defines the textbox used to specify temporal limits on the
    data to be analysed. It is not very elegant to have a separate class for it
    and I should find a better solution'''
    def __init__(self, parent):
        
        self.t, self.t1 = 0,1440
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.chk = wx.CheckBox(parent,wx.ID_ANY)
        self.txt = masked.TextCtrl(parent , -1, '0001:1440', mask = "####:####")
        #self.txt = wx.TextCtrl(parent, wx.ID_ANY, ':', size = (80,-1), style=wx.ALIGN_CENTER_HORIZONTAL)
        self.Add(self.chk,0)
        self.Add(self.txt,0)
        self.txt.Bind(wx.EVT_KILL_FOCUS, self.OnLoseFocus)
        self.chk.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)

    def isActive(self):
        return self.chk.GetValue()

    def GetVals(self):
        try:
            vals = self.txt.GetValue().split(':')
            return int(vals[0]), int(vals[1])
        except:
            return 0, 0

    def SetVals(self,t,t1):
        self.t, self.t1 = t, t1
        self.txt.SetValue(str(t)+':'+str(t1))

    def OnLoseFocus(self,event):
        self.Validate()

    def OnCheckBox(self,event):
        if self.Validate():
            self.t, self.t1 = self.GetVals()

    def Validate(self):
        value = self.txt.GetValue()
        vals = self.GetVals()

        if (vals[0] >= vals[1]) or (vals[0]<1) or (vals[1]>1440):
            self.txt.SetValue('0001:1440')
            return False
        else:
            return True


class ExportVariable(object):
    '''
    Class defining a variable that can be exported
    '''
    def __init__(self, panel_name, variable, variable_name, description):
        '''
        '''
        self.panel = panel_name
        self.variable = variable
        self.name = variable_name
        self.description = description
    
    def exportToFile(self, outfile, fileType='binary'):
        '''
        export to variable as np export object
        if it is not a numpy array, it will be first converted to one
        '''
        if 'binary' in fileType:
            np.save(outfile, self.variable)
        else:
            np.savetxt(outfile, self.variable, delimiter=',')   # X is an array

        return True


class pySoloPanel(wx.Panel):
    '''
    '''
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

    def AddOption(self, option_name, option_type, option_checked, option_choices, option_description):
        '''
        Called in from the panel code, will add a new variable option_name of type option_type. Default value
        will be at position option_checked of the list option_choices and option_description is used to describe
        the variable in the option Frame

        option_name = the name of the variable for the current panel
        option_type = boolean | radio | text | multiple
        option_checked = the int number indicating the position of the chosen value in option_choices. Must be 0 if option_type = text
        option_choices = a list containing the possible choices
        '''
        global customUserConfig

        if self.name not in customUserConfig:
            customUserConfig[self.name] = pySoloOption()

        if option_name not in customUserConfig[self.name]:
            customUserConfig[self.name].AddOption( option_name, option_type, option_checked, option_choices, option_description )


    def GetOption(self, option_name):
        '''
        Retrieve Selected value of a custom Panel variable
        If boolean will return True or False
        If radio or check will return the value in the list option_choices
        If text will return the text value as string.
        '''

        return customUserConfig[self.name].GetOption(option_name)

    def canExport(self, variable, var_name, var_description):
        '''
        Place in the dictionary the data concerning an exportable variable
        '''
        GUI['canExport'][var_name] = ExportVariable(self.name, variable, var_name, var_description)

    def isCompatible(self):
        """
        """
        return (pySoloVersion == 'dev') or (self.compatible >= pySoloVersion) or (self.compatible == 'all')


class GridGrid(pySoloPanel):
    '''This is the panel composed of n Grid, one above each other.
    Receives Proportions, Labels and dataTypes as lists.'''

    def __init__(self, parent, PanelProportion, Labels, dataTypes, choiceList=[]):
        pySoloPanel.__init__(self, parent)
        self.parent = parent

        if len(PanelProportion) != len(Labels) != len(dataTypes):
            print 'Error loading a GridGrid Module.'

        self.table, self.sheet = [], []
        sz = wx.BoxSizer (wx.VERTICAL)

        for n in range (0, len(PanelProportion)):
            self.sheet.append ( CustTableGrid(self, Labels[n], dataTypes[n]))
            sz.Add (self.sheet[n], PanelProportion[n], wx.EXPAND | wx.ALL, 10)

        #Some controls at the bottom of the panel
        lowCtrlSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.holdBTN = wx.ToggleButton(self, wx.ID_ANY, 'Add')
        self.holdplot = False
        GUI['holdplot'] = self.holdplot
        self.holdBTN.Bind(wx.EVT_TOGGLEBUTTON, self.OnHoldBTN)

        #Add the time limits box
        self.limits = TimeLimits(self)

        GUI['choice'] = '' #will change on the event
        self.choiceBox = wx.Choice(self, -1, (100, 50), choices = choiceList)
        self.choiceBox.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnChoice, self.choiceBox)
        if len(choiceList)==0: self.choiceBox.Show(False)

        lowCtrlSizer.Add(self.holdBTN, 0)
        lowCtrlSizer.Add(self.limits, 0)
        lowCtrlSizer.Add(self.choiceBox, 0, wx.ALL, 5)

        sz.Add(lowCtrlSizer,0 , wx.ALL, 10)

        self.SetSizer(sz)

    def OnHoldBTN(self, event):
        GUI['holdplot'] = self.holdplot = event.GetEventObject().GetValue()

    def OnChoice(self, event):
        GUI['choice'] = event.GetString()
        self.RefreshAll(True)

    def RefreshAll(self, repaint=False):

        GUI['choice'] = self.choiceBox.GetStringSelection()

        self.holdBTN.SetValue(GUI['holdplot'])

        if repaint:
            backup_hold = GUI['holdplot']
            GUI['holdplot'] = False
            GUI['currentlyDrawn'] = 1

            for GUI['dtList'] in GUI['currentData']:
                GUI['num_selected'] = len(GUI['dtList'])
                self.Refresh()
                GUI['holdplot'] = len(GUI['currentData'])>1
                GUI['currentlyDrawn'] += 1

            GUI['holdplot'] = backup_hold

        else:

            GUI['dtList'] = GUI['currentData'][-1]
            GUI['num_selected'] = len(GUI['dtList'])
            GUI['currentlyDrawn'] = len(GUI['currentData'])
            self.Refresh()

    def ClearEverything(self):
        '''
        '''
        GUI['currentData'] = []
        for sheet in self.sheet:
            sheet.Clear()


class PlotGrid(pySoloPanel):
    '''
    This is a panel containing a canvas in the upper part,
    a table, a comment textbox and some buttons to control the plotting on the lower side
    '''

    def __init__(self, parent, PanelProportion, CanvasInitialSize, colLabels, dataTypes, choiceList=[]):
        pySoloPanel.__init__(self, parent)
        self.parent = parent

        #Create Virtual Window
        self.virtualw = wx.ScrolledWindow(self)
        self.virtualw.SetScrollRate(20,20)
        self.cs = wx.BoxSizer()

        self.CreateCanvas(size = CanvasInitialSize )


        #Create Grid
        self.sheet = CustTableGrid(self, colLabels, dataTypes)


        #Create CommentBox
        self.commentText = wx.TextCtrl(self, -1,'', size=(-1, -1), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.commentTexthasFocus = 0
        self.commentText.Bind(wx.EVT_SET_FOCUS, self.TextGetFocus)
        self.commentText.Bind(wx.EVT_KILL_FOCUS, self.LoseFocus)
        self.commentText.Bind(wx.EVT_TEXT, self.onTextEntered)

        #Create Buttons and their sizer
        imageHold = wx.Image(imgPath +'/t_add.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.holdBTN = GenBitmapToggleButton(self, wx.ID_ANY, bitmap=imageHold, size = (imageHold.GetWidth()+2, imageHold.GetHeight()+2))
        self.holdBTN.SetToolTipString("Add more selections to this panel")
        GUI['holdplot'] = self.holdplot = False
        self.holdBTN.Bind(wx.EVT_BUTTON, self.OnHoldBTN)

        imageOptions = wx.Image(imgPath +'/t_options.png', wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.OptionsBTN = GenBitmapToggleButton(self, wx.ID_ANY, bitmap=imageOptions, size = (imageOptions.GetWidth()+2, imageOptions.GetHeight()+2))
        self.OptionsBTN.SetToolTipString("Show Options Sidebar")
        self.OptionsBTN.Bind(wx.EVT_BUTTON, self.OnOptionsBTN)

        #Add the time limits box
        self.limits = TimeLimits(self)

        GUI['choice'] = '' #will change on the event
        self.choiceBox = wx.Choice(self, wx.ID_ANY, (100, 50), choices = choiceList)
        self.choiceBox.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnChoice, self.choiceBox)
        if len(choiceList)==0: self.choiceBox.Show(False)

        GUI['inputbox'] = ''
        self.inputBox = wx.TextCtrl(self, wx.ID_ANY, GUI['inputbox'], size = (40,-1), style=wx.ALIGN_CENTER_HORIZONTAL)
        if GUI['inputbox'] == '': self.inputBox.Show(False)
        self.inputBox.Bind(wx.EVT_KILL_FOCUS, self.OnInputBox)

        lowCtrlSizer = wx.BoxSizer(wx.HORIZONTAL)

        lowCtrlSizer.Add(self.holdBTN, 0, wx.RIGHT, 8)
        lowCtrlSizer.Add(self.OptionsBTN,0, wx.RIGHT , 15)
        lowCtrlSizer.Add(self.limits, 0, wx.ALL, 3)
        lowCtrlSizer.Add(self.choiceBox,0, wx.LEFT | wx.RIGHT, 3)
        lowCtrlSizer.Add(self.inputBox,0, wx.LEFT | wx.RIGHT, 3)

        #Main panel sizer
        bs = wx.BoxSizer(wx.VERTICAL)
        bs.Add(self.virtualw, PanelProportion[0], wx.GROW|wx.ALL, 5)
        bs.Add(self.sheet, PanelProportion[1], wx.GROW|wx.ALL, 1)
        bs.Add(self.commentText , PanelProportion[2], wx.GROW|wx.ALL, 1)

        bs.Add(lowCtrlSizer)
        self.SetSizer(bs)
        

    def ShowHideOptionSB(target):
        '''
        Starts an EVENT telling around that the file has been
        modified from its original form
        '''
        #create the event
        evt = myEVT_OPTIONSB_SHOW_HIDE (wx.NewId())
        #post the event
        wx.PostEvent(target, evt)

    def CreateCanvas(self, size):
        '''
        Creates the canvas for plotting of the figures
        '''
        dpi = userConfig['dpi']
        use_wxmpl = ( userConfig['Canvas'] == 'wxmpl')
        
        if size == (-1,-1) or size == None:
            size = (userConfig['FigureSize'][0], userConfig['FigureSize'][1])

        if use_wxmpl:
            self.canvas = MyWxMPLCanvas(self.virtualw, size, dpi)
        else:
            self.canvas = MyWXCanvas(self.virtualw, size)
        
        self.virtualw.SetBackgroundColour(wx.NamedColour("white"))
       
        self.virtualw.SetVirtualSize(size)
        #self.virtualw.SetScrollbars(20, 20, size[0]/20, size[1]/20)
        self.virtualw.SetScrollRate(20,20) 

        self.cs.Add (self.canvas, 0)#, wx.GROW | wx.ALL, 5)
        self.virtualw.SetSizer(self.cs)
        self.virtualw.FitInside()

    def GetCanvasSize(self):
        return self.canvas.get_figure().get_size_inches()

    def SetCanvasSize(self, size):
        '''
        Set the size of the plotting canvas
        size is a tuple of pixels
        '''
        self.canvas.SetSize(size)
        self.virtualw.SetVirtualSize(size)
        #self.virtualw.SetScrollbars(20, 20, size[0]/20, size[1]/20)

    def OnHoldBTN(self, event):
        GUI['holdplot'] = self.holdplot = event.GetEventObject().GetValue()

    def OnOptionsBTN(self, evt):
        '''
        Press the option button to show the options for the current panel
        '''
        self.ShowHideOptionSB()
        #self.OptionFrame = not(self.OptionFrame)
        #self.optFRM.Show(self.OptionFrame)

    def OnInputBox(self,event):
        GUI['inputbox'] = self.inputBox.GetValue()
        self.RefreshAll(True)

    def OnChoice(self, event):
        GUI['choice'] = event.GetString()
        self.RefreshAll(True)

    def WriteComment(self,text):
        self.commentText.SetValue(text)

    def GetComment(self):
        return str(self.commentText.GetValue())

    def TextGetFocus(self,event):
        self.commentTexthasFocus = 1

    def LoseFocus(self,event):
        self.commentTexthasFocus = 0

    def onTextEntered(self,event):
        if self.commentTexthasFocus == 1:
            SetFileAsModified(self.parent)

    def CopyFigure(self):
        '''
        Copy content of canvas to clipboard
        '''
        self.canvas.Copy_to_Clipboard()

    def SaveFigure(self):
        '''
        Save content of canvas as file
        '''
        self.canvas.SaveFigure()

    def ClearEverything(self):
        '''
        Clear the content of the panel
        '''
        self.canvas.clear()
        self.canvas.draw()
        GUI['currentData'] = []
        self.sheet.Clear()
        self.WriteComment('')


    def RefreshAll(self, repaint = False):

        GUI['choice'] = self.choiceBox.GetStringSelection()

        if GUI['currentData'] == []:
            self.ClearEverything()


        self.holdBTN.SetValue(GUI['holdplot'])
        if repaint:
            backup_hold = GUI['holdplot']
            GUI['holdplot'] = False
            GUI['currentlyDrawn'] = 1

            for GUI['dtList'] in GUI['currentData']:
                GUI['num_selected'] = len(GUI['dtList'])
                self.Refresh()
                GUI['holdplot'] = len(GUI['currentData'])>1
                GUI['currentlyDrawn'] += 1

            GUI['holdplot'] = backup_hold

        else:

            GUI['dtList'] = GUI['currentData'][-1]
            GUI['num_selected'] = len(GUI['dtList'])
            GUI['currentlyDrawn'] = len(GUI['currentData'])
            self.Refresh()


#Some plotting function
        
def brighten(color, b=0.5):
    '''
    takes a hex matplotlib color and returns one with different brigthness (b)
    '''
    def dec2Hex(d):
        return int(d, 16)

    red, green, blue = dec2Hex(color[1:3]), dec2Hex(color[3:5]), dec2Hex(color[5:])


    if b > 1: raise 'b cannot be higher than 1'

    red += b*(255 - red)
    green += b*(255 - green)
    blue += b*(255 - blue)

    red = '%X' % red
    green = '%X' % green
    blue = '%X' % blue

    brighter_color = '#' + str(red).zfill(2) + str(green).zfill(2) + str(blue).zfill(2)
    return brighter_color

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


def getPlottingColor(num):
    '''
    Return the hex code for the Nth plotting color and its name
    '''

    if GUI['UseColor'] == 'Automatic':
        try:
            return userConfig['plotting_colors'][num], userConfig['plotting_colors_name'][num]
        except:
            wx.MessageBox('You cannot visualize more than %s different colors on the same graph. Sorry.' % len(userConfig['plotting_colors']), 'oops!', style=wx.OK|wx.ICON_EXCLAMATION)
            return userConfig['plotting_colors'][0], userConfig['plotting_colors_name'][0]
    else:
        i = userConfig['plotting_colors_name'].index(GUI['UseColor'])
        return userConfig['plotting_colors'][i], userConfig['plotting_colors_name'][i]


