#!/usr/bin/env python
#########################################################################
# Converts TriKinetics files from the monitor format of TriKinetics to the channel format
#
# monitor file name = '%02s%02dM%03d.txt' % (month, day, monitor)
# channel file name = '%02s%02dM%03dC%02d.txt' % (month, day, monitor, channel)
#
# last modification on 2009.1.05
#
# Giorgio Gilestro <gilestro@wisc.edu>
#
# Go to line 84 to operate
#
#########################################################################


import os, datetime
errormsg = ''
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug','Sep', 'Oct', 'Nov', 'Dec']


def processFile(inFile, outFile, mon):
    '''
    Goes through the given file and copy those lines corresponding to given date
    to a new file in the output dir
    '''

    newcontent = ''
    remains = ''
    lineCount = 0
    global errormsg

    inputfile = open(inFile, 'r')       #open the file for reading as inputfile
    monData = inputfile.readlines()     #read contents of the file as a list of lines (strings)
    inputfile.close()                   #close the file
            
    singleLine = monData[0] #goes through the file line by line
    line = singleLine.split('\t')   #split contents by tabs
    d, t = line[1].split(' '), line[2].split(':') #split date and time by spaces or ':'

    lineDate = datetime.datetime(   2000+int(d[2]),               #year
                                      months.index(d[1])+1,     #month as number
                                      int(d[0]),                 #day
                                      int(t[0]),                  #hour
                                      int(t[1]),                 #minute
##                                          int(t[2]) )                #seconds
                                      0 )                #seconds

    mm = str(lineDate.month).zfill(2)
    dd = str(lineDate.day).zfill(2)


    #Writes proper contents in Channel files (1 file = 1 channel)

    ch_matrix_r = []
    ch = 1
    ch_content = monData#.split('\n')
    for line in ch_content[:-1]:
        ch_matrix_r.append(line.split('\t')[10:])

    ch_matrix = zip(*ch_matrix_r)

    t_date = '%s %s %s' % (dd, months[int(mm)-1], lineDate.year)

    for channel in ch_matrix:

        ch_filename = '%s%sM%sC%s' % (mm,dd,mon, str(ch).zfill(2) )
        header = '%s   %s\n' % (ch_filename, t_date)
        header += '%s\n' % 1440
        header += '%s\n' % 1 
        header += '%s%s\n' % (str(lineDate.hour).zfill(2), str(lineDate.minute).zfill(2))
        header += ('\n'.join(channel))
        header += '\n'
        ch +=1

        ch_filename = ch_filename + outputFileExtension
        ch_outFile = os.path.join (outFile, ch_filename)

        outputfile = open(ch_outFile, 'w')
        outputfile.write(header)
        outputfile.close()


#''' Here we start! '''

#change these values as you need it
year = 2008
month = 12
day = 26
inputPath = '/media/fellini/DAM/'
outputPath = '/moredata/DAMc/'
outputFileExtension = '' # '.txt'

#
datePath = '%04d/%02d/%02d%02d/' % (year, month, month, day)
inputPath = os.path.join(inputPath, datePath)
outputPath = os.path.join(outputPath, datePath)


filelist = os.listdir(inputPath)          #extract the list of files in the dir inputPath
if not os.access(outputPath, os.F_OK): os.makedirs(outputPath)

n=0
if outputPath:
    tot = len(filelist)
    for monFile in filelist:
        n+=1
        print 'processing file %s/%s' % (n,tot)
        try:
            mon = int(monFile[5:8])
            processFile(os.path.join(inputPath, monFile), outputPath, mon)
        except:
            pass
else:
    errormsg = 'The output folder alread exists! Process Aborted.'

