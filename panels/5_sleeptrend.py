'''
This Panel gives two different information:
in the upper part, it plots the sleep by day, recorded over the selected period
in the lower part it shows the average sleep of all days selected, showing the proportion 
between daily sleep and night sleep
Multiple selections are allowed
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
                                         choiceList
                                         )
        self.name = 'Sleep Trend'
        self.compatible = 'all'
        

    def Refresh(self):
        '''
        This function takes the coordinates from the item selection and plots the data as day by day
        '''

        allSelections = GUI['dtList']
        cDAM = GUI['cDAM']
        ShowErrorBar = GUI['ErrorBar']
        holdplot = GUI['holdplot']
        num_of_selected = GUI['num_selected'] #int - how many selections we are dealing with?

        datarow = []
        sel_days = dict()

        genotype_set, day_set, mon_set, ch_set = set ([]), set ([]), set ([]), set([])
        #get start and end value in the limit subpanel
        t0, t1 = self.limits.isActive() * self.limits.GetVals() or (None, None)

        for n_sel, selection in enumerate(allSelections): #every selection carries a 5 digits coordinate 

            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]

            genotype_set.add ( cSEL.getGenotype() )
            mon_t = cSEL.getMonitorName(m, d, f) or 'All'; mon_set.add(mon_t)
            day_t = cSEL.getDate(d, f) or 'All'; day_set.add(day_t)
            ch_t = cSEL.getChannelName(m, f) or 'All'; ch_set.add(ch_t)

            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)
            # take the 3D arrays for
            ax_t, s5_t = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1)[0:2]  #get the S5 of the currently selected item

            if n_sel == 0:
                s5 = s5_t
                ax = ax_t
            else:
                s5 = concatenate ((s5, s5_t), axis=0)
                ax = concatenate ((ax, ax_t), axis=0)


        #OUT OF THE LOOP HERE
        # Data plotted in the upper panel (the sleep trend)
        
        total_sleep = SleepAmountByFly (s5)
        day_sleep = SleepAmountByFly (s5, t0=None, t1=720)
        night_sleep = SleepAmountByFly (s5, t0=720, t1=None)
        AI = ActivityIndexByFly(ax, s5)

        #data going in the table
        for d in range(s5.shape[0]):
            
            if len(day_set) > 1:
                day_t = list(day_set)[d]
            else:
                day_t = cSEL.getDate(d)

            num_alive = (total_sleep < 1430)[d].sum()
            num_flies = total_sleep.shape[1]

            datarow.append ([list2str(genotype_set), day_t, list2str(mon_set), list2str(ch_set),
                             num_flies, num_alive,
                             average(total_sleep[d]), std(total_sleep[d]),
                             average(day_sleep[d]), std(day_sleep[d]),
                             average(night_sleep[d]), std(night_sleep[d]),
                             average(AI[d]), std(AI[d]) ])
            
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

        #Data been plotted
        if GUI['choice'] == 'sleep TD':
            value_avg =  average(total_sleep, axis=1)
            value_std =  std(total_sleep, axis=1)
        
        elif GUI['choice'] == 'sleep RD':
            value_avg =  average(day_sleep, axis=1)
            value_std =  std(day_sleep, axis=1)
        
        elif GUI['choice'] == 'sleep RN':
            value_avg =  average(night_sleep, axis=1)
            value_std =  std(night_sleep, axis=1)
        
        elif GUI['choice'] == 'AI':
            value_avg =  average (AI, axis=1)
            value_std =  std (AI, axis=1)

        single_day_avg = average(value_avg)
        single_day_std = average(value_std) 
        single_day_rd_avg = average(day_sleep)
        single_day_rn_avg = average(night_sleep)

        self.canvas.redraw(subplot_trend, title, value_avg, value_std, single_day_avg, single_day_std, single_day_rd_avg, single_day_rn_avg, pos, color )
        self.WriteComment(cSEL.Comment or '')


def subplot_trend(fig, title, value_avg, value_std, single_day_avg, single_day_std, single_day_rd_avg, single_day_rn_avg, pos, col):

##    for n, point in zip(range(len(value_avg)), value_avg):
##        if point == NaN: value_avg[n] = -1


    #UPPER PANEL
    a1 = fig.add_subplot(211)
    #a1.xlim(0,len(tot_sleep)+1)
    a1.plot(value_avg, color=col, marker= 'o', ls = ':')
    if GUI['ErrorBar']: a1.errorbar(range(0,len(value_avg)), value_avg, value_std, ecolor=col, fmt=None )
    if single_day_avg > 3: a1.set_ylim(0,1440)
    a1.set_ylabel('Sleep (m/d)')

    a1.set_xlim(-1,len(value_avg))
    step = (len(value_avg)>50 * 5) or 1
    a1.set_xticklabels( range(1, len(value_avg) +1)[::step]  )
    a1.set_xticks( range(0, len(value_avg))[::step] )

    a1.set_xlabel('Day')
    a1.set_title(title)

    #LOWER RIGHT
    a2 = fig.add_subplot(224, title = 'Total Sleep')
    pos = pos + 1
    width = float(pos) / (pos*2)

    if GUI['ErrorBar']:
        a2.bar(pos, single_day_avg, width, color=col, yerr=single_day_std, ecolor=col, align='center' )
    else:
        a2.bar(pos, single_day_avg, width, color=col , align='center')

    a2.set_ylabel('Sleep (m/d)')
    a2.set_xticks(range(1,pos+2))
    a2.set_xticklabels(['']+range(1,pos))
    a2.set_xlim(1.5,pos+0.5)
    if single_day_avg > 3: a2.set_ylim(0,1440)


    #LOWER LEFT
    a3 = fig.add_subplot(223, title = 'Total Sleep (day/night)')

    col_brighter = brighten(col)

    p1 = a3.bar(pos, single_day_rd_avg, width, color=col, ecolor=col, align='center' )
    if GUI['ErrorBar']:
        p2 = a3.bar(pos, single_day_rn_avg, width, color=col_brighter, bottom=single_day_rd_avg, yerr=single_day_std, ecolor=col, align='center' )
    else:
        p2 = a3.bar(pos, single_day_rn_avg, width, color=col_brighter, bottom=single_day_rd_avg, align='center')
    a3.set_xticks(range(1,pos+2))
    a3.set_xticklabels(['']+range(1,pos))
    a3.set_xlim(1.5,pos+0.5)
    a3.set_ylim(0,1440)
##    a3.legend( (p1[0], p2[0]), ('Day', 'Night') )
    ##a3.set_ylabel('Sleep (m/d)')
