#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       untitled.py
#       
#       Copyright 2011 Giorgio Gilestro <giorgio@gilest.ro>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import datetime
import numpy as np

pySoloVersion = 'dev'


class DAMslice(object):
    """
    DAMslice is the core class for managing the DAM data. The object DAMslice contains
    all the properties that refer to one genotype.
    
    fly is a number from 0 to nF (nF is the number of flies in the DAM class)
    channel is the name of the fly(n)
    monitor is a number from 0 to nM (nM is the number of monitors in the DAM class)
    monitor_name is the name of the monitor(n)
    for instance:
    
    Fly    Channel    Monitor    Monitor_name
    0        1        0            31
    1        2        0            31
    2        3        0            31
    3        1        1            60
    4        2        1            60
    5        3        1            60
    
    """
    def __init__(self, mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version=pySoloVersion):

        #Data coming from outside
        self.Header = [mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version]
        self.Mon = [str(int(m)) for m in str(mon).split('/')]
        self.StartChannel = [str(int(sc)) for sc in str(sch).split('/')]
        self.EndChannel = [str(int(ec)) for ec in str(ech).split('/')]
        self.Genotype = str(genotype)
        self.Comment = str(comment)
        self.StartMonth = int(smont)
        self.StartDay = int(sd)
        self.EndMonth = int(emont)
        self.EndDay = int(eday)
        self.years = year
        self.StartYear = int(str(year).split('/')[0])
        self.EndYear = int(str(year).split('/')[-1])
        self.version = version


        #Data calculated here
        #This are some of the values that can be called from outside
        #TO DO: first four are not really needed - remove
        self.totFlies = self.getTotalFlies()
        self.totDays = self.getTotalDays()

        self.rangeDays = self.getDatesRange()
        self.rangeChannel = self.getChannelsMonitorsRange()


        self.isOneMon = (len(self.Mon) == 1)    #Boolean. If False the DAM data span more than 1 monitor

        #Arrays
        self.datatype = np.int32
        self.datalenght = 1440

        self.fly = np.zeros((self.totDays,self.totFlies, self.datalenght), dtype=self.datatype)
        self.fly5min = np.zeros((self.totDays, self.totFlies, self.datalenght), dtype=self.datatype)
        self.fly30min = np.zeros((self.totDays, self.totFlies, self.datalenght), dtype=self.datatype)
        self.flyStatus = np.ones((self.totDays, self.totFlies), dtype=self.datatype) # fly is enabled or not?

#TODO
    def __CalculateSleep__(self, fly_to_calc=None, inactivity=0, use_legacy_algorithm=False):
        """
        This function will calculate sleep5mins and sleep30mins array
        for all the flies of the current DAM
        inactivity could be higher than 0 if there is a noise in the activty level (for instance with video analysis).
        """


        if fly_to_calc:
            fc = range(fly_to_calc, fly_to_calc+1)
        else:
            fc = range(self.totFlies)

        d,f,c = self.fly.shape
        self.fly = self.fly.transpose((1,0,2)) #d,f,c -> f,d,c

        single_flies = self.fly.reshape((f, d*c))
        single_flies5min = self.fly5min.reshape((f, d*c))
        single_flies30min = self.fly30min.reshape((f, d*c))

        bins = c
        minute = bins / 1440. #this is the number of counts per minute. this value is not userdefined! 

        # a + b = number of bins spanning a 5 mins period
        # if sample rate is 1440/day then a1 = 2, b1 = 3
        a1 = int(np.floor((minute * 5 ) / 2))
        b1 = int(np.ceil((minute * 5 ) / 2))

        # c + d = number of bins spanning a 30 mins period
        # if sample rate is 1440/day then a2 = 15, b2 = 15
        a2 = int(np.floor((minute * 30) / 2))
        b2 = int(np.ceil((minute * 30) / 2))

        #t1 = single_flies.transpose

        if use_legacy_algorithm:

            for fly in fc:
                single_flies5min[fly] = [( single_flies[fly][i-b1:i+a1].sum() <= inactivity ) for i in range (d*c)]
                single_flies30min[fly]  = [ single_flies5min[fly][i-b2:i+a2].sum() for i in range (d*c)]

        else:

            for fly in fc:
                
                sf_1 = np.array([( single_flies[fly][i:i+5].sum() <= inactivity ) for i in range (d*c)])
                sf_2 = np.array([( single_flies[fly][i-1:i+4].sum() <= inactivity ) for i in range (d*c)])
                sf_3 = np.array([( single_flies[fly][i-2:i+3].sum() <= inactivity ) for i in range (d*c)])
                sf_4 = np.array([( single_flies[fly][i-3:i+2].sum() <= inactivity ) for i in range (d*c)])
                sf_5 = np.array([( single_flies[fly][i-4:i+1].sum() <= inactivity ) for i in range (d*c)])

                single_flies5min[fly] = sf_1 + sf_2 + sf_3 + sf_4 + sf_5

                single_flies30min[fly]  = [ single_flies5min[fly][i-b2:i+a2].sum() for i in range (d*c)]


        #single_flies5min = single_flies5min * 1./minute #this is necessary to have all values properly referring to minutes
        #single_flies30min = single_flies30min * 1./minute

        self.fly = self.fly.transpose((1,0,2))
        self.fly5min = single_flies5min.reshape((f,d,c)).transpose((1,0,2))
        self.fly30min = single_flies30min.reshape((f,d,c)).transpose((1,0,2))


    def ___resampleAllto1440__(self):
        """
        This function can be used to resample all our arrays to 1440 bins per day (1 bin per minute)
        """
        
        d,f,c = self.fly.shape
        c1 = c / 1440
        
        self.fly = self.fly.reshape((d,f,1440,c1)).sum(axis=3)
        self.fly5min = self.fly5min.reshape((d,f,1440,c1)).sum(axis=3) / c1
        self.fly30min = np.average(self.fly30min.reshape((d,f,1440,c1)),axis=3) / c1
        
        self.fly = self.fly.astype(np.int32)
        self.fly5min = self.fly5min.astype(np.int32)
        self.fly30min = self.fly30min.astype(np.int32)
        

    def getHeader(self):
        """
        Return the initial information about the DAMslice as a list
        the first argument in the list is the class name
        the second argument in the list must be a list with the following parameters
        [mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version]
        """
        return [DAMslice, self.Header]

    def getTotalDays(self):
        """
        Return the number of days recorded in this DAMslice
        """
        elapse = datetime.date(self.EndYear, self.EndMonth, self.EndDay) - datetime.date(self.StartYear, self.StartMonth, self.StartDay)
        return elapse.days +1

    def getTotalFlies(self):
        """
        Return the total number of flies recorded in this DAMslice
        """
        tot = 0
        for i in range (0,len(self.StartChannel)):
            tot += int(self.EndChannel[i]) - int(self.StartChannel[i]) +1
        return tot

    def getMonitorFlyName(self, f, d=None):
        """
        given fly 
        returns monitor_name and channel 
        """
        r = self.getChannelsMonitorsRange()
        monitor = r[1][f]
        channel = r[0][f]
        return monitor, channel
        

    def getGenotype(self):
        """
        Return the genotype name
        """
        return str(self.Genotype)

    def getDatesRange(self):
        """
        Return a 3-dimensional list composed of three list of the same size:
        the list of days, the list of months, the list of year
        eg: [[30,31,1,2],[12,12,1,1],[2007,2007,2008,2008]]
        """

        dateStart = datetime.date( self.StartYear, self.StartMonth, self.StartDay )
        dateEnd = datetime.date( self.EndYear, self.EndMonth, self.EndDay )
        tot_days = (dateEnd - dateStart).days

        all_dates = [dateStart + datetime.timedelta(days=d) for d in range(0, tot_days+1)]

        rangedays = [d.day for d in all_dates]
        rangemonths = [d.month for d in all_dates]
        rangeyear = [d.year for d in all_dates]

        return [rangedays, rangemonths, rangeyear]

    def getChannelsMonitorsRange(self):
        """
        Return an array composed of two arrays of the same size:
        the list of channel numbers and the list of monitor_names
        Example: [[1,2,3,4,5,6,7],[5,5,5,5,5,5,5]]
        """
        rangeCh, rangeMon = [], []
        for i in range (0,len(self.Mon)):
            rangeCh += range(int(self.StartChannel[i]), int(self.EndChannel[i])+1)
            rangeMon += [self.Mon[i]]*(int(self.EndChannel[i])+1-int(self.StartChannel[i]))

        return rangeCh, rangeMon

    def getFliesInMon(self, mon):
        """
        Return the first and the last fly belonging to the monitor_name mon
        """
        mon = str(int(mon))
        f = self.rangeChannel[1].index(mon)
        f1 = f + self.rangeChannel[1].count(mon)-1
        return f, f1

    def getRangePerMon(self, monitor):
        """
        Return the list of channels (1-32) within a given monitor
        """
        monitor = int(monitor)
        return range (int(self.StartChannel[monitor]), int(self.EndChannel[monitor])+1)

    def getDate(self, d, f=None, format = 'mm/dd'):
        """
        Return a string with formatted Date for for the Nth day in current DAMslice
        format can use: m, mm, d, dd, yy, yyyy and / as separator
        """
        d = int(d)

        if d >= 0 and d < self.totDays:

            dd = format.count('d')
            mm = format.count('m')
            yy = format.count('y')

            day = '%s' % ( str(self.getDatesRange()[0][d]).zfill(dd) * (dd>0) )
            month = '%s' % ( str(self.getDatesRange()[1][d]).zfill(mm) * (mm>0) )
            year = '%s' % (str(self.getDatesRange()[2][d]))[4-yy:] * (yy>0)

            format = format.replace('d'*dd, day)
            format = format.replace('m'*mm, month)
            date_output = format.replace('y'*yy, year)

        else:

            date_output = None

        return date_output


    def getMonitorName(self, m, d=None, f=None):
        """
        given the monitor number, returns a string with the monitor_name 
        If all monitor are selected will return the string 'all'
        """

        if self.isOneMon and m == -1: m = 0
        if m >= 0:
            mon_name = self.Mon[m]
        else:
            mon_name = None

        return mon_name

    def getChannelName(self, m, f, d=None):
        """
        Return a string with the channel specified monitor.
        If all channels are selected will return the string 'all'
        TODO: Adjust this!
        """
        if m == -1 and self.isOneMon: m = 0

        #if m >= 0 and f >= 0:
        if f >= 0:
            channels, monitors = self.getChannelsMonitorsRange()
            output = channels[f]
            #output = self.getRangePerMon(m)[f]
        else:
            output = None
        return output

    def getFliesInInterval(self, m, f, d=None):
        """
        Return the tuple f, f1 as fly values
        If all flies are selected f=0, f1=self.totFlies-1
        """

        if f == -1 and m == -1:
            f, f1 = 0, self.totFlies

        elif f == -1 and m != -1:
            m0 = self.getMonitorName(m)
            f0 = self.getChannelName(m, f)
            f = self.rangeChannel[1].index(m0)
            f1 = self.getFliesInMon(m0)[-1] + 1

        elif f != -1:
            m0 = self.getMonitorName(m)
            f0 = self.getChannelName(m, f)
            f = f1 = self.rangeChannel[0].index(f0,self.rangeChannel[1].index(m0))

        return f, f1

    def getDaysInInterval(self, d, m=None, f=None):
        """
        Return the tuple d, d1 as int values
        If all days are selected d=0, d1=self.totDays-1
        """

        if d == -1:
            d, d1 = 0, self.totDays
        else:
            d1 = d

        return d, d1


    def setFly(self, d, f, activity):
        """
        Set the raw data for fly f at day d
        Then calculates the 5min sleep bins and the 30min sleep curve
        activity is a list of bins spanning the day (default length = 1440)
        """

        self.fly[d,f] = activity
        #calculate sleep for the fly, if it is dead
        #if not self.fly[d][f].any() and not self.fly5min[d][f].any() : self.__CalculateSleep__(f)
        #calculate sleep for all flies if we are adding the final one
        if d == (self.totDays - 1)  and f == (self.totFlies - 1): self.__CalculateSleep__()

    def setFlyStatus(self, d, d1, f, f1, status=0):
        """
        Change the status of the flies f to f1 for days d to d1:

        -1 - Inactive Baseline
        -2 - Inactive SD
        -3 - Inactive Recovery
        -4 - Inactive None
        -5 - Make Inactive
        0 - Toggle Status (mirror)
        1 - Active Baseline
        2 - Active SD
        3 - Active Recovery
        4 - Active None
        5 - Make Active

        Only active flies are counted when flyAlive is run
        """

        if f1 ==-1:
            f1 = self.totFlies
        else:
            f1 = f1 + (f==f1)

        if d1 ==-1:
            d1 = self.totDays
        else:
            d1 = d1 + (d==d1)

        for day in range(d,d1):
            for sf in range (f, f1):
                if status == 0:
                    self.flyStatus[day,sf] = self.flyStatus[day,sf] * -1
                elif status == 5:
                    self.flyStatus[day,sf] = abs(self.flyStatus[day,sf]) or 4
                elif status == -5:
                    self.flyStatus[day,sf] = (0 - abs(self.flyStatus[day,sf])) or -4
                else:
                    if self.flyStatus[day,sf] <= 0 : self.flyStatus[day,sf] = 0 - status
                    if self.flyStatus[day,sf] > 0 : self.flyStatus[day,sf] = status



    def allinStatus(self, mon=None, day=None, fly=None, status=-5):
        """
        Return true if all the flies in the interrogated category have the same status

        -5 - All Inactive
        5 - All Active

        +/-1 - Baseline
        +/-2 - SD
        +/-3 - Recovery
        +/-4 - None

        """

        def AllinStatus(input):
            if status == -5: return all ([v < 0 for v in input])
            if status == 5: return all ([v > 0 for v in input])
            else: return all ([abs(v) == abs(status) for v in input])

        if fly!= None and mon!=None and day!=None:
            mon = self.Mon[mon]
            f,f1 = self.getFliesInMon(mon)
            return AllinStatus ( [ self.flyStatus[day][(range(f,f1+1)[fly])] ] )

        elif day!=None and mon!=None:
            mon = self.Mon[mon]
            f,f1 = self.getFliesInMon(mon)
            return AllinStatus ( self.flyStatus[day][f:f1+1] )

        elif fly!= None and mon!=None:
            mon = self.Mon[mon]
            f,f1 = self.getFliesInMon(mon)
            return AllinStatus ( self.flyStatus.T[range(f,f1+1)[fly]] )

        elif mon!=None:
            mon = self.Mon[mon]
            f,f1 = self.getFliesInMon(mon)
            return AllinStatus ( self.flyStatus.T[f:f1+1].reshape(-1) )

        elif day!=None:
            return AllinStatus ( self.flyStatus[day] )

        elif fly!=None:
            return AllinStatus ( self.flyStatus.T[fly] )

        return False



    def filterbyStatus(self, d, d1, f, f1, t0=None, t1=None, status=5, use_dropout = True, min_alive = 0, max_alive = 1400, useFilter = True):
        """
        RETURN MASKED ARRAY
        This function filters the fly raw data by fly status and returns the distribution
        of the fundamental values in the selected population. 
        
        Status are:

            -1 - Inactive Baseline
            -2 - Inactive SD
            -3 - Inactive Recovery
            -4 - Inactive None
            -5 - All Inactive

            1 - Active Baseline
            2 - Active SD
            3 - Active Recovery
            4 - Active None
            5 - All Active

        """


        if useFilter: ## Do we exclude inactive flies from our harvesting?
            if status == 5: s0, s1 = 1, 4
            elif status == -5: s0, s1 = -1, -4
            else: s0,s1 = status, status
        else:
            status = abs(status)
            if status == 5: s0, s1 = -1, 4
            else: s0,s1 = status, status

        if f1 == -1: f1 = None
        else: f1 += 1
        if d1 == -1: d1 = None
        else: d1 += 1

        fly5_slice =  self.fly5min[d:d1,f:f1,t0:t1]
        fly_Status_slice =  self.flyStatus[d:d1,f:f1]

        # Here we create a mask to be applied to the other array to exclude
        # those flies that died at a certain point (the dropouts).
        if not useFilter: min_alive, max_alive = 0, 1440

        fly_alive_through = ((fly5_slice.sum(axis=2) > min_alive) & (fly5_slice.sum(axis=2) < max_alive)) #shape = (f,d)
        
        if use_dropout:
            # If we decided to use the dropout we at least have to change their value to NaN
            # after they died so that they are not going to be included in our averages
            mask_do = (fly_alive_through == False)

        else:
            # If we don't want to use the dropouts we completely get rid of the data for
            # those flies as they never existed ,masking it
            mask_do = np.zeros(fly_alive_through.shape, dtype = np.bool)
            fly_alive_through_by_row = fly_alive_through.all(axis=0) #for each fly check if there is at least a day beyond limits
            indices = np.where(fly_alive_through_by_row == False)
            mask_do[:,indices] = True

        # Now we get rid of the flies we don't want because they are not in the Status
        # we asked for. All those flies will be NaN
        StatusMask = (fly_Status_slice >=s0) & (fly_Status_slice <=s1)

        mask_t = mask_do | (StatusMask==False)
        mask_f = np.zeros(fly5_slice.shape)
        indices = np.where(mask_t == True)
        mask_f[indices] = True

        fly5_slice = np.ma.masked_array(fly5_slice, mask=mask_f)

        fly_slice = np.ma.masked_array(self.fly[d:d1,f:f1,t0:t1], mask=mask_f)
        fly30_slice = np.ma.masked_array(self.fly30min[d:d1,f:f1,t0:t1], mask=mask_f)

        return fly_slice, fly5_slice, fly30_slice

    def saveRawData(self, tmpFileHandle):
        """
        """
        self.fly.tofile(tmpFileHandle)
        self.fly5min.tofile(tmpFileHandle)
        self.fly30min.tofile(tmpFileHandle)
        self.flyStatus.tofile(tmpFileHandle)

    def loadRawData(self, tmpFileHandle):
        """
        """
        shape = self.fly.shape
        size = self.fly.size
        shapeStatus = self.flyStatus.shape
        sizeStatus = self.flyStatus.size
        datatype = self.datatype

        self.fly = np.fromfile(tmpFileHandle, count = size, dtype=datatype).reshape(shape)
        self.fly5min = np.fromfile(tmpFileHandle, count = size, dtype=datatype).reshape(shape)
        self.fly30min = np.fromfile(tmpFileHandle, count = size, dtype=datatype).reshape(shape)
        self.flyStatus = np.fromfile(tmpFileHandle, count = sizeStatus, dtype=datatype).reshape(shapeStatus)

class videoSlice(DAMslice):
    """
    This is the class modified to handle pysolo Video files.
    Input files are of kind .ccf (coordinates files)
    """

    def __init__(self, mon='0', sch='1', ech='1', genotype='none', comment='', smont='1', sd='1', emont='1', eday='1', year='1900', version=pySoloVersion):
        """
        Proxy to DAMslice
        """
        DAMslice.__init__(self, mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version)
        

    def __updateHeaderData__(self, genotype):
        """
        This is run by loadSingleFile after a single file has been loaded
        """
        
        d,f,c = self.fly.shape
        mon = 0; sch = 1; ech = f
        comment = 'This data were not obtained using pySolo database but they were imported from a raw coords file'
        smont = 1; emont = 1; sd = 1; eday = d; year = '1900'
  
        self.Header = [mon, sch, ech, genotype, comment, smont, sd, emont, eday, year]
        self.Mon = str(mon).split('/')
        self.StartChannel = str(sch).split('/')
        self.EndChannel = str(ech).split('/')
        self.Genotype = str(genotype)
        self.Comment = str(comment)
        self.StartMonth = int(smont)
        self.StartDay = int(sd)
        self.EndMonth = int(emont)
        self.EndDay = int(eday)
        self.years = year
        self.StartYear = int(str(year).split('/')[0])
        self.EndYear = int(str(year).split('/')[-1])

        #Data calculated here
        #This are some of the values that can be called from outside
        #TO DO: first four are not really needed - remove
        self.totFlies = self.getTotalFlies()
        self.totDays = self.getTotalDays()
        self.rangeDays = self.getDatesRange()
        self.rangeChannel = self.getChannelsMonitorsRange()

        self.isOneMon = (len(self.Mon) == 1)    #Boolean. If False the DAM data span more than 1 monitor
        self.flyStatus = np.ones((self.totDays, self.totFlies), dtype=self.datatype) # fly is enabled or not?

        

    def loadSingleFile(self, filename, use_virtual_trikinetics=False, min_act=100, max_act=1000 ):
        """
        open a file containing the raw coordinates and populates the DAMslice with the data
        inside then computes the activity of the flies
        """
        #open the filename and stores the coords
        self.coords = self.getCoordinatesArray(filename)
        
        #transform coords to activity
        #uses the virtual monitor
        if use_virtual_trikinetics:
            self.fly = self.getActivityFromPosition(self.coords)
            min_act = 0
        #uses the activity 
        else:
            self.fly = self.getActivityFromCoords(self.coords)

        #fills in holes in the reading (likely for missing frames)
        self.fly = self.expandToProperSize(self.fly)
        self.datalenght = self.fly.shape[2]
        
        genotype = filename.split('/')[-1][:-4]
        self.__updateHeaderData__(genotype)

        self.fly5min = np.zeros((self.totDays, self.totFlies, self.datalenght), dtype=self.datatype)
        self.fly30min = np.zeros((self.totDays, self.totFlies, self.datalenght), dtype=self.datatype)
        
        self.__CalculateSleep__(inactivity=min_act)
        self.___resampleAllto1440__()

    def expandToProperSize(self, in_array, size=None):
        """
        If the recording has missed some frames then we need to fill in here and there with some other values
        will do this on the activity array
        Can calculate the proper size or can be suggested what size expand to
        this is not a Fourier based resampling, it's just interpolation
        """
        
        d,f,c = in_array.shape
        
        #do we need to guess the best size?
        if not size: size = int(np.ceil(c / 1440.)*1440)
        
        if size > c:

            new_array = np.zeros((d,f,size), dtype = np.int32)
            
            missing_frames = size - c
            #fragments = int(np.ceil(c / missing_frames * 1.0))
            fragments = int(np.ceil(size / missing_frames * 1.0))
    
            #pos1 = range(0, c, fragments)
            pos = range(0, size+1, fragments)
           
            for i in range(missing_frames)[:]:
                a = pos[i]; b = pos[i+1]-1
                c = a - i; d = b - i
                #print 'frag: %s\t%s:%s in %s:%s'%(i,a,b,c,d)
                new_array[:,:,a:b] = in_array[:,:,c:d]
            
            return new_array
        
        else:
            
            return in_array
    


    def getCoordinatesArray(self, filename):
        """
        open a file with one day worth of data and returns a 3D numpy array with the data inside
        Array coordinates are (num_flies, num_frames, 2)
        """
        
        n_day = 1
        f = open (filename, 'r')
        coord_list = []
        
        #read the file line by line (that is frame by frame)
        for line in f.readlines():
            #remove the last entry (newline char) and the first (frame number)
            l = line.split('\t')[1:-1]
            coord_list.append(l)
        
        #understand how many flies we have and how many frames    
        n_frame = len(coord_list)
        n_flies = len(coord_list[0])
        
        #creates a 3D array of the proper size
        coords = np.zeros((n_day, n_flies, n_frame, 2))
        
        #fill the array with the values
        for fl in range(n_flies):
            for fr in range(n_frame):
                x, y = coord_list[fr][fl].split(',')
                coords[0,fl,fr] = int(x), int(y)
    
        return coords
    
    
    def getActivityFromCoords(self, coords):
        """
        coords is a 3D array of shape: num_flies, num_frames, (x, y)
        returns an array of size num_flies, num_frames
        """
        coords1 = np.roll(coords, 1, axis=2) #copy and roll everything 1 position on the right frame
        
        #subtract one to the other to have the measure of the perpendicular distances
        cats = coords1 - coords
        c_x = cats[:,:,:,0]
        c_y = cats[:,:,:,1] 
        #Pitagora's theorem
        dist = np.hypot(c_x, c_y)
        
        return dist

    def getActivityFromPosition(self, coords, beam_size=35):
        """
        coords is a 3D array of shape: num_flies, num_frames, (x, y)
        returns an array of size num_flies, num_frames
        
        the data returned here are computed as if in a Virtual Monitor
        """
        y_pos = coords[:,:,:,1]
        #here we draw the virtual line which is going to be exactly half way #
        #between the highest point and the lowest point
        lines = np.expand_dims(y_pos.max(axis=2) / 2, axis=2) + beam_size
        
        is_north = y_pos < lines
        is_south = y_pos >= lines
        #is_on_beam = (y_pos > (lines - 2) ) & (y_pos  < (lines + 2)) 

        has_crossed = ( is_north - np.roll(is_south, -1, axis=2) ) == 0
        
        
        return has_crossed# | is_on_beam)


class sixminsSlice(DAMslice):
    
    def __init__(self, mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version=pySoloVersion):
        """
        """
        DAMslice.__init__(self, mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version=pySoloVersion)
    
    
    def __CalculateSleep__(self, fly_to_calc=None):
        """
        This function will calculate sleep5mins and sleep30mins array
        for all the flies of the current DAM
        """

        if fly_to_calc:
            fc = range(fly_to_calc, fly_to_calc+1)
        else:
            fc = range(self.totFlies)

        d,f,c = self.fly.shape
        self.fly = self.fly.transpose((1,0,2)) #d,f,c -> f,d,c

        single_flies = self.fly.reshape((f, d*c))
        single_flies5min = self.fly5min.reshape((f, d*c))
        single_flies30min = self.fly30min.reshape((f, d*c))

        bins = c
        minute = bins / 1440. #this value is not userdefined!

        # a + b = number of bins spanning a 5 mins period
        # if sample rate is 1440/day then a1 = 2, b1 = 3
        a1 = int(np.floor((minute * 6 ) / 2))
        b1 = int(np.ceil((minute * 6 ) / 2))

        # c + d = number of bins spanning a 30 mins period
        # if sample rate is 1440/day then a2 = 15, b2 = 15
        a2 = int(np.floor((minute * 30) / 2))
        b2 = int(np.ceil((minute * 30) / 2))

        t1 = single_flies.transpose

        for fly in fc:
            single_flies5min[fly] = [( single_flies[fly][i-b1:i+a1].sum() == 0 ) for i in range (d*c)] #1440 * n_days
            single_flies30min[fly]  = [ single_flies5min[fly][i-b2:i+a2].sum() for i in range (d*c)]

        self.fly = self.fly.transpose((1,0,2))
        self.fly5min = single_flies5min.reshape((f,d,c)).transpose((1,0,2))
        self.fly30min = single_flies30min.reshape((f,d,c)).transpose((1,0,2))


class plusSlice(DAMslice):
    """
    the class tankSlice add some functionalities to DAMslice by providing further data for use
    with the trikinetics systems. It includes two new arrays: one called response where we store
    data about the response time (TANK system) and one called lights were we can store data about
    the lights conditions.
    """
    def __init__(self, mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version=pySoloVersion):
        DAMslice.__init__(self, mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version)

        self.response = np.zeros((self.totDays, self.totFlies,  self.datalenght), dtype=self.datatype)
        self.lights = np.zeros((self.totDays, self.datalenght), dtype=self.datatype)

    def getHeader(self):
        """
        Return the initial information about the DAMslice as a list
        the first argument in the list is the class name
        the second argument in the list must be a list with the following parameters
        [mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version]
        """
        return [DAMslice, self.Header]

    def setResponse(self, d, f, response):
        """
        When we use the tank we need to store also another bit of information
        namely after how many milliseconds did the fly cross the beam
        """
        self.response[d,f] = response

    def setLights(self, d, lights):
        """
        Set the light status for the given day
        """
        self.lights[d] = lights

    def getResponseTime(self, mask_f, d, d1, f, f1):
        """
        Only for TANKED data. Return response time profile of the flies f to f1 for days d to d1 masking away according to the provided mask_f
        """

        if f1 ==-1:
            f1 = None
        else:
            f1 = f1+1

        if d1 ==-1:
            d1 = None
        else:
            d1 = d1+1

        rt_transposed = np.ma.masked_array(self.response[d:d1,f:f1], mask=mask_f)
        return rt_transposed

    def saveRawData(self, tmpFileHandle):
        """
        """
        self.fly.tofile(tmpFileHandle)
        self.fly5min.tofile(tmpFileHandle)
        self.fly30min.tofile(tmpFileHandle)
        self.flyStatus.tofile(tmpFileHandle)
        self.response.tofile(tmpFileHandle)
        self.lights.tofile(tmpFileHandle)

    def loadRawData(self, tmpFileHandle):
        """
        """
        shape = self.fly.shape
        size = self.fly.size
        shapeStatus = self.flyStatus.shape
        sizeStatus = self.flyStatus.size
        shapeLights = self.lights.shape#(shape[0], shape[2])
        sizeLights = self.lights.size#(size / shape[1])
        datatype = self.datatype


        self.fly = np.fromfile(tmpFileHandle, count = size, dtype=datatype).reshape(shape)
        self.fly5min = np.fromfile(tmpFileHandle, count = size, dtype=datatype).reshape(shape)
        self.fly30min = np.fromfile(tmpFileHandle, count = size, dtype=datatype).reshape(shape)
        self.flyStatus = np.fromfile(tmpFileHandle, count = sizeStatus, dtype=datatype).reshape(shapeStatus)
        self.response = np.fromfile(tmpFileHandle, count = size, dtype=datatype).reshape(shape)
        self.lights = np.fromfile(tmpFileHandle, count = sizeLights, dtype=datatype).reshape(shapeLights)



class metaSlice(DAMslice):
    """
    the class metaSlice is a class that provide the possibility of
    having flies with different histories in the same slice
    it inherits all properties and functions of DAMslice and introduce new ones
    based on two new classes called metaFly and metaDay
    """
    def __init__(self, mon=None, sch=None, ech=None, genotype=None, comment=None, smont=None, sd=None, emont=None, eday=None, year=None, version=None, metaFlies=None):
        """
        """
        if metaFlies:
            #self.Header = header
            self.metaFly = metaFlies
            self.ToDAMslice()
        else:
            self.metaFly = []

    def AddFly(self, f):
        """
        Add a new metaFly to the list metaFly
        """
        self.metaFly.append (f)

    def getTotalDays(self):
        """
        Return the maximum number of days
        it equals the number of days the longest living fly lived
        """
        d = []
        for f in self.metaFly:
            d.append ( f.getTotalDays() )
        d.sort()
        return int(d[-1])

    def getTotalFlies(self):
        """
        return the total number of flies in this metaSlice
        """
        return len(self.metaFly)

    def ToDAMslice(self):
        """
        inherits from DAMslice all the properties
        """
        #DAMslice(mon, sch, ech, genotype, comment, smont, sd, emont, eday, year, version=PySoloVersion)
        mon = 0
        sch = 1
        ech = self.getTotalFlies()
        td = self.getTotalDays()

        self.genotype = self.metaFly[-1].genotype
        comment = ''

        s_date = datetime.date(2001,1,1)
        e_date = s_date + datetime.timedelta(days=td+1)

        DAMslice.__init__(self, mon, sch, ech, self.genotype, comment, s_date.month, s_date.day, e_date.month, e_date.day, s_date.year)

    def getMonitorName(self, m, d=None, f=None):
        """
        return the REAL monitor name or 0 for a virtual one
        """

        if f != None and f >= 0 and d < self.metaFly[f].getTotalDays():
            output = self.metaFly[f].metaDay[d].monitor

        elif f == -1 and d != None and d != -1:
            all_mon = set()
            for fa in self.metaFly:
                try:
                    all_mon.add( fa.metaDay[d].monitor )
                except:
                    pass
            if len(all_mon) == 1:
                output = all_mon.pop()
            else:
                output = '0'

        else:
            output = '0'

        return output

    def getMonitorFlyName(self, f, d=None):
        """
        given the fly number in the matrix,
        returns the name of the monitor and the channel she was in
        """
        if d == -1: d = None

        monitor = self.metaFly[f].getMonitor(d)
        channel = self.metaFly[f].getChannel(d)
            
        return monitor, channel

    def getDate(self, d, f=None, format = 'mm/dd'):
        """
        Return a string with formatted Date for for the Nth day for the specified fly
        or else a crescent dayber if the fly is not specified
        format can use: m, mm, d, dd, yy, yyyy and / as separator
        """

        output = 'Day %s' % (d+1)

        dd = format.count('d')
        mm = format.count('m')
        yy = format.count('y')

        if f != None and f >= 0 and d < self.metaFly[f].getTotalDays(): #if we specified a fly, fetch and return the REAL data
            f = int(f)

            day_s = '%s' % ( str(self.metaFly[f].metaDay[d].date.day).zfill(dd) * (dd>0) )
            month_s = '%s' % ( str(self.metaFly[f].metaDay[d].date.month).zfill(dd) * (dd>0) )
            year_s = '%s' % ( str(self.metaFly[f].metaDay[d].date.year)[4-yy:] * (dd>0) )

            format = format.replace('d'*dd, day_s)
            format = format.replace('m'*mm, month_s)
            output = format.replace('y'*yy, year_s)

        elif f != None and int(f) == -1:
            f = int(f)
            day_s, month_s, year_s = set(), set(), set()

            for af in self.metaFly:
                try:
                    day_s.add(af.metaDay[d].date.day)
                    month_s.add(af.metaDay[d].date.month)
                    year_s.add(af.metaDay[d].date.year)
                except:
                    pass

            if (len(day_s) + len(month_s) + len(year_s)) == 3:

                day_s = '%s' % ( str(day_s.pop()).zfill(dd) * (dd>0) )
                month_s = '%s' % ( str(month_s.pop()).zfill(dd) * (dd>0) )
                year_s = '%s' % ( str(year_s.pop())[4-yy:] * (dd>0) )

                format = format.replace('d'*dd, day_s)
                format = format.replace('m'*mm, month_s)
                output = format.replace('y'*yy, year_s)


        return output

    def getHeader(self):
        """
        Return the initial information about the metaDAMslice as list
        the first item in the list is the DAMclass
        the second item are the default headers as list
        + any eventual needed item
        """
        return [metaSlice, self.Header + [self.metaFly]]




class metaFly(object):
    """
    The metafly class contains the details of a "metafly"
    """

    def __init__(self, genotype):
        self.genotype = genotype
        self.metaDay = []

    def AddStartDay(self, mon, ch, date, comment=''):
        """
        the first day of recording
        """
        start_day = metaDay(monitor=mon, channel=ch, date=date, comment=comment)
        self.metaDay.append(start_day)

    def AddTipDay(self, mon, ch, date, comment='', end=False):
        """
        day in which we tip the fly to a new monitor/channel
        """
        new_date = date
        last_metaDay = self.metaDay[-1]
        last_mon = last_metaDay.monitor
        last_channel = last_metaDay.channel
        last_comment = last_metaDay.comment
        last_date = last_metaDay.date

        interval = (new_date - last_date).days

        c = 1
        for d in range(interval-1):
            imDate = last_date + datetime.timedelta(days=c)
            imDay = metaDay(monitor=last_mon, channel=last_channel, date = imDate, comment=last_comment)
            self.metaDay.append (imDay)
            c += 1

        if not end:
            finalDay = metaDay(monitor=mon, channel=ch, date=date, comment=comment)
            self.metaDay.append(finalDay)

    def AddEndDay(self, date, comment=''):
        """
        The day we discard the fly
        """
        ch = 0
        mon = 0
        self.AddTipDay(mon, ch, date, comment, end=True)

    def getTotalDays(self):
        """
        How many days did we record
        """
        elapse = self.metaDay[-1].date - self.metaDay[0].date
        return elapse.days + 1
    
    def getMonitor(self, d=None):
        """
        return the monitor name for day d
        if d is not specified will return a set with the monitor names
        """
        if d != None and d!= -1:
            monitor = self.metaDay[d].monitor
        else:
            monitor = set()
            for mD in self.metaDay: monitor.add(mD.monitor)
        return monitor
        
    def getChannel(self, d=None):
        """
        return the channel name for day d
        if d is not specified will return a set with the channel names
        """
        if d != None and d!= -1:
            channel = self.metaDay[d].channel
        else:
            channel = set()
            for mD in self.metaDay: channel.add(mD.channel)
        return channel 
            
        
            

class metaDay(object):
    """
    the metaday class is used to create a meta DAMslice in which flies have different origins
    (for instance different monitors on different days)
    """
    def __init__(self, monitor, channel, date, comment=''):
        self.monitor = int(monitor)
        self.channel = int(channel)
        self.date = date
        self.comment = str(comment)

