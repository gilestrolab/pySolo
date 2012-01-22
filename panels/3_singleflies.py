'''
This Panel will take the coordinates of the data coming from the tree selection
and get the data diveded by 24h. Will plot the sleep pattern fly by fly as scatter plot.
X axis is average sleep time, Y axis is AI, size of each bubble is its standard deviation
'''
from default_panels import *

class Panel(PlotGrid):

    def __init__(self, parent):
        
        PanelProportion = [6,2,1]
        CanvasInitialSize = (10,6)     #size in inches
        choiceList = ['sleep TD','sleep RD','sleep RN'] # this will appear on the right of the buttons
        
        colLabels = ['Genotype', 'Mon', 'Ch', 'alive', 'Day 1' , 'AVG', 'SD']
        dataTypes = [gridlib.GRID_VALUE_STRING] * 3 + [gridlib.GRID_VALUE_NUMBER] * 1 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * (3)
        
        PlotGrid.__init__(self, parent,
                        PanelProportion,
                        CanvasInitialSize,
                        colLabels,
                        dataTypes,
                        choiceList
                        )
                        
                        
        self.name = 'Single Fly Data'
        self.compatible = 'all'
        
    def Refresh(self):
        '''
        This function takes the coordinates coming upon tree item selection
        and fills the grid with the data about all flies
        '''
        
        allSelections = GUI['dtList']
        cDAM = GUI['cDAM']
        pos = GUI['currentlyDrawn']
        num_of_selected = GUI['num_selected']
        holdplot = GUI['holdplot']
        
        
        genotype_set, day_set, mon_set, ch_set = set ([]), set ([]), set ([]), set([])
        last_gen, last_day, last_mon = '','',''
        
        colLabels = ['Genotype', 'Mon', 'Ch', 'alive', 'Day 1' , 'AVG', 'SD']
        dataTypes = [gridlib.GRID_VALUE_STRING] * 3 + [gridlib.GRID_VALUE_NUMBER] * 1 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * (3)

        #get start and end value in the limit subpanel
        t0, t1 = self.limits.isActive() * self.limits.GetVals() or (None, None)

        single_fly_data = []
        
        for n_sel, selection in enumerate(allSelections): #every selection carries a 5 digits coordinate 

            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]
            
            gen_t = cSEL.getGenotype()
            genotype_set.add ( last_gen )
    
            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)
    
            # take the 3D arrays for
            # ax -> fly activity (the raw data of beam crossing)
            # s5 -> the 5mins sleep bins
            ax_t, s5_t = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1)[0:2]

            if n_sel == 0:
                s5 = s5_t
                ax = ax_t
            else:
                s5 = concatenate ((s5, s5_t), axis=0)
                ax = concatenate ((ax, ax_t), axis=0)

       
        ## OUT OF THE SELECTION LOOP HERE 
        if GUI['choice'] == 'sleep TD':
            day_values = SleepAmountByFly (s5)
        elif GUI['choice'] == 'sleep RD':
            day_values = SleepAmountByFly (s5, t0=0, t1=720)
        elif GUI['choice'] == 'sleep RN':
            day_values = SleepAmountByFly (s5, t0=720, t1=1440)
        
        AI_day_values = ActivityIndexByFly(ax, s5)

        # The size of this table has to change with the number of days we
        # have selected. Also if we are holding the plot we have to make
        # sure the table is as wide as the longest of our selections
        add_day_cols = self.sheet.GetNumberCols() - len (colLabels)
        ds, fs = 0, 0
        de, fe = s5.shape[0:2]

        if de > add_day_cols + 1:
            add_day_cols = de + 1 - add_day_cols
        else:
            add_day_cols = 0


        #Here we COLLECT the data for the lower grid (SINGLE FLIES)
        buffer_values = [''] * (add_day_cols - s5.shape[1] - 1)
        
        for f in range (fe) or [fs]:
            mon_t = cSEL.getMonitorName(m, d, f) or 'All'
            mon_set.add ( mon_t )
            ch_t = cSEL.getChannelName(m, f) or 'All'

            alive = (s5.sum(axis=2) < 1430)[:,f].sum()
            header = [gen_t, mon_t, ch_t, alive]

            cleaned_list = day_values[:,f].tolist()
            single_fly_data.append ( header + cleaned_list + buffer_values +  [average(day_values[:,f]), std(day_values[:,f])] )

        #Here we COLLECT some information about the days we are analysing.
        #This information will go in the title and the column header of the table
        for d in range (ds,de) or [ds]:
            day_t = cSEL.getDate(d, f) or 'All'
            day_set.add (day_t)

        # Here we add new columns to the table in case we need to write data for more than one day
        if not holdplot: self.sheet.Reset(colLabels, dataTypes)
        for il in range(add_day_cols-2):
            self.sheet.InsertCol (5, gridlib.GRID_VALUE_FLOAT+':6,2' , 'day %s' % (add_day_cols-il-1))

        #HERE WE DO THE ACTUAL FILLING OF THE TABLE
        if holdplot:
            title = 'Multiple Selection'
            self.sheet.AddRow(single_fly_data)
            color, color_name = getPlottingColor(pos-1)
        else:
            self.sheet.SetData(single_fly_data)
            color, color_name = getPlottingColor(0)
            title = list2str(genotype_set) +' - Day: '+ list2str(day_set) +', Mon: ' +list2str(mon_set)#+ ', Ch. '+list2str(Ch)


        # AND HERE WE PASS THE DATA TO BE DRAWN ON THE PLOT
        self.canvas.redraw(self.ScatterPlot, title, day_values, AI_day_values , color)


    def ScatterPlot(self, fig, title, sleep, AI, color):
        '''
        we calculate what we need. We compress them into lists to get rid of masked values
        '''
        
        area = np.ma.compressed( sleep.std(axis=0) )
        area = np.array([a or 3.0 for a in area]) #if one of the values is 0, then we put it to 3
        sleep = np.ma.compressed( average(sleep, axis=0) )
        AI = np.ma.compressed ( average(AI, axis=0) )

        a1 = fig.add_subplot(111)
        if sleep.any(): #we need this to prevent the graph from plotting a dead fly (that would result in an error)
            a1.scatter(sleep, AI, alpha = 0.75, c = color, s = area, marker = 'o', picker=True)


        a1.set_title(title)
        a1.set_ylabel('Activity Index')
        a1.set_xlabel('Sleep (m/d)')

