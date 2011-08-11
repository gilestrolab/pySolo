'''This Panel will take the coordinates of the data coming from the tree selection
and get the data diveded by 24h. Will plot the sleep pattern day by day and show the data
in the table.'''
#Default IMPORTED MODULES (DO NOT REMOVE)

from default_panels import *
import numpy as np

class Panel(PlotGrid):

    #Here some variable specific to the PanelType

    def __init__(self, parent):

        PanelProportion = [6,2,1]    #0 = not_show
        CanvasInitialSize = (-1,-1)     #size in inches

        colLabels = ['Genotype','Day','Mon','Ch','n(tot)','n(a)','sleep TD','st.dv.','sleep RD','st.dv.','sleep RN','st.dv.','AI','','st.dv','','color' ]
        dataTypes = [gridlib.GRID_VALUE_STRING] * 4 + [gridlib.GRID_VALUE_NUMBER] *2 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * 10 + [gridlib.GRID_VALUE_STRING]

        PlotGrid.__init__(self, parent,
                                         PanelProportion,
                                         CanvasInitialSize,
                                         colLabels,
                                         dataTypes
                                         #choiceList
                                         )
        self.name = 'Activity Peak'
        self.compatible = '0.9'
        
        self.AddOption('Yactivity', 'radio', 0, ['Max (dynamic)', '15', '10', '5'], 'Set the upper limit for the Y axis on the Activity plot')
        self.AddOption('mask_left', 'radio', 16, range(48), 'Set the left limit to look for the activity peak')
        self.AddOption('mask_right', 'radio', 32, range(48), 'Set the right limit to look for the activity peak')
        self.AddOption('thre_sleep_onset', 'text', 0, ['25'], 'Defines the threshold for sleep onset (%). Should not be higher than 30' )




    def Refresh(self):
        '''This function takes the coordinates from the item selection and plots the data as day by day'''

        allSelections = GUI['dtList']
        cDAM = GUI['cDAM']

        ShowErrorBar = GUI['ErrorBar']
        num_of_selected = GUI['num_selected']

        holdplot = GUI['holdplot']
        pos = GUI['currentlyDrawn'] #int - if yes, which one


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
        
        d,f,c = ax.shape

        #
        #finds the bin where activity peaks within the given mask
        #
        ax30 = ax.reshape((d,f,48,c/48)).sum(axis=3) # divides in 48 bins to sum up activity in bin of 30mins
        peak_mask = ones((d,f,48))
        left = int(self.GetOption('mask_left'))
        right = int(self.GetOption('mask_right'))
        peak_mask[:,:,left:right] = False
        ax30.mask = peak_mask
        peak_30 = ax30.argmax(axis=2)
        peak_avg = average(peak_30, axis=0)
        #peak_avg.compressed().tofile('avg1.csv', sep='\n')
        

        #this code is very ugly
        xmin = int(self.GetOption('thre_sleep_onset'))
        first_xmin_ep = np.zeros((d,f), dtype=np.int)
        for ds in range(d):
            for fs in range(f):
                a = s30[ds,fs].compressed()
                v = np.where(a >= xmin)
                try: 
                    v = np.min(v[0])
                except: 
                    v = 0
                first_xmin_ep[ds,fs] = int(v)
        
        print average(first_xmin_ep)
        first_xmin_ep.tofile('avg1.csv', sep='\n')
        
        


       
        if holdplot:
            color, color_name = getPlottingColor(pos-1)
            #datarow.append(color_name)
            #self.sheet.AddRow (datarow)
        else:
            color, color_name = getPlottingColor(pos-1)
            #datarow.append(color_name)
            #self.sheet.SetData ([datarow])

        
        title = ''

        self.canvas.redraw(self.plot_peak, title, ax30, color)
        
        
    def plot_peak(self, fig, title, ax30, col):
        '''
        '''
                #Draw the Activity plot
        #if sync: a1 = fig.add_axes([0.08, 0.60, 0.98, 0.3], sharex=a4)
        #else:  a1 = fig.add_axes([0.08, 0.60, 0.98, 0.3])


        
        a1 = fig.add_subplot(311)

        ax30_avg = average(average(ax30, axis=1), axis=0) 
        a1.plot(ax30_avg, color=col)

        ax30.mask = (ax30.mask == False)
        ax30_avg = average(average(ax30, axis=1), axis=0) 
        a1.plot(ax30_avg, color=brighten(col))
        
        #a1.grid(use_grid)
        a1.set_title(title)
        a1.set_ylabel('Activity Plot')
        a1.set_xlim((0, len(ax30_avg)))
        #self.AddOption('Yactivity', 'radio', '0', ['Max (dynamic)', '15', '10', '5'], 'Set the upper limit for the Y axis on the Activity plot')

        activity_limit = self.GetOption('Yactivity')
        if activity_limit != 'Max (dynamic)':
            activity_limit = int(activity_limit)
            a1.set_ylim((0, activity_limit))

        mpl.artist.setp( a1.get_xticklabels(), visible=False)

