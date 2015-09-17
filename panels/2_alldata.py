'''
This is a panel without graphs. It takes the basic information of selected flies and return the
data in two tables. The upper table returns averaged data of all selected flies. The lower table
gives specific data of single flies, day by day.
Multiple selections are possible
'''
#Default IMPORTED MODULES (DO NOT REMOVE)

from default_panels import *

class Panel(GridGrid):
    '''
    Here some variable specific to the PanelType
    '''
    
    def __init__(self, parent):

        PanelProportion = [2,6]
        
        sfLabels = ['Genotype', 'Day', 'Mon', 'Ch', 'alive', 'totSleep', 'rDS', 'rNS', 'AI', 'rD aLSE', 'rD aNSE', 'rN aLSE', 'rN aNSE', 'latency']
        sfdataTypes = [gridlib.GRID_VALUE_STRING] * 4 + [gridlib.GRID_VALUE_NUMBER] *1 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * 10
        
        AVGLabels = ['Genotype', 'Day', 'Mon', 'n(tot)','n(a)' , 'DaySleep', 'stdDV' ,'rDS', 'stdDV' ,'rNS', 'stdDV' , 'AI', 'stdDV', 'latency', 'stdDV']
        AVGdataTypes = [gridlib.GRID_VALUE_STRING] * 3 + [gridlib.GRID_VALUE_NUMBER] *2 + [gridlib.GRID_VALUE_FLOAT + ':6,2'] * 10
        
        GridGrid.__init__(self, parent, PanelProportion, [AVGLabels, sfLabels], [AVGdataTypes, sfdataTypes])
        self.name = 'All Data'
        self.compatible = 'all'

    def Refresh(self):
        '''
        This function takes the coordinates coming upon tree item selection
        and fills the grid with the data about all flies
        '''
        
        allSelections = GUI['dtList']
        cDAM = GUI['cDAM']
          
         
        single_fly_data = []
        genotype_set, day_set, mon_set = set ([]), set ([]), set ([])
        
        t0, t1 = self.limits.isActive() * self.limits.GetVals() or (None, None)

        for n_sel, selection in enumerate(allSelections): #every selection carries a 5 digits coordinate 
            
            k, m, d, f = selection[1:] #cDAMnumber, monitor, day, fly
            cSEL = cDAM[k]
            
            fs, fe = cSEL.getFliesInInterval(m, f)
            ds, de = cSEL.getDaysInInterval(d)
            
            gen_t = cSEL.getGenotype(); genotype_set.add ( gen_t )
            day_t = cSEL.getDate(d, format = 'mm/dd') or 'All'; day_set.add (day_t)
            mon_t = cSEL.getMonitorName(m, d, f) or 'All'; mon_set.add ( mon_t )

            #Here we gather the actual data
            ax_t, s5_t = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1)[0:2]

            #Here we set the data for the lower grid (SINGLE FLIES)
            for d in range(ds,de) or [ds]:
                day_sl = cSEL.getDate(d, format = 'mm/dd')
                for f in range(fs, fe) or [fs]:
                    
                    mon_sl, ch_sl = cSEL.getMonitorFlyName(f)
                     
                    # we need these two rows because fs and ds correspond to row 0 and col 0 of our matrix
                    fc = f - fs
                    dc = d - ds
    
                    alive = s5_t[dc,fc].sum() < 1430
                    AI = ax_t[dc,fc].sum() / (1440. - s5_t[dc,fc].sum())

                    len_sleep_episodes_day = all_sleep_episodes (s5_t[dc,fc], 0, 720)
                    len_sleep_episodes_night = all_sleep_episodes (s5_t[dc,fc], 721, 1440)
                    num_sleep_episodes_day = number_sleep_episodes (s5_t[dc,fc], 0, 720)
                    num_sleep_episodes_night = number_sleep_episodes (s5_t[dc,fc], 721, 1440)
                    latency = sleep_latency(s5_t[dc,fc], lightsoff=720)

                    single_fly_data.append([gen_t, day_sl, mon_sl, ch_sl, alive,
                                        s5_t[dc,fc].sum(),
                                        s5_t[dc,fc,0:720].sum(),
                                        s5_t[dc,fc,720:1440].sum(),
                                        AI,
                                        average( len_sleep_episodes_day ),
                                        average( num_sleep_episodes_day ),
                                        average( len_sleep_episodes_night ),
                                        average( num_sleep_episodes_night ),
                                        latency
                                        ])

            #Here we add data to the pool in case we are dealing with multiple selections
            if n_sel == 0:
                s5 = s5_t
                ax = ax_t
            else:
                s5 = concatenate ((s5, s5_t), axis=0)
                ax = concatenate ((ax, ax_t), axis=0)


        ## OUT OF THE LOOP ##
        #Here we set the data for the upper grid (AVERAGE)

        num_flies = s5.shape[1]
        num_alive = (s5.sum(axis=2)<1430).all(axis=0).sum() 
        dist_tot_sleep_by_fly = average (SleepAmountByFly (s5, t0, t1), axis=0)
        dist_day_sleep_by_fly = average (SleepAmountByFly (s5, t0=0, t1=720), axis=0)
        dist_night_sleep_by_fly = average (SleepAmountByFly (s5, t0=720, t1=1440), axis=0)
        dist_AI_by_fly = average (ActivityIndexByFly(ax, s5), axis=0)
        latency = sleep_latency(s5, 720)
        
        AVGdata = ( [list2str(genotype_set), list2str(day_set), list2str(mon_set),
                  num_flies, num_alive,
                  average(dist_tot_sleep_by_fly), std(dist_tot_sleep_by_fly),
                  average(dist_day_sleep_by_fly), std(dist_day_sleep_by_fly),
                  average(dist_night_sleep_by_fly), std(dist_night_sleep_by_fly),
                  average(dist_AI_by_fly), std(dist_AI_by_fly),
                  average(latency),std(latency),
                  0,0,0,0
               ]  )

        #this places the data in the table        
        if GUI['holdplot']:
            self.sheet[0].AddRow(AVGdata)
            self.sheet[1].AddRow(single_fly_data)
        else:
            self.sheet[0].SetData([AVGdata])
            self.sheet[1].SetData(single_fly_data)
