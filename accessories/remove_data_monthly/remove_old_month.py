#!/usr/bin/env python
# ########################################
# #   Last modification to this code
# #   on 07.02.2008
# ########################################

# HOW TO USE THIS PROGRAM
#
# Specify the folder where the real time collected data are stored
# Launch the program



import os, datetime
from zipfile import ZipFile, ZIP_DEFLATED
from time import mktime

#Here we define some variables that are used all over the place


try:
    inputPath = os.sys.argv[1]
except:
    inputPath = 'C:/Program Files/DAM Software/DAMSystem3Data/'

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug','Sep', 'Oct', 'Nov', 'Dec']
errormsg = ''

def processFile(inFile):
    '''
    Goes through the given file and copy those lines corresponding to given date
    to a new file in the output dir
    '''
    newcontent = ''
    global errormsg

    try:
        inputfile = open(inFile, 'r')       #open the file for reading as inputfile
        monData = inputfile.readlines()     #read contents of the file as a list of lines (strings)
        inputfile.close()                   #close the file
    except:
        errormsg += 'Error: Cannot open or read from file %s \n' % inFile

    for singleLine in monData: #goes through the file line by line; every line is a minute
        line = singleLine.split('\t')   #split contents by tabs
        d, t = line[1].split(' '), line[2].split(':') #split date and time by spaces or ':'

        lineDate = datetime.datetime(   2000+int(d[2]),               #year
                                          months.index(d[1])+1,     #month as number
                                          int(d[0]),                 #day
                                          int(t[0]),                  #hour
                                          int(t[1]),                 #minute
                                          int(t[2]) )                #seconds

        if lineDate.month == currentMonth: # copy the line only if it belongs to current month
            newcontent += singleLine

    try:
        RAWfile = open(inFile, 'w')
        RAWfile.write(newcontent)
        RAWfile.close()
    except:
        errormsg += 'Error: Cannot open or write into the original raw file %s\n' % inFile


def zipFile(path, zipFileName):
    '''
    if a not empty path is given will create a zip file containing all the files
    in the given path
    '''
    n = 0
    if path:
        zip = ZipFile(zipFileName, 'w', compression = ZIP_DEFLATED)
        for root, dirs, files in os.walk(path):
             n_files = len(files)
             for fileName in files:
                n+=1
                print 'processing file %s of %s' % (n, n_files)
                zip.write(os.path.join(root,fileName))


        zip.close()


#''' Here we start the program! '''

now = datetime.date.today() #full datetime of now
currentMonth = now.month # current Month in number (1 = January, 12=December)

filelist = os.listdir(inputPath)          #extract the list of files in the dir inputPath
tot = len(filelist)                     #number of files to be processed

#For backup purposes firstmMake a zip containing the current data

print 'Current month is %s' % months[currentMonth-1]
print 'First I make a Zip backup of all files'
print 'This will take a little bit'
zipFileName = '%s-%s.zip' % (now.year, str(currentMonth-1).zfill(2))
zipFile(inputPath, zipFileName)

print 'Now I am going to eliminate all the lines that have not been recorded this month.'

n = 0
for monFile in filelist:
    n+=1
    print 'processing file %s/%s' % (n,tot)
    processFile(os.path.join(inputPath, monFile))


print errormsg
