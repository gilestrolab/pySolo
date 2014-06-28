'''
This Panel will take the coordinates of the data coming from the tree selection
and plot the basic sleep data for the 24h: activity pattern, sleep pattern and hypnogram.
The hypnogram should be considered useful only for single flies, not for the entire population.
A lower table reports the basic data about the selected fly(ies).
Multiple selections are possible
'''

from default_panels import *

class Panel(PlotGrid): #Class name must be Panel

    def __init__(self, parent):

    #Here some variable specific to the PanelType

        PanelProportion = [6,2,1]

        CanvasInitialSize = (-1,-1)# size in inches or userDefined (-1,-1)

        colLabels = ['Genotype','Day','Mon','Ch','n(tot)','n(a)','sleep TD','st.dv.','sleep RD','st.dv.','sleep RN','st.dv.','AI','st.dv','color' ]
        dataTypes = [gridlib.GRID_VALUE_STRING] * 4 + [gridlib.GRID_VALUE_NUMBER] *2 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * 8 + [gridlib.GRID_VALUE_STRING]

        PlotGrid.__init__(self, parent,
                                         PanelProportion,
                                         CanvasInitialSize,
                                         colLabels,
                                         dataTypes,
                                         #choiceList
                                         )
        self.name = 'Browser'
        self.compatible = 'all'


        self.AddOption('use_grid', 'boolean', 1, ['Draw grid', 'Do not draw grid'], 'Do you want to draw a cartesian grid in the graph?')
        self.AddOption('zeitgeber', 'radio', 0, ['Hours', 'Minutes'], 'Would you like to indicate the zeitgeber in hours or minutes?')
        self.AddOption('invertlight', 'boolean', 1, ['Night First', 'Day First'], 'How do you want to plot the light cycle.')
        self.AddOption('Yactivity', 'radio', 0, ['Normalized','Max (dynamic)', '15', '10', '5'], 'Set the upper limit for the Y axis on the Activity plot')
        self.AddOption('sync_graphs', 'boolean', 0, ['Sync', 'Do not Sync'], 'Do you want to sync the coordinates on all graphs?\ni.e.: when you zoom in one, the others are zoomed accordingly')
        self.AddOption('sleep_y_limit', 'text', 0, ['30'], 'Set the upper limit for the Y axis on the Sleep plot')
        self.AddOption('show_error', 'radio', 2, ['Only above', 'Only below', 'Both sides'], 'On what sides do we want to show the error bar?')
        self.AddOption('activity_bin', 'radio', 0, ['1', '5', '10', '15', '30', '60'], 'Plot activity in bin count of n minutes')
        self.AddOption('show_hypno_group', 'boolean', 1, ['Show always', 'Show only on single flies'], 'When do you want to show the hypnogram?')



    def Refresh(self):
        '''
        This function takes the coordinates coming upon tree item selection
        and plot the data as 24h/12h hold/no-hold
        '''
        allSelections = GUI['dtList'] #list of lists - all the coordinates of all the selected tree items
        num_of_selected = GUI['num_selected'] #int - how many selections we are dealing with?

        cDAM = GUI['cDAM'] #list of DAMslices - the currenlty selected DAMslice(s)
        ShowErrorBar = GUI['ErrorBar'] #boolean - are we showing errorbars?

        holdplot = GUI['holdplot'] #boolean - are we adding a new selection on top of a previous one?
        pos = GUI['currentlyDrawn'] #int - if yes, which one
        
        use_dropout = userConfig['use_dropout'] #boolean
        min_alive = userConfig['min_sleep'] #int
        max_alive = userConfig['max_sleep'] #int
        use_std = userConfig['use_std'] #boolean, if False we should use stde
        if use_std: cStd = std
        else: cStd = stde 

        #get start and end value in the limit subpanel
        t0, t1 = self.limits.isActive() * self.limits.GetVals() or (None, None)

        #start setting some variable that we are going to use later
        genotype_set, day_set, mon_set, ch_set = set ([]), set ([]), set ([]), set([])

        #for each one of the selection we want to pull togheter
        for n_sel, selection in enumerate(allSelections): #every selection carries a 5 digits coordinate

            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]

            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)

            # translate tree coordinates to flies and days of current DAM
            genotype_set.add ( cSEL.getGenotype() )
            mon_t = cSEL.getMonitorName(m, d, f) or 'All'; mon_set.add(mon_t)
            day_t = cSEL.getDate(d, f) or 'All'; day_set.add(day_t)
            ch_t = cSEL.getChannelName(m, f) or 'All'; ch_set.add(ch_t)

            # take the 3D arrays for
            # ax -> fly activity (the raw data of beam crossing)
            # s5 -> the 5mins sleep bins
            # s30 -> the sleep for 30 mins across the day
            ax_t, s5_t, s30_t = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1, status=5, use_dropout=use_dropout, min_alive=min_alive, max_alive=max_alive)  #get the S5 of the currently selected item

            if n_sel == 0:
                s5 = s5_t
                ax = ax_t
                s30 = s30_t
            else:
                s5 = concatenate ((s5, s5_t))
                ax = concatenate ((ax, ax_t))
                s30 = concatenate ((s30, s30_t))
        
        ## HERE WE ARE OUT OF THE SELECTION LOOP
        # we calculate date by fly
        num_flies = s5.shape[1]
        num_alive = (s5.sum(axis=2)<1430).all(axis=0).sum()
        dist_tot_sleep_by_fly = average ( s5[:,:,t0:t1].sum(axis=2), axis=0)
        dist_day_sleep_by_fly = average( s5[:,:,0:720].sum(axis=2), axis=0)
        dist_night_sleep_by_fly = average( s5[:,:,720:1440].sum(axis=2), axis=0)
        dist_AI_by_fly = average (ActivityIndexByFly(ax, s5, t0, t1), axis=0)
        # we now calculate the data to be placed in the table
        # Single number averages of all flies and their standard deviations
        datarow = [list2str(genotype_set),
                     list2str(day_set) ,
                     list2str(mon_set),
                     list2str(ch_set),
                     num_flies, num_alive,
                     average( dist_tot_sleep_by_fly), cStd( dist_tot_sleep_by_fly),
                     average( dist_day_sleep_by_fly), cStd( dist_day_sleep_by_fly),
                     average( dist_night_sleep_by_fly), cStd( dist_night_sleep_by_fly),
                     average( dist_AI_by_fly), cStd( dist_AI_by_fly)]
        #here we decide what to do with the table data.
        #Do we add the current line to the table or we completely refresh the contents?
        if holdplot:
            color, color_name = getPlottingColor(pos-1)
            datarow.append(color_name)
            self.sheet.AddRow (datarow)
        else:
            color, color_name = getPlottingColor(pos-1)
            datarow.append(color_name)
            self.sheet.SetData ([datarow])
        # Finally, we calculate the data to be drawn on the graph

        
        activity_bin = int( self.GetOption('activity_bin') ) # 1,5,10,15,30,60 minutes
        
        if activity_bin > 1:
            d,f,t = ax.shape
            activity = ax.reshape((d,f,-1,activity_bin)).sum(axis=3)
            fly_activity = average (average (activity, axis=0), axis=0)
            fly_activity_std = cStd (average (activity, axis=0), axis=0)
    
        else:
            fly_activity = average (average (ax, axis=0), axis=0)
            fly_activity_std = cStd (average (ax, axis=0), axis=0)
            
        dist_fly30 = average (average (s30, axis=0), axis=0)
        stde_fly30 = cStd (average (s30, axis=0), axis=0)
        
        # We set the title of the whole thing
        if num_of_selected > 1 or holdplot:
            title = 'Multiple Selection'
        else:
            title = list2str(genotype_set) +' - Day: '+ list2str(day_set) +', Mon: ' +list2str(mon_set)+ ', Ch. '+list2str(ch_set)
        # We Draw what we need to
        self.canvas.redraw(self.subplot_dailydata, title, str(genotype_set),
                           fly_activity, fly_activity_std, dist_fly30, stde_fly30,
                           ShowErrorBar, num_flies, col=color)

        self.WriteComment(cSEL.Comment or '')


    def subplot_dailydata(self, fig, title, lbl, activity, activity_std, sleep, sleep_std, errBars, num_flies, col=None):

        #This in case the data we are passing are actually empty (flies are inactive or dead).
        #Here we determine the length of a day to be able to fill things

        #recall values of panel specific options
        use_grid = self.GetOption('use_grid')
        zeitgeber = self.GetOption('zeitgeber')
        invertlight = self.GetOption('invertlight')
        sync = self.GetOption('sync_graphs')
        sleep_lim = int(self.GetOption('sleep_y_limit'))
        error_direction = self.GetOption('show_error')
        activity_bin = int( self.GetOption('activity_bin') ) # 1,5,10,15,30,60 minutes
        activity_limit = self.GetOption('Yactivity')
        show_hypno_group = self.GetOption('show_hypno_group')
        
        try:
            DayLength = len(sleep)
        except:
            DayLength = 1440

        if isAllMasked(activity) or hasNaN(activity):
            activity = [0]*DayLength
            sleep = [0]*DayLength
            sleep_std = [0]*(DayLength/30)
            title = title + ' - Inactive or dead'

        #add_axes allow more control than add_subplot on where to place the graphs in the figure
        #the syntax is add_axes([x,y,w,h)) where
        # x and y indicate distance from the bottom left corner (from 0 to 1)
        # w, h are the width and height of the graph (0 to 1, 1 means as big as the whole canvas)
        #
        lm = 0.08 ; rm = 0.9
        a4 = fig.add_axes([lm, 0.08, rm, 0.03], yticks=[])

        #Draw the light/dark bar at the very bottom
        
        if invertlight:
                light_pattern = [[1]*(DayLength/2)+[0]*(DayLength/2),]
        else:
                light_pattern = [[0]*(DayLength/2)+[1]*(DayLength/2),]
                
        a4.imshow(light_pattern, aspect='auto', cmap=mpl.cm.binary, interpolation='nearest')

        if zeitgeber == 'Minutes':
            a4.set_xlabel('Zeitgeber (min)')
            a4.set_xticks(range(0, DayLength+1, DayLength/8))
            a4.set_xticklabels(range(0,DayLength,DayLength/8))

        elif zeitgeber == 'Hours':
            a4.set_xlabel('Zeitgeber (H)')
            a4.set_xticks(range(0, DayLength+1, DayLength/8))
            a4.set_xticklabels(range(0,25,3))

        #Draw the hypnogram at the bottom of the figure and the axis labels
        if show_hypno_group or num_flies == 1:

            ipno = np.zeros(DayLength)
            indices = np.where(activity < 1)
            ipno[indices] = 1
            ipno = ipno,
            
            if sync: a3 = fig.add_axes([lm, 0.12, rm, 0.1], yticks=[], sharex=a4)
            else: a3 = fig.add_axes([lm, 0.12, rm, 0.1], yticks=[])
                

            a3.imshow(ipno, aspect='auto', cmap=mpl.cm.binary, interpolation='nearest')
            mpl.artist.setp( a3.get_xticklabels(), visible=False)

        #Draw the Activity plot
        if sync: a1 = fig.add_axes([lm, 0.60, rm, 0.3], sharex=a4)
        else:  a1 = fig.add_axes([lm, 0.60, rm, 0.3])

        if activity_limit == 'Normalized': activity = activity / np.mean(activity)

        if activity_bin > 1:
            pos = range(0,DayLength,activity_bin)
            
            if errBars: a1.bar(pos, activity, color=col, width=activity_bin, alpha=0.65, yerr=activity_std, ecolor=col)
            else: a1.bar(pos, activity, color=col, width=activity_bin, alpha=0.65)
        
        else:
            a1.plot(activity, color=col)
        
        a1.grid(use_grid)
        a1.set_title(title)
        a1.set_ylabel('Activity Plot')
        a1.set_xlim((0, len(activity)))

        if activity_limit != 'Max (dynamic)' and activity_limit != 'Normalized':
            activity_limit = int(activity_limit)
            a1.set_ylim((0, activity_limit))

        mpl.artist.setp( a1.get_xticklabels(), visible=False)


        #Draw the daily sleep graph
        if sync: a2 = fig.add_axes([lm, 0.25, rm, 0.3], sharex=a4)
        else: a2 = fig.add_axes([lm, 0.25, rm, 0.3])
        
        a2.plot(sleep, color=col)

        if error_direction == 'Only above':
            error = [sleep_std[::30]*0,sleep_std[::30]]
        elif error_direction == 'Only below':
            error = [sleep_std[::30],sleep_std[::30]*0]
        else:
            error = sleep_std[::30]

        if errBars: a2.errorbar(range(0,len(sleep),30), sleep[::30], error, ecolor=col, fmt=None)
        a2.grid(use_grid)
        a2.set_ylabel('Sleep for 30 min')
        a2.set_xlim((0, len(sleep)))
        a2.set_ylim((0, sleep_lim))
        mpl.artist.setp(a2.get_xticklabels(), visible=False)

