'''
This Panel analyzes the sleep deprivation data of a fly population.
The upper graph shows the distribution of sleep deprivation efficiency among the population: lightly colored bars on the left indicate the flies
that do not reach the desired threshold (specified in the options)
The lower left graph shows the sleep rebound in minutes, the lower middle graph shows sleep rebound in %
the lower right graph plots the ration between sleep deprivation efficiency and sleep rebound in %.
'''
#Default IMPORTED MODULES (DO NOT REMOVE)
from default_panels import *

class Panel(PlotGrid):

    #Here some variable specific to the PanelType

    def __init__(self, parent):

        PanelProportion = [6,2,1]    #0 = not_show
        CanvasInitialSize = (10,6)     #size in inches
        colLabels = ['Genotype','Day','Mon','Ch','n(tot)','n(a)', 'eff(%)','n(dep)' ,'rebound','st.dv.','sleep diff.','st.dv.','SD efficacy','st.dv.','color' ]
        dataTypes = [gridlib.GRID_VALUE_STRING] * 5 + [gridlib.GRID_VALUE_NUMBER] * 3 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * 6 + [gridlib.GRID_VALUE_STRING]

        choiceList = ['rebound TD', 'rebound 0-3H', 'rebound 0-6H', 'rebound 0-9H', 'rebound RD', 'rebound RN']

        PlotGrid.__init__(self, parent,
                                         PanelProportion,
                                         CanvasInitialSize,
                                         colLabels,
                                         dataTypes,
                                         choiceList
                                         )
        self.name = 'Sleep Deprivation'
        self.compatible = 'all'

        self.AddOption('dep_thre', 'text', 0, ['80'], 'Utilize only flies that have at least this value of deprivation score (%)' )


#-----------------------------------------------

    def Refresh(self):
        '''
        This function takes the coordinates coming upon tree item selection
        and plot the data as 24h/12h hold/no-hold
        '''

        allSelections = GUI['dtList']
        cDAM = GUI['cDAM']
        ShowErrorBar = GUI['ErrorBar']
        holdplot = GUI['holdplot']
        num_of_selected = GUI['num_selected']

        genotype_set, day_set, mon_set, ch_set = set ([]), set ([]), set ([]), set([])

        if GUI['choice'] == 'rebound 0-3H': tr, tr1 = 1, 180
        elif GUI['choice'] == 'rebound 0-6H': tr, tr1 = 1, 360
        elif GUI['choice'] == 'rebound 0-9H': tr, tr1 = 1, 540
        elif GUI['choice'] == 'rebound TD': tr, tr1 = 1, 1440
        elif GUI['choice'] == 'rebound RD': tr, tr1 = 1, 720
        elif GUI['choice'] == 'rebound RN': tr, tr1 = 721, 1440
        else: tr, tr1 = None, None

        #get start and end value in the limit subpanel
        t0, t1 = self.limits.isActive() * self.limits.GetVals() or (None, None)

        for n_sel, selection in enumerate(allSelections): #every selection carries a 5 digits coordinate

            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]
 
            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)
 
            genotype_set.add ( cSEL.getGenotype() )
            mon_t = cSEL.getMonitorName(m, d, f) or 'All'; mon_set.add(mon_t)
            day_t = cSEL.getDate(d, f) or 'All'; day_set.add(day_t)
            ch_t = cSEL.getChannelName(m, f) or 'All'; ch_set.add(ch_t)
            
            s5_bs_t = cSEL.filterbyStatus(ds,de,fs,fe, status=1)[1] #only baseline days
            s5_sd_t = cSEL.filterbyStatus(ds,de,fs,fe, status=2)[1] #only sleep deprivation days
            s5_re_t = cSEL.filterbyStatus(ds,de,fs,fe, status=3)[1] #only recovery days
            
            if n_sel == 0:
                s5_bs = s5_bs_t
                s5_sd = s5_sd_t
                s5_re = s5_re_t
            else:
                s5_bs = concatenate ((s5_bs, s5_bs_t))
                s5_sd = concatenate ((s5_sd, s5_sd_t))
                s5_re = concatenate ((s5_re, s5_re_t))

                
        # OUT OF THE LOOP HERE    
        # First we calculate the SD efficiency
        bs_sleep = average(SleepAmountByFly (s5_bs, t0=t0, t1=t1), axis=0)
        sd_sleep = average(SleepAmountByFly (s5_sd, t0=t0, t1=t1), axis=0)
        dist_sde = (1.0 - (sd_sleep / bs_sleep)) * 100 # FIRST VALUE TO PLOT
        self.canExport(dist_sde, 'Distribution SD Efficiency', 'The Distribution of Sleep Deprivation efficiency of selected flies')

        # Now we mask all those flies for which eff. was less than the specified value
        min_sde = int(self.GetOption('dep_thre')) # Minimal sleep dep efficiency for flies to be included (%)
        mask_sde = dist_sde < min_sde # this is our mask (1-d array, long as many flies we have)

        #This is what we are going to plot in panel a
        dist_sde_sel = np.ma.masked_array(dist_sde, mask=mask_sde) # dist of only selected (above the threshold)
        dist_sde_rem = np.ma.masked_array(dist_sde, mask= (mask_sde == False)) # dist of only remaining (below the threshold)

        #Now we calculate the gain in minutes for recovery day, only in flies above the threshold
        re_sleep = average(SleepAmountByFly (s5_re, t0=tr, t1=tr1), axis=0)
        bs_sleep = average(SleepAmountByFly (s5_bs, t0=tr, t1=tr1), axis=0)
        dist_re_mins_all = re_sleep - bs_sleep
        dist_re_mins = np.ma.masked_array(dist_re_mins_all, mask=mask_sde) # dist of only selected (above the threshold) Plot in panel b
    
        #Now we calculate the Rebound, meaning the recovery in mins / effective sleep of sd day
        # Rebound = (RE - BS) / (BS - SD)
        bs_all = average(SleepAmountByFly (s5_bs), axis=0)
        sd_all = average(SleepAmountByFly (s5_sd), axis=0)
        dist_rebound_all = ((re_sleep - bs_sleep) / (bs_all - sd_all)) * 100
        dist_rebound = np.ma.masked_array((dist_rebound_all), mask=mask_sde)

        #In the table
        num_flies = s5_bs.shape[1]
        num_alive = (s5_bs.sum(axis=2)<1430).all(axis=0).sum()
        num_dep = num_flies - dist_sde_sel.mask.sum()
        rebound_avg = average(dist_rebound)
        rebound_std = stde(dist_rebound)
        sleep_diff_avg = average(dist_re_mins)
        sleep_diff_std = std(dist_re_mins)
        sde_avg = average(dist_sde_sel)
        sde_std = stde(dist_sde_sel)

        datarow = [list2str(genotype_set), list2str(day_set) , list2str(mon_set), list2str(ch_set), num_flies, num_alive, min_sde, num_dep, rebound_avg, rebound_std, sleep_diff_avg, sleep_diff_std, sde_avg, sde_std]

        #HOLD vs. NO-HOLD
        #Do we add the current line to the table or we completely refresh the contents?

        pos = GUI['currentlyDrawn']
        if holdplot:
            title = 'Multiple Selection'
            color, color_name = getPlottingColor(pos-1)
            datarow.append(color_name)
            self.sheet.AddRow (datarow)
        else:
            title = list2str(genotype_set) +' - Day: '+ list2str(day_set) +', Mon: ' +list2str(mon_set)+ ', Ch. '+list2str(ch_set)
            color, color_name = getPlottingColor(pos-1)
            datarow.append(color_name)
            self.sheet.SetData ([datarow])

        self.canvas.redraw(self.rebound_plot, title, dist_sde_sel.compressed() , dist_sde_rem.compressed(), dist_re_mins, dist_rebound, dist_sde, dist_re_mins_all, pos, color )
        self.WriteComment(cSEL.Comment or '')

    def rebound_plot(self, fig, t, dist_sde_sel , dist_sde_rem, dist_re_mins, dist_rebound, all_sde, all_reb, pos, col ):
        '''
        '''

        #add_axes allow more control on where to place the graphs in the figure
        #the syntax is add_axes([x,y,w,h)) where
        # x and y indicate distance from the bottom left corner (from 0 to 1)
        # w, h are the width and height of the graph (0 to 1, 1 means as big as the whole canvas)
        #
        a1 = fig.add_axes([0.13, 0.55, 0.53, 0.35], title = 'Distribution of sleep deprivation efficiency')
        
        n_bin1 = len(dist_sde_sel)/5 #show 5 flies per bin
        n_bin2 = len(dist_sde_rem)/5 #show 5 flies per bin

        n1 = [0]; n2 = [0]
        w1 = 1        
        if n_bin1: w2 = 1.0/n_bin1
        else: w2 = 0.3
        
        if len(dist_sde_sel) > 1: n1, bins, patches = a1.hist(dist_sde_sel, n_bin1 , rwidth=w1, fc = col)#, alpha=0.5)
        if len(dist_sde_rem) > 1: n2, bins, patches = a1.hist(dist_sde_rem, n_bin2 , rwidth=w2, fc = brighten(col))#, alpha=0.5)
    
        a1.set_ylabel('n. of flies')
        a1.set_xlim((0, 100))
        up_b = np.max(list(n1) + list(n2))
        a1.set_ylim(0, up_b*1.2)
        
        
        a5 = fig.add_axes([0.70, 0.55, 0.20, 0.35])
        n_low_sde_thre = len(dist_sde_rem)
        n_hig_sde_thre = len(dist_sde_sel)

        #if plot_legend:
        b1 = a5.bar(1, n_low_sde_thre, color=brighten(col) , align='center')
        b2 = a5.bar(2, n_hig_sde_thre, color=col , align='center')
        a5.legend( (b1[0], b2[0]), ('<SDE', '>SDE') )

        a5.set_xticks([])
        a5.set_xticklabels([])

        
        
        
        a2 = fig.add_subplot(234, title = 'Avg Recovery (min)')
        pos = pos + 1
        width = float(pos) / (pos*2)    
        
        if GUI['ErrorBar']:
            a2.bar(pos, average(dist_re_mins), width, color=col, yerr=stde(dist_re_mins), ecolor=col, align='center' )
        else:
            a2.bar(pos, average(dist_re_mins), width, color=col , align='center')
    
        a2.set_xticks(range(1,pos+2))
        a2.set_xticklabels(range(0,pos))
        a2.set_xlim(1.5, pos+0.5)
        a2.set_ylabel('Sleep (min)')
    
        a3 = fig.add_subplot(235, title = 'Avg Rebound (%)')
    
    
        if GUI['ErrorBar']:
            a3.bar(pos, average(dist_rebound), width, color=col, yerr=stde(dist_rebound), ecolor=col, align='center' )
        else:
            a3.bar(pos, average(dist_rebound), width, color=col , align='center')
    
        a3.set_xticks(range(1,pos+2))
        a3.set_xticklabels(range(0,pos))
        a3.set_xlim(1.5, pos+0.5)
        a3.set_ylabel('Rebound (%)')

    
        a4 = fig.add_subplot(236, title = 'SDE / Reb')

        if len( dist_sde_sel ) > 0:
            x, y = all_sde, all_reb
            r = np.corrcoef(x,y)
            coeffs = np.polyfit(x,y,1)
            besty = np.polyval(coeffs, x)
            
            a4.plot(x, y, 'o', x, besty, '-', color=col)

