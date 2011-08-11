'''This Panel will take the coordinates of the data coming from the tree selection
and get the data diveded by 24h. Will plot the sleep pattern day by day and show the data
in the table.'''
#Default IMPORTED MODULES (DO NOT REMOVE)

from default_panels import *


class Panel(PlotGrid):

    #Here some variable specific to the PanelType

    def __init__(self, parent):

        PanelProportion = [6,2,1]    #0 = not_show
        CanvasInitialSize = (12,12)     #size in inches

        colLabels = ['Genotype','Day','Mon','Ch','n(tot)','n(a)','sleep TD','st.dv.','sleep RD','st.dv.','sleep RN','st.dv.','AI','','st.dv','','color' ]
        dataTypes = [gridlib.GRID_VALUE_STRING] * 4 + [gridlib.GRID_VALUE_NUMBER] *2 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * 10 + [gridlib.GRID_VALUE_STRING]

        PlotGrid.__init__(self, parent,
                                         PanelProportion,
                                         CanvasInitialSize,
                                         colLabels,
                                         dataTypes
                                         #choiceList
                                         )
        self.name = 'Day By Day'
        self.compatible = '0.9'

        self.AddOption('Yactivity', 'radio', 3, ['Max (dynamic)', '15', '10', '5'], 'Set the upper limit for the Y axis on the Activity plot')

    def Refresh(self):
        '''This function takes the coordinates from the item selection and plots the data as day by day'''

        allSelections = GUI['dtList']
        cDAM = GUI['cDAM']
        ShowErrorBar = GUI['ErrorBar']
        holdplot = GUI['holdplot']
        num_of_selected = GUI['num_selected']

        datarow = []
        genotype_set, mon_set, ch_set, day_set = set ([]), set ([]), set ([]), set ([])
        
        #get start and end value in the limit subpanel
        t0, t1 = self.limits.isActive() * self.limits.GetVals() or (None, None)

        for n_sel, selection in enumerate(allSelections): #every selection carries a 5 digits coordinate

            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]

            genotype_set.add ( cSEL.getGenotype() )
            mon_t = cSEL.getMonitorName(m, d, f) or 'All'; mon_set.add(mon_t)
            ch_t = cSEL.getChannelName(m, f) or 'All'; ch_set.add(ch_t)
            day_t = cSEL.getDate(d, format = 'mm/dd') or 'All'; day_set.add(day_t)

            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)

            ax_t, s5_t, s30_t = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1)  #get the S5 of the currently selected item

            if n_sel == 0:
                s5 = s5_t
                ax = ax_t
                s30 = s30_t
            else:
                s5 = concatenate ((s5, s5_t))
                ax = concatenate ((ax, ax_t))
                s30 = concatenate ((s30, s30_t))

        #OUT OF THE LOOP HERE
        num_flies = s5.shape[1]
        num_alive = (s5.sum(axis=2)<1430).all(axis=0).sum()
        dist_tot_sleep_by_fly = SleepAmountByFly (s5)
        dist_day_sleep_by_fly = SleepAmountByFly (s5, t0=0, t1=720)
        dist_night_sleep_by_fly = SleepAmountByFly (s5, t0=720, t1=1440)
        dist_AI_by_fly = ActivityIndexByFly(ax, s5)
        
        for d in range(s5.shape[0]):
            total_sleep = average(dist_tot_sleep_by_fly[d])
            std_total_sleep = std(dist_tot_sleep_by_fly[d])
            day_sleep = average(dist_day_sleep_by_fly[d])
            std_day_sleep = std(dist_day_sleep_by_fly[d])
            night_sleep = average(dist_night_sleep_by_fly[d])
            std_night_sleep = std(dist_night_sleep_by_fly[d])
            AI = average(dist_AI_by_fly[d])
            std_AI = std(dist_AI_by_fly[d])
            if len(day_set) == 1:
                day = cSEL.getDate(d, format = 'mm/dd')
            else:
                day = list(day_set)[d]
            

            #data going in the table
            datarow.append ([list2str(genotype_set), day, list2str(mon_set) , 'all',
                             num_flies, num_alive,
                             total_sleep, std_total_sleep,
                             day_sleep , std_day_sleep,
                             night_sleep,  std_night_sleep,
                             AI, std_AI])



        pos = GUI['currentlyDrawn']
    
        if holdplot:
            for i in range (0,len(datarow)):
                color, color_name = getPlottingColor(pos-1)
                datarow[i].append(color_name)
                self.sheet.AddRow(datarow[i])
        else:
            color, color_name = getPlottingColor(pos-1)
            for i in range (0,len(datarow)): datarow[i].append(color_name)
            self.sheet.SetData (datarow)
    
        if num_of_selected==1:
            title = list2str(genotype_set) + ' - Mon: ' +list2str(mon_set)+ ', Ch. '+list2str(ch_set)
        else:
            title = 'Multiple Selection'


        #data to be plotted
        days_avg = average(s30, axis=1)
        days_std = stde(s30, axis=1)
        act_avg = average(ax, axis=1)

        size = self.GetCanvasSize()
        self.SetCanvasSize((size[0]*1.5, 1.2*len(days_avg)))
        
        self.canvas.redraw(self.subplot_daybyday, title, days_avg , days_std, act_avg, GUI['ErrorBar'], color )
        self.WriteComment(cSEL.Comment or '')

    
    def subplot_daybyday(self, fig, title, days, days_std, act_avg, errBars, col):
        '''
        TODO: change all the 1440 to custom values.
        '''
    
        a = ['']*len(days)
        b = ['']*len(days)
    
        sz = (len(days) > 4 )*len(days) or 5
    
        activity_limit = self.GetOption('Yactivity')
        if activity_limit == 'Max (dynamic)': 
            activity_limit = -1
        else:
            activity_limit = int(activity_limit)
    
    
        for i in range (len(days)): #two plots per row
            if i == 0: 
                a[i] = fig.add_subplot(sz, 2, (i*2)+1) #first plot (do not share axes)
                b[i] = fig.add_subplot(sz, 2, (i*2)+2)
            else:
                 a[i] = fig.add_subplot(sz, 2, (i*2)+1, sharex = a[0]) #next plots - do share axes
                 b[i] = fig.add_subplot(sz, 2, (i*2)+2, sharex = b[0])
    
            a[i].plot(days[i], color = col)
            if errBars: a[i].errorbar(range(0,len(days[i]),30), days[i][::30], days_std[i][::30]/2, ecolor=col, fmt=None )
    
            a[i].set_ylim((0, 30))
            mpl.artist.setp( a[i].get_xticklabels(), visible=False)
    
            b[i].plot(act_avg[i], color = col)
            #b[i].set_ylim((0))
            mpl.artist.setp( b[i].get_xticklabels(), visible=False)
    
        a[0].set_xlim((0, 1440))
        b[0].set_xlim((0, 1440))
        a[0].set_title(title)
    
        a[len(days)/2].set_ylabel('Sleep for 30 min')
        a[-1].set_xlabel('Zeitgeber (H)')
        a[-1].set_xticks(range(0, 1440+1, 180))
        a[-1].set_xticklabels(range(0,25,3))
        mpl.artist.setp( a[-1].get_xticklabels(), visible=True)
    
