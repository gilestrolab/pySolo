#!/usr/bin/env python

#########################################################################
# Converts TriKinetics files from the channel format of TriKinetics to the monitor format
#
# channel file name = '%02s%02dM%03dC%02d.txt' % (month, day, monitor, channel)
# monitor file name = '%02s%02dM%03d.txt' % (month, day, monitor)
#
# last modification on 2008.12.05
#
# Giorgio Gilestro <gilestro@wisc.edu>
#
#########################################################################

import os, datetime, numpy

def channel2monitor(inputPath, ch_number, bin_number):
    '''
    converts a file from type channel to type monitor
    '''

    def readContent(yy, mm, dd, fileName ):
        '''
        reads the content of the channel filename
        and returns number of bins, start time and the actual content
        '''
        fh = open(fileName, 'r')
        content = fh.readlines()
        fh.close()
        bin_num = int(content[1])
        sh, sm = int(content[3][0:2]), int(content[3][2:4]) 
        content = content[4:]
        while '\n' in content: content = content.replace('\n', '')
        while '\r' in content: content = content.replace('\r', '')
        content = [int(line) for line in content]
        s_time = datetime.datetime(yy, mm, dd, sh, sm)
        return bin_num, s_time, content


    def time2str(t):
        '''
        format time in the proper way
        '''
        hh = t.hour
        mm = t.minute
        sec = 0
        return '%02d:%02d:%02d' % (hh, mm, sec)


    def write2monitorFile(yy, mm, dd, start_time, mon, matrix):
        '''
        write the whole matrix to a single file containing the data for all the channels
        '''

        outputPath = '/moredata/DAMm/%s/%02d/%02d%02d/' % (yy, mm, mm, dd)
        if not os.access(outputPath, os.F_OK): os.makedirs(outputPath)

        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug','Sep', 'Oct', 'Nov', 'Dec']
        filename = '%02s%02dM%03d.txt' % (mm, dd, mon)
        yy = str(yy)[2:4]
        time = start_time - datetime.timedelta(minutes=1)
        n = 0


        filename = os.path.join(outputPath, filename)
        fh = open(filename, 'w')
        
        matrix = matrix.transpose((1,0)) # rotate the matrix 90 degrees
        for line in matrix:
            n += 1
            m_name = month_names[mm-1]
            time = time + datetime.timedelta(minutes=1)  
            time2str(time)

            line_str = [str(v) for v in line]
            line_str = '\t'.join(line_str)
            header = '%s\t%s %s %s\t%s\t1\t' % (n, dd, m_name, yy, time2str(time))
            full_line = header + line_str+'\n'
            
            fh.write(full_line)
        fh.close()
        
            
    #here we create some sets to be used in the process
    monSet = set([])
    mmSet = set([])
    ddSet = set([])
    
    # collect the list of files in the specified folder 
    # and extract information from it
    fileList = os.listdir(inputPath) 
    for file in fileList:
        try:
            mm = int(file[0:2])
            dd = int(file[2:4])
            mon = int(file[5:8])
            ch = int(file[9:11])
            yy = 2006
            
            monSet.add(mon)
            mmSet.add(mm)
            ddSet.add(dd)
        except:
            print 'file %s was not added in folder %s' % (file, inputPath)
    
    # make sure that all the files in the same folder refer to the same month and day
    if len(mmSet) != 1 or len(ddSet) != 1:
        raise 'Error. The input path should contain data only from a day.\nMultiple days or months were found.'    
    
    ar = numpy.zeros((ch_number+6, bin_number), dtype=numpy.int)
    # starts going monitor by monitor and collects the data
    for mon in list(monSet):
        for ch in range(1,33):
            fileName = '%02s%02dM%03dC%02d.txt' % (mm, dd, mon, ch)
            fileName = os.path.join(inputPath, fileName)
            bin_n, start_time, content = readContent(yy, mm, dd, fileName)
            #there is an offset of 6 in the format for the lights
            ar[ch+5] = content
        
        write2monitorFile(yy, mm, dd, start_time, mon, ar)
        
        
            
        
# Here we start!        
if __name__ == '__main__':

    bin_number = 1440
    ch_number = 32


    yy = 2006
    mm = [12]
    dd = [13, 14, 15, 16, 17, 18, 19]
    
    for m in mm:
        for d in dd:
            inputPath = '/home/gg/Desktop/%s/%02d/%02d%02d/' % (yy, m, m, d)
            channel2monitor(inputPath, ch_number, bin_number)
            
    
    



    