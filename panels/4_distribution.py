'''
-
'''
#Default IMPORTED MODULES (DO NOT REMOVE)
from default_panels import *


class Panel(PlotGrid):

    #Here some variable specific to the PanelType

    def __init__(self, parent):

        PanelProportion = [6,2,1]    #0 = not_show
        CanvasInitialSize = (10,6)     #size in inches

        colLabels = ['Genotype','Day','Mon','Ch','n(tot)','n(a)','sleep TD','st.dv.','sleep RD','st.dv.','sleep RN','st.dv.','AI','st.dv','color' ]
        dataTypes = [gridlib.GRID_VALUE_STRING] * 4 + [gridlib.GRID_VALUE_NUMBER] *2 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * 8 + [gridlib.GRID_VALUE_STRING]

        choiceList = ['sleep TD','sleep RD','sleep RN','AI']

        PlotGrid.__init__(self, parent,
                                         PanelProportion,
                                         CanvasInitialSize,
                                         colLabels,
                                         dataTypes,
                                         choiceList)
        self.name = 'Distribution'
        self.compatible = 'all'

#-----------------------------------------------

    def Refresh(self):
        '''
        This function takes the coordinates coming upon tree item selection
        and plots the data
        '''

        allSelections = GUI['dtList']
        cDAM = GUI['cDAM']
        holdplot = GUI['holdplot']
        num_of_selected = GUI['num_selected']
        pos = GUI['currentlyDrawn']

        flies = []
        value_dist, value_std = [], []
        genotype_set, day_set, mon_set, ch_set = set ([]), set ([]), set ([]), set([])

        #get start and end value in the limit subpanel
        t0, t1 = self.limits.isActive() * self.limits.GetVals() or (None, None)

        for n_sel, selection in enumerate(allSelections): #every selection carries a 5 digits coordinate 

            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]

            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)

            genotype_set.add ( cSEL.getGenotype() )
            mon_t = cSEL.getMonitorName(m, d, f) or 'All' ; mon_set.add (mon_t)
            day_t = cSEL.getDate(d, f) or 'All' ; day_set.add (day_t)
            ch_t = cSEL.getChannelName(m, f) or 'All' ; ch_set.add (ch_t)
            # take the 3D arrays for
            ax_t, s5_t = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1)[0:2]  #get the S5 of the currently selected item

            if n_sel == 0:
                s5 = s5_t
                ax = ax_t
            else:
                s5 = concatenate ((s5, s5_t), axis=1)
                ax = concatenate ((ax, ax_t), axis=1)

            
        ## OUT OF THE LOOP HERE
        # Here we are, out of the selection cycle
        num_flies = s5.shape[1]
        num_alive = (s5.sum(axis=2)<1430).all(axis=0).sum() 
        dist_tot_sleep_by_fly = average(SleepAmountByFly (s5), axis=0)
        dist_day_sleep_by_fly = average(SleepAmountByFly (s5, t0=0, t1=720), axis=0)
        dist_night_sleep_by_fly = average(SleepAmountByFly (s5, t0=720, t1=1440), axis=0)
        dist_AI_by_fly = average(ActivityIndexByFly(ax, s5), axis=0)
        # we now calculate the data to be placed in the table
        # Single number averages of all flies and their standard deviations
        datarow = [list2str(genotype_set),
                     list2str(day_set) ,
                     list2str(mon_set),
                     list2str(ch_set),
                     num_flies, num_alive,
                     average(dist_tot_sleep_by_fly, axis=0), std(dist_tot_sleep_by_fly, axis=0),
                     average(dist_day_sleep_by_fly, axis=0), std(dist_day_sleep_by_fly, axis=0),
                     average(dist_night_sleep_by_fly, axis=0), std(dist_night_sleep_by_fly, axis=0),
                     average(dist_AI_by_fly, axis=0), std(dist_AI_by_fly, axis=0)]

        #HOLD vs. NO-HOLD
        #Do we add the current line to the table or we completely refresh the contents?
        if holdplot:
            color, color_name = getPlottingColor(pos-1)
            datarow.append(color_name)
            self.sheet.AddRow (datarow)
            title = 'Multiple Selection'
        else:
            color, color_name = getPlottingColor(pos-1)
            datarow.append(color_name)
            self.sheet.SetData ([datarow])

        #Here we pass the data according to what the selection was
        if GUI['choice'] == 'sleep TD':
            value_dist =  dist_tot_sleep_by_fly
            value_std  =  std(dist_tot_sleep_by_fly)
        elif GUI['choice'] == 'sleep RD':
            value_dist=  dist_day_sleep_by_fly
            value_std =  std(dist_day_sleep_by_fly)
        elif GUI['choice'] == 'sleep RN':
            value_dist=  dist_night_sleep_by_fly
            value_std =  std(dist_night_sleep_by_fly)
        elif GUI['choice'] == 'AI':
            value_dist=  dist_AI_by_fly
            value_std =  std(dist_AI_by_fly)

        title = list2str(genotype_set) +' - Day: '+ list2str(day_set) +', Mon: ' +list2str(mon_set)+ ', Ch. '+list2str(ch_set)

        self.canvas.redraw(subplot_distribution, title, value_dist, value_std, pos, color)
        self.WriteComment(cSEL.Comment or '')


def subplot_distribution(fig, title, value_dist, value_std, pos=1, col=None):
    '''
    Will plot a distribution in two formats: bins and candles
    '''

    #This in case the data we are passing are actually empty (flies are inactive or dead).
    if not (isAllMasked(value_dist) or hasNaN(value_dist)):

        n_bin = len(value_dist)/2

        a1 = fig.add_subplot(311)
        try:
            a1.boxplot(value_dist, positions=[pos])
        except:
            a1.boxplot(value_dist.compressed(), positions=[pos])

        a1.set_xticks(range(1,pos+1))
        a1.set_xticklabels(range(1,pos+1))
        a1.set_xlim((0, pos+1))
        a1.set_title(title)

        a2 = fig.add_subplot(312)
        w = 1
        n, bins, patches = a2.hist(value_dist.compressed(), n_bin , rwidth=w, fc = col, alpha=0.5)
        a2.set_ylabel('n. of flies')
        a2.set_xlim((0, 1440))
        a2.set_ylim(min(n)*1.1, max(n)*1.1)

        a3 = fig.add_subplot(313, sharex=a2)
        mu = average (value_dist)
        y = mpl.mlab.normpdf( bins , mu, value_std) #normal probability dension function in the mlab submodule
        a3.plot(bins, y, color=col)
        a3.set_xlabel('sleep (m/d)')
        a3.set_yticklabels([])


