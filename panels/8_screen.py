'''
This Panel will plot in a distribution the values of sleep, AI, brief awakening and more
taking them from ALL the flies in the selection tree, including ALL genotype.

It was custom made for Daniel Bushey for screening purposes.

'''

from default_panels import *

class Panel(PlotGrid): #Class name must be Panel

    def __init__(self, parent):

    #Here some variable specific to the PanelType

        PanelProportion = [6,2,1]

        CanvasInitialSize = (-1,-1)# size in inches or userDefined (-1,-1)

        colLabels = ['Genotype','Mon','Ch','alive','sleep TD','st.dv.','sleep RD','st.dv.','sleep RN','st.dv.','AI','st.dv','BA','st.dv.']
        dataTypes = [gridlib.GRID_VALUE_STRING] * 3 + [gridlib.GRID_VALUE_NUMBER] *1 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * 10

        choiceList = ['sleep TD','sleep RD','sleep RN']

        PlotGrid.__init__(self, parent,
                                         PanelProportion,
                                         CanvasInitialSize,
                                         colLabels,
                                         dataTypes,
                                         choiceList
                                         )
        self.name = 'Screen'
        self.compatible = '0.9.1'
        
        self.AddOption('use_first_day', 'boolean', 1, ['Use first day', 'Do not use first day'], 'Do you want to include data from the first day?')


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
        headers = []
        for k, cSEL in enumerate(cDAM):
            fs, fe = 0, -1 #it takes all flies
            
            use_first_day = self.GetOption('use_first_day')
            if use_first_day:
                ds, de = 0, -1 #it takes all days but the first one
            else:
                ds, de = 1, -1 #it takes all days but the first one
                
            m = -1 #takes all monitors
            ax_t, s5_t, s30_t = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1, status=5, use_dropout=use_dropout, min_alive=min_alive, max_alive=max_alive) 

            n_flies = ax_t.shape[1]
            for fly in range(n_flies):
                genotype = cSEL.getGenotype()
                mon, ch = cSEL.getMonitorFlyName(fly)
                headers.append([genotype, mon, ch])
    
            if k == 0:
                s5 = s5_t
                ax = ax_t
                s30 = s30_t
            else:
                s5 = concatenate ((s5, s5_t), axis=1)
                ax = concatenate ((ax, ax_t), axis=1)
                s30 = concatenate ((s30, s30_t), axis=1)

        # at the end of this loop we have the 3 basic arrays: s5, ax, s30
        dist_tot_sleep_by_fly = average ( s5[:,:,t0:t1].sum(axis=2), axis=0)
        dist_std_tot_sleep_by_fly = cStd ( s5[:,:,t0:t1].sum(axis=2), axis=0)
        dist_day_sleep_by_fly = average( s5[:,:,0:720].sum(axis=2), axis=0)
        dist_std_day_sleep_by_fly = cStd( s5[:,:,0:720].sum(axis=2), axis=0)
        dist_night_sleep_by_fly = average( s5[:,:,720:1440].sum(axis=2), axis=0)
        dist_std_night_sleep_by_fly = cStd( s5[:,:,720:1440].sum(axis=2), axis=0)
        dist_AI_by_fly = average (ActivityIndexByFly(ax, s5, t0, t1), axis=0)
        dist_std_AI_by_fly = cStd (ActivityIndexByFly(ax, s5, t0, t1), axis=0)
        dist_BA_by_fly = average ( ba(s5[:,:,t0:t1]).sum(axis=2), axis=0)  
        dist_std_BA_by_fly = cStd ( ba(s5[:,:,t0:t1]).sum(axis=2), axis=0)  

        # we now calculate the data to be placed in the table
        # Single number averages of all flies and their standard deviations
        if len(self.sheet.GetData()) <= 1:
            self.sheet.SetData ([])

            datarow = []
            for fly, heads in enumerate(headers):
                datarow.append([])
                genotype, mon, ch = heads
                tot_sleep = dist_tot_sleep_by_fly[fly]; std_tot_sleep = dist_std_tot_sleep_by_fly[fly]
                alive = tot_sleep>0
    
                day_sleep = dist_day_sleep_by_fly[fly]; std_day_sleep = dist_std_day_sleep_by_fly[fly]
                night_sleep = dist_night_sleep_by_fly[fly];std_night_sleep = dist_std_night_sleep_by_fly[fly]
                AI = dist_AI_by_fly[fly]; std_AI = dist_std_AI_by_fly[fly]
                BA = dist_BA_by_fly[fly]; std_BA = dist_std_BA_by_fly[fly]
                
                datarow[-1] = [genotype,
                           mon,
                           ch,
                           alive,
                           tot_sleep, std_tot_sleep,
                           day_sleep, std_day_sleep,
                           night_sleep, std_night_sleep,
                           AI, std_AI,
                           BA, std_BA]
    
            self.sheet.SetData (datarow)
        
            
        #Here we select what we have to mark blue in the distribution
        for n_sel, selection in enumerate(allSelections): #every selection carries a 5 digits coordinate
            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]
            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)
            ax, s5, s30 = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1, status=5, use_dropout=use_dropout, min_alive=min_alive, max_alive=max_alive)  #get the S5 of the currently selected item
            selected_sleep = average ( s5[:,:,t0:t1].sum(axis=2))
            selected_ai = average (ActivityIndexByFly(ax, s5, t0, t1))


        #Here we pass the data according to what the selection was
        if GUI['choice'] == 'sleep TD':
            dist_sleep = dist_tot_sleep_by_fly
        elif GUI['choice'] == 'sleep RD':
            dist_sleep =  dist_day_sleep_by_fly
        elif GUI['choice'] == 'sleep RN':
            dist_sleep =  dist_night_sleep_by_fly

        dist_AI = dist_AI_by_fly
        dist_nSE = 0
        
        self.canvas.redraw(self.plot_distributions, selected_sleep, dist_sleep, selected_ai, dist_AI, dist_nSE)


        self.WriteComment(cSEL.Comment or '')


    def plot_distributions(self, fig, selected_sleep, dist_sleep, selected_ai, dist_AI, dist_nSE):
        '''
        '''
        def find_bin_bounds(bins, x):
            bins = list(bins)
            bins.append(x); bins.sort(); 
            i = bins.index(x)
            return [bins[i-1], bins[i+1]]


        color, color_name = getPlottingColor(0)
        color1, color_name = getPlottingColor(1)
            
        n_bin = len(dist_sleep)/2
        a1 = fig.add_subplot(321)
        a1.set_title('Sleep distribution')
        n, bins, patches = a1.hist(dist_sleep, n_bin , rwidth=1, fc = color, alpha=0.5)
        bb = find_bin_bounds(bins, selected_sleep)
        n1, bins1, patches1 = a1.hist(bb, 1 , rwidth = 1, fc = color1)
        a1.set_ylabel('n. of flies')
        a1.set_xlim((0, 1440))
        a1.set_ylim(min(n)*1.1, max(n)*1.1)


        n_bin = len(dist_AI)/2
        a2 = fig.add_subplot(322)
        a2.set_title('AI distribution')
        n, bins, patches = a2.hist(dist_AI, n_bin , rwidth=1, fc = color, alpha=0.5)
        bb = find_bin_bounds(bins, selected_ai)
        n1, bins1, patches1 = a2.hist(bb, 1 , rwidth = 1, fc = color1)
        a2.set_ylabel('n. of flies')
        a2.set_ylim(min(n)*1.1, max(n)*1.1)

    
