'''
'''
#Default IMPORTED MODULES (DO NOT REMOVE)
from default_panels import *

###Additional IMPORTED MODULES
##import wx.grid as gridlib
##from pylab import *

class Panel(PlotGrid):

    #Here some variable specific to the PanelType

    def __init__(self, parent):

        PanelProportion = [6,2,1]    #0 = not_show
        CanvasInitialSize = (10,6)     #size in inches

        colLabels = ['Genotype', 'Day', 'Mon', 'Ch', 'N' ,'alive', 'totSleep', 'SD', 'rDS', 'SD', 'rNS', 'SD', 'AI', 'SD', 'rD aLSE', 'SD', 'rD aNSE', 'SD','rN aLSE', 'SD', 'rN aNSE', 'SD','aLoSE', 'latency', 'SD', 'color']
        dataTypes = [gridlib.GRID_VALUE_STRING] * 4 + [gridlib.GRID_VALUE_NUMBER] *2 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * 19 + [gridlib.GRID_VALUE_STRING]

        PlotGrid.__init__(self, parent,
                                         PanelProportion,
                                         CanvasInitialSize,
                                         colLabels,
                                         dataTypes
                                         #choiceList
                                         )
        self.name = 'Sleep Episodes'
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

        flies = []
        value_dist, value_std = [], []
        genotype_set, day_set, mon_set, ch_set = set ([]), set ([]), set ([]), set([])
        #get start and end value in the limit subpanel
        t0, t1 = self.limits.isActive() * self.limits.GetVals() or (None, None)

        for n_sel, selection in enumerate(allSelections): #every selection carries a 5 digits coordinate 

            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]

            genotype_set.add ( cSEL.getGenotype() )
            mon_t = cSEL.getMonitorName(m, d, f) or 'All'; mon_set.add (mon_t)
            day_t = cSEL.getDate(d, f) or 'All'; day_set.add (day_t)
            ch_t = cSEL.getChannelName(m, f) or 'All'; ch_set.add (ch_t)

            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)

            ax_t, s5_t = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1)[0:2]  #get the S5 of the currently selected item

            if n_sel == 0:
                s5 = s5_t
                ax = ax_t
            else:
                s5 = concatenate ((s5, s5_t), axis=0)
                ax = concatenate ((ax, ax_t), axis=0)

        num_flies = s5.shape[1]
        num_alive = (s5.sum(axis=2)<1430).all(axis=0).sum() 
        dist_tot_sleep_by_fly = SleepAmountByFly (s5)
        dist_day_sleep_by_fly = SleepAmountByFly (s5, t0=0, t1=720)
        dist_night_sleep_by_fly = SleepAmountByFly (s5, t0=720, t1=1440)
        dist_AI_by_fly = ActivityIndexByFly(ax, s5)
   
        len_sleep_episodes_day = all_sleep_episodes (s5, 0, 720)
        len_sleep_episodes_night = all_sleep_episodes (s5, 721, 1440)
        num_sleep_episodes_day = number_sleep_episodes (s5, 0, 720)
        num_sleep_episodes_night = number_sleep_episodes (s5, 721, 1440)
        latency = sleep_latency(s5, 720)

        longest_sleep_episode = max( len_sleep_episodes_night )
        frag_factor = 1
        
        #print len_sleep_episodes_day, len_sleep_episodes_night#, longest_sleep_episode


        datarow = [list2str(genotype_set), list2str(day_set) ,
                   list2str(mon_set), list2str(ch_set),
                   num_flies, num_alive,
                   average(dist_tot_sleep_by_fly), std(dist_tot_sleep_by_fly),
                   average(dist_day_sleep_by_fly), std(dist_day_sleep_by_fly) ,
                   average(dist_night_sleep_by_fly), std(dist_night_sleep_by_fly) ,
                   average(dist_AI_by_fly), std(dist_AI_by_fly) ,
                   average( len_sleep_episodes_day ),
                   std( len_sleep_episodes_day ),
                   average( num_sleep_episodes_day ),
                   std( average( num_sleep_episodes_day, axis=0 ) ),
                   average( len_sleep_episodes_night ),
                   std( len_sleep_episodes_night ),
                   average( num_sleep_episodes_night ),
                   std( average( num_sleep_episodes_night, axis=0 ) ),
                   average( longest_sleep_episode ),
                   average(latency),
                   std(latency)]

        pos = GUI['currentlyDrawn']

        if GUI['holdplot']:
            color, color_name = getPlottingColor(pos-1)
            datarow.append(color_name)
            self.sheet.AddRow(datarow)
        else:
            color, color_name = getPlottingColor(pos-1)
            datarow.append(color_name)
            self.sheet.SetData([datarow])

        title = 'title'
        self.canvas.redraw(plot_episodes, title, len_sleep_episodes_day, len_sleep_episodes_night, num_sleep_episodes_day, num_sleep_episodes_night, longest_sleep_episode, frag_factor, latency, pos, color )




def plot_episodes(fig, title, lse_day, lse_night, nse_day, nse_night, longest_episode, ff_dist, latency, pos, col):

    lse_avg_day = average(lse_day)
    lse_avg_night = average(lse_night)
    long_avg_night = average(longest_episode)
    ff = average(ff_dist)
    
    # . . .
    # x . .
    a1 = fig.add_subplot(234, title = 'Length of SE (day)')
    pos = pos + 1
    width = float(pos) / (pos*2)
    if GUI['ErrorBar']:
        a1.bar(pos, lse_avg_day, width, color=col, yerr=std(lse_day), ecolor=col, align='center' )
    else:
        a1.bar(pos, lse_avg_day, width, color=col , align='center')

    a1.set_xticks(range(1,pos+2))
    a1.set_xticklabels(range(0,pos))
    a1.set_xlim(1.5, pos+0.5)
    a1.set_ylabel('Sleep (m)')

    # . . .
    # . x .

    a2 = fig.add_subplot(235, sharey=a1, title = 'Length of SE (night)')
    width = float(pos) / (pos*2)

    if GUI['ErrorBar']:
        a2.bar(pos, lse_avg_night, width, color=col, yerr=std(lse_night), ecolor=col, align='center' )
    else:
        a2.bar(pos, lse_avg_night, width, color=col , align='center')

    a2.set_xticks(range(1,pos+2))
    a2.set_xticklabels(range(0,pos))
    a2.set_xlim(1.5, pos+0.5)
    a2.set_ylim(0,720)

    # . x .
    # . . .

    a3 = fig.add_subplot(232, title = 'Number of SE (n/d)')
    width = float(pos) / (pos*2)
    col_brighter = brighten(col)

    sf_nse_night = average(nse_night, axis=0)
    sf_nse_day = average(nse_day, axis=0)

    if GUI['ErrorBar']:
        p1 = a3.bar(pos, average(sf_nse_night), width, color=col, yerr=std(sf_nse_night), ecolor=col, align='center' )
        p2 = a3.bar(pos, average(sf_nse_day), width, color=col_brighter, bottom=average(sf_nse_night), yerr=std(sf_nse_day), ecolor=col, align='center' )
    else:
        p1 = a3.bar(pos, average(sf_nse_night), width, color=col, ecolor=col, align='center' )
        p2 = a3.bar(pos, average(sf_nse_day), width, color=col_brighter, bottom=average(sf_nse_night), align='center')


    a3.set_xticks(range(1,pos+2))
    a3.set_xticklabels(range(0,pos))
    a3.set_xlim(1.5, pos+0.5)
    #a3.set_ylim(0,720)

    # x . .
    # . . .
    a4 = fig.add_subplot(231, title = 'Longest SE')
    width = float(pos) / (pos*2)

    if GUI['ErrorBar']:
        a4.bar(pos, long_avg_night, width, color=col, yerr=std(longest_episode), ecolor=col, align='center' )
    else:
        a4.bar(pos, long_avg_night, width, color=col , align='center')

    a4.set_xticks(range(1,pos+2))
    a4.set_xticklabels(range(0,pos))
    a4.set_xlim(1.5, pos+0.5)
    #if lse_avg_night > 3: a4.set_ylim(0,120)

    # . . x
    # . . .
    a5 = fig.add_subplot(233, title = 'Latency')
    width = float(pos) / (pos*2)

    if GUI['ErrorBar']:
        a5.bar(pos, average(latency), width, color=col, yerr=std(latency), ecolor=col, align='center' )
    else:
        a5.bar(pos, average(latency), width, color=col , align='center')

    a5.set_xticks(range(1,pos+2))
    a5.set_xticklabels(range(0,pos))
    a5.set_xlim(1.5, pos+0.5)



##    a5 = fig.add_subplot(222)
##    width = float(pos) / (pos*2)
##
##    if GUI['ErrorBar']:
##        a5.bar(pos, ff, width, color=col, yerr=std(ff_dist), ecolor=col, align='center' )
##    else:
##        a5.bar(pos, ff, width, color=col , align='center')
##
##    a5.set_xticks(range(1,pos+2))
##    a5.set_xticklabels(range(0,pos))
##    #if lse_avg_night > 3: a4.set_ylim(0,12
