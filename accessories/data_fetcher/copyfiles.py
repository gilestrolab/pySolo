#!/usr/bin/env python
# ####################################################################
#   Version 0.7
#   Versions now handled in version control
#
#   Before using, modify the variables in the copyfiles_config.py file
#
#   Use without parameters to fetch yesterday's data
#   or use "copyfiles -d year-mm-dd" to fetch data from a given day
#
#   Giorgio Gilestro <gilestro@gilest.ro>
#
# ####################################################################


import os, datetime, smtplib, sys, re
from zipfile import ZipFile, ZIP_DEFLATED
from time import mktime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

##from copyfiles_config_local import *
from copyfiles_config import *

#Here we define some variables that are used all over the place
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug','Sep', 'Oct', 'Nov', 'Dec']
errormsg = ''

def zipFile(path, zipFileName):
    '''
    if a not empty path is given will create a zip file containing all the files
    in the given path
    '''
    if path:
        zip = ZipFile(zipFileName, 'w', compression = ZIP_DEFLATED)
        for root, dirs, files in os.walk(path):
             for fileName in files:
                zip.write(os.path.join(root,fileName))
        zip.close()

def writeLog(filepath, msg):
    '''
    Write the error message in a logfile in a given directory. If no valid dir
    is given then write in the root of the output path
    '''

    logpath = ''
    msg = 'Log for: %s \n%s' % (startTime, msg)

    if filepath: # a not-empty string is == True
        logpath = os.path.join(filepath, 'logfile.txt')
    else:
        logpath = os.path.join(outputPath, 'logfile.txt')

    logfile = open(logpath, 'w')
    logfile.write(msg)
    logfile.close()

def sendMail(to, subject, text, files=[],server=SMTPmailserver):
    '''
    send an email containing the error message. A file could also be attached
    using this function
    '''

    global errormsg
    assert type(to)==list         #just make sure the we are using a list
    assert type(files)==list
    fro = 'The FlyDAM Data <gilestro@wisc.edu>'

    msg = MIMEMultipart()
    msg['From'] = fro
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    if files:

        for file in files:
            part = MIMEBase('application', "octet-stream")
            part.set_payload( open(file,"rb").read() )
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"'
                            % os.path.basename(file))
            msg.attach(part)

    smtp = smtplib.SMTP(server)
    smtpresult = smtp.sendmail(fro, to, msg.as_string() )
    smtp.close()

def createDayDir():
    '''
    Creates a new directory based on given date. The structure of the
    directory is outputPath/yyyy/mm/mmdd/
    '''
    global errormsg

    dirFullPath = os.path.join (outputDAMPath,
                                str(startTime.year),
                                str(startTime.month).zfill(2),
                                str(startTime.month).zfill(2) + str(startTime.day).zfill(2)
                                )

    if os.access(dirFullPath, os.F_OK):         #if the dir is accessible
        errormsg += 'Error: the directory for %s already exists! Files were not overwritten.\n' % startTime
        return ''
    else:
        os.makedirs(dirFullPath)
        return str(dirFullPath)

def processFile(inFile, outFile):
    '''
    Goes through the given file and copy those lines corresponding to given date
    to a new file in the output dir
    '''

    newcontent = ''
    remains = ''
    lineCount = 0
    global errormsg
    mon = 0

    try:
        mon = int(inFile[inFile.index('Monitor')+len('Monitor'):-4])
    except:
        pass

    if monNumber.count(mon):

        previousTime = startTime - datetime.timedelta(minutes=1)

        with open(inFile, 'rU') as inputfile:      #open the file for reading as inputfile U is for universal mode  - will work with Mac file

            for singleLine in inputfile: #goes through the file line by line
                line = singleLine.split('\t')   #split contents by tabs
                d, t = re.split('\W+', line[1]), re.split('\W+', line[2]) #split date and time
                lineDate = datetime.datetime(   2000+int(d[2]),               #year
                                                  months.index(d[1])+1,     #month as number
                                                  int(d[0]),                 #day
                                                  int(t[0]),                  #hour
                                                  int(t[1]),                 #minute
        ##                                          int(t[2]) )                #seconds
                                                  0 )                #seconds
                if startTime <= lineDate < endTime: # copy the line only if timing is correct

                    minDiff = (lineDate - previousTime)
                    minDiff = (minDiff.seconds)/60
                    if minDiff > 1 and correctErrors:
                        for i in range (1,minDiff):
                            newcontent += singleLine
                            lineCount +=1
                        errormsg += 'Error: Adding %s minutes to monitor: %s \n' % (i, inFile)


                    previousTime = lineDate
                    newcontent += singleLine
                    lineCount +=1
                else:
                    remains += singleLine

        inputfile.close()                   #close the file


        if lineCount != expectedLines and sameDay:
            print 'adjusting data for same day collection.\n Adding %s times last line' % (expectedLines - lineCount)
            for i in range(expectedLines - lineCount): newcontent += singleLine

        elif lineCount != expectedLines and not sameDay:
            errormsg += 'Error: I have found %s lines of data in file %s\n' % (lineCount, inFile)


        mm = str(startTime.month).zfill(2)
        dd = str(startTime.day).zfill(2)
        mon = outFile[outFile.index('Monitor')+len('Monitor'):-4].zfill(3)


        if use_monFile: #Writes proper contents in Monitor files (1 file = 1 monitor)

            outFile = outFile[:outFile.index('Monitor')] + '%s%sM%s.txt' % (mm, dd, mon)

            try:
                outputfile = open(outFile, 'w')
                outputfile.write(newcontent)
                outputfile.close()
            except:
                errormsg += 'Error: Cannot open or write into the monitor destination file %s\n' % outFile

        if use_chanFile: #Writes proper contents in Channel files (1 file = 1 channel)

            ch_matrix_r = []
            ch = 1
            ch_content = newcontent.split('\n')
            for line in ch_content[:-1]:
                ch_matrix_r.append(line.split('\t')[10:])

            ch_matrix = zip(*ch_matrix_r)

            t_date = '%s %s %s' % (dd, months[int(mm)-1], startTime.year)

            for channel in ch_matrix:

                ch_filename = '%s%sM%sC%s' % (mm,dd,mon, str(ch).zfill(2) )
                header = '%s   %s\n' % (ch_filename, t_date)
                header += '%s\n' % lineCount
                header += '%s\n' % 1 # what is this 1?
                header += '%s%s\n' % (str(startTime.hour).zfill(2), str(startTime.minute).zfill(2))
                header += ('\n'.join(channel))
                header += '\n'
                ch +=1

                ch_outFile = outFile[:outFile.index('Monitor')] + ch_filename + '.txt'

                try:
                    outputfile = open(ch_outFile, 'w')
                    outputfile.write(header)
                    outputfile.close()
                except:
                    errormsg += 'Error: Cannot open or write into the channel destination file %s\n' % outFile


        if remove_original_lines and not errormsg:
            try:
                RAWfile = open(inFile, 'w')
                RAWfile.write(remains)
                RAWfile.close()
            except:
                errormsg += 'Error: Cannot open or write into the original raw file %s\n' % inFile


#''' Here we start! '''
args = sys.argv
#show some helpful message through the commandline
if args.count('-h') or args.count('--help'):
    print ('''Usage: copyfiles [-d date] [-i path]\n\
    no options\t\t\tfetch yesterday\'s data with settings specified in config file\n\
    -d year-mm-dd\t\tfetch data for specified date\n\
    -i path\t\t\tuse specified path as inputpath\n\
        ''')
    exit()

#First get the date to be processed, either automatically (=yesterday) or through the commandline
#get startTime automatically
n=1
startTime = datetime.datetime.combine(datetime.date.today()-datetime.timedelta(days=n), datetime.time(startHour,startMinute))

#get startTime through the command line
if args.count('-d'):
    d = args.index('-d') + 1
    year, month, day = args[d].split('-')
    year = int(year)
    month = int(month)
    day = int(day)
    print year,month,day
    startTime = datetime.datetime(year,month,day,startHour,startMinute,00)


#Use provided path instead of the one specified in the config file
if args.count('-i'):
    i = args.index('-i') + 1
    pathname = args[i]
    if os.path.exists(pathname):
        print 'Using input directory %s' % s
        inputPath = pathname

#''' Do things here '''

print 'Processing data for date: %s/%s/%s' % (startTime.year, startTime.month, startTime.day)

#Are we fetching the data for today? In that case we will have to make up all the data that are missing
sameDay = False
today = datetime.datetime.today()
if (today - startTime).days <= 0: sameDay = True


endTime = startTime + datetime.timedelta(days=1) #end time is starttime + 1 day

expectedLines = int(mktime(endTime.timetuple())-mktime(startTime.timetuple()))/60
#expectedlines is automatically calculated to be end (sec) - start (sec) / 60 = min

filelist = os.listdir(inputPath)          #extract the list of files in the dir inputPath
if len(filelist) != len(monNumber):
    errormsg += 'Error importing data: %s monitor(s) were found\n' % len(filelist)

outputPath = createDayDir()

n=0
if outputPath:
    tot = len(filelist)
    for monFile in filelist:
        n+=1
        print 'processing file %s/%s' % (n,tot)
        processFile(os.path.join(inputPath, monFile), os.path.join(outputPath, monFile))
else:
    errormsg = 'The output folder alread exists! Process Aborted.'

errormsg = errormsg or 'All files were succesfully copied.\n'
writeLog (outputPath, errormsg)

zipFileName = str(startTime).split(' ')[0]+'.zip'
zipFileName = os.path.join(zippedDataPath, zipFileName)
zipFile(outputPath, zipFileName)

if send_email and attach_zipfile:
    sendMail(email_rcpts, '[DAM Data] %s' % startTime, errormsg, [zipFileName])
elif send_email and not attach_zipfile:
    sendMail(email_rcpts, '[DAM Data] %s' % startTime, errormsg)

print errormsg
