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


import os, datetime, smtplib, optparse, glob, re
from zipfile import ZipFile, ZIP_DEFLATED
import ConfigParser
from calendar import month_abbr

from time import mktime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

#Here we define some variables that are used all over the place
__version__ = 0.93


class cp_config():
    """
    Handles program configuration
    Uses ConfigParser to store and retrieve
    """
    def __init__(self, filename=None):
        
        filename = filename or 'copyfiles.cfg'
        pDir = os.getcwd()
        if not os.access(pDir, os.W_OK): pDir = os.environ['HOME']

        self.filename = os.path.join (pDir, filename)
        
        self.config = None

        self.defaultOptions = { "startTime" : ['09:00', "The time at which the day starts for flies", 'text'],
                                "monitors" :  ['1-4', "The first and the last monitors of the series you want to use", 'text'],
                                "cleanInput" : [False, "If True will remove the lines from the original files! Use with extreme caution!", 'boolean'],
                                "correctErrors" : [False, "Used to add bins if some are lost", 'boolean'],
                                "send_email" : [False, "Do we want to send an email with the script's summary?", 'boolean'],
                                "SMTPmailserver" : ['smtp.mail.edu', "you need to specify your own SMTP server here. This will not work for you", 'text'],
                                "email_username" : ['', "Credentials for your smtp account", 'text'],
                                "email_password" : ['', "Credentials for your smtp account", 'password'],
                                "email_rcpts" : ['your@email.com', "List of recipients. Separate using comma", 'text'],
                                "attach_zipfile" : [True, "The zip file can be attached to the email", 'boolean'],
                                "use_monFile" : [True, "Use TriKinetics monitor format", 'boolean'],
                                "use_chanFile" : [False, "Use TriKinetics channel format", 'boolean'],
                                "inputPath" : ['/', "The path to where your raw data are stored", 'path'],
                                "outputPath" : ['/', "The path to where your processed data are stored", 'path'],
                                "zipPath" : ['/', "The path to where the zipped files are stored", 'path'],
                                "file_prefix" : [ 'Monitor', "Prefix of filenames", 'text']
                               }
        self.Read()
        
    def Read(self):
        """
        read the configuration file. Initiate one if does not exist
        """
        
        if os.path.exists(self.filename):
            self.config = ConfigParser.RawConfigParser()
            self.config.read(self.filename)   
            
        else:
            self.Save(newfile=True)

    def Save(self, newfile=False):
        """
        """
            
        if newfile:
            self.config = ConfigParser.RawConfigParser()
            self.config.add_section('Options')
            
            for key in self.defaultOptions:
                self.config.set('Options', key, self.defaultOptions[key][0])

        with open(self.filename, 'wb') as configfile:
            self.config.write(configfile)
            
        log.output ('A new configuration file was just created. Change values inside before continuing')

    def SetValue(self, section, key, value):
        """
        """
        
        if not self.config.has_section(section):
            self.config.add_section(section)
        
        self.config.set(section, key, value)
        
    def GetValue(self, section, key):
        """
        get value from config file
        Does some sanity checking to return tuple, integer and strings 
        as required.
        """
        r = self.config.get(section, key)
        
        if type(r) == type(0) or type(r) == type(1.0): #native int and float
            return r
        elif type(r) == type(True): #native boolean
            return r
        elif type(r) == type(''): #string
            #r = r.split(',')
            pass
        
        if len(r) == 2: #tuple
            r = tuple([int(i) for i in r]) # tuple
        
        elif len(r) < 2: #string or integer
            try:
                r = int(r[0]) #int as text
            except:
                r = r[0] #string
        
        if r == 'False' or r == 'True':
            r = (r == 'True') #bool
        
        return r
                

    def GetOption(self, key):
        """
        """
        return self.GetValue('Options', key)
        
    

class customLogger():
    def __init__(self, verbose=True):
        self.errorlog = ''
        self.outputlog = ''
        self.log = ''
        self.successmessage = 'All monitors were succesfully copied'
        self.verbose = verbose
        
    def error(self, txt):
        self.log += '\nError:' + str(txt)
        self.errorlog += '\n' + str(txt)
        if self.verbose:
            print >>os.sys.stderr, txt
        
    def output(self, txt):
        self.log += '\nOutput:' + str(txt)
        self.outputlog += '\n' + str(txt)
        if self.verbose:
            print >>os.sys.stdout, txt

    def getLog(self):
        if not self.errorlog: self.log += '\n' + self.successmessage
        return self.log + '\n'
        
    def hasError(self):
        return (self.errorlog != '')
        
    def write(self, filepath):
        """
        Write the log message in a logfile in a given directory. If no valid dir
        is given then write in the root of the output path
        """

        if filepath and os.path.exists(filepath): 
            logpath = os.path.join(filepath, 'logfile.txt')
        else:
            logpath = 'logfile.txt'

        logfile = open(logpath, 'w')
        logfile.write( self.getLog() )
        logfile.close()

        self.__init__()

 
 
def zipFile(path, zipFileName):
    """
    if a not empty path is given will create a zip file containing all the files
    in the given path
    """
    if os.path.exists(path):
        zip = ZipFile(zipFileName, 'w', compression = ZIP_DEFLATED)
        for root, dirs, files in os.walk(path):
             for fileName in files:
                zip.write(os.path.join(root,fileName))
        zip.close()


def sendMail(to, subject, text, server, username=None, password=None, files=[]):
    """
    send an email containing the error message. A file could also be attached
    using this function
    """

    assert type(to)==list         #just make sure the we are using a list
    assert type(files)==list
    fro = 'The FlyDAM Data'

    isGmail = 'gmail' in server or 'google' in server

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


    port = [25, 587][isGmail*1]
    smtp = smtplib.SMTP(server, port)
    
    if isGmail: smtp.ehlo(); smtp.starttls(); smtp.ehlo()
    if username and password: smtp.login(username, password)
    
    smtpresult = smtp.sendmail(fro, to, msg.as_string() )
    smtp.close()

def createDayDir(rootpath, date, overwrite=False):
    """
    Creates a new directory based on given date. The structure of the
    directory is outputPath/yyyy/mm/mmdd/
    """

    dirFullPath = os.path.join (rootpath,
                                str(date.year),
                                str(date.month).zfill(2),
                                str(date.month).zfill(2) + str(date.day).zfill(2)
                                )

    if os.path.exists(dirFullPath) and not overwrite:
        log.error ( 'The directory for %s already exists! Files were not overwritten.\n' % date )
        return ''
    else:
        try:
            os.makedirs(dirFullPath)
        except:
            pass
        return str(dirFullPath)

def processFile(inFile, outFile, startTime, dataType=0, correctErrors=True, cleanInput=False):
    """
    Goes through the given file and copy those lines corresponding to given date
    to a new file in the output dir
    

    inFile         full path to file    File to be used as input
    outFile        full path to file    File to be written as output
    startTime      datetime time        Starting time - Will collect 24 hours of data

    dataType       0 (Default)          Monitor mode 
                   1                    Channel mode
                   
    """

    newcontent = ''
    remains = ''
    lineCount = 0

    #Are we fetching the data for today? In that case we will have to make up all the data that are missing
    sameDay = ( (datetime.datetime.today() - startTime).days <= 0 )
    endTime = startTime + datetime.timedelta(days=1) #end time is starttime + 1 day
    #expectedlines is automatically calculated to be end (sec) - start (sec) / 60 = min
    expectedLines = int(mktime(endTime.timetuple())-mktime(startTime.timetuple()))/60

    previousTime = startTime - datetime.timedelta(minutes=1)

    with open(inFile, 'rU') as inputfile:      #open the file for reading as inputfile U is for universal mode  - will work with Mac file

        for singleLine in inputfile: #goes through the file line by line
            line = singleLine.split('\t')   #split contents by tabs
            try:
                d, t = re.split('\W+', line[1]), re.split('\W+', line[2]) #split date and time
            except:
                print line
            
            lineDate = datetime.datetime(    (int(d[2]) < 2000)*2000 + int(d[2]),               #year
                                              [m for m in month_abbr].index(d[1]),     #month as number
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
                    log.error ( 'Adding %s minutes to monitor: %s \n' % (i, inFile) )


                previousTime = lineDate
                newcontent += singleLine
                lineCount +=1
            else:
                remains += singleLine

    inputfile.close()                   #close the file


    if lineCount != expectedLines and sameDay:
        log.output ( 'Adjusting data for same day collection.\n Adding %s times last line' % (expectedLines - lineCount) )
        for i in range(expectedLines - lineCount): newcontent += singleLine

    elif lineCount != expectedLines and not sameDay:
        log.error ( 'I have found %s lines of data in file %s\n' % (lineCount, inFile) )


    mm = str(startTime.month).zfill(2)
    dd = str(startTime.day).zfill(2)
    FT = FILE_PREFIX[0].upper()
    mon = outFile[outFile.index(FILE_PREFIX)+len(FILE_PREFIX):-4].zfill(3)


    if dataType == 0: #Writes proper contents in Monitor files (1 file = 1 monitor)

        outFile = outFile[:outFile.index(FILE_PREFIX)] + '%s%s%s%s.txt' % (mm, dd, FT, mon)

        try:
            outputfile = open(outFile, 'w')
            outputfile.write(newcontent)
            outputfile.close()
        except:
            log.error ( 'Cannot open or write into the monitor destination file %s\n' % outFile )

    elif dataType == 1: #Writes proper contents in Channel files (1 file = 1 channel)

        ch_matrix_r = []
        ch = 1
        ch_content = newcontent.split('\n')
        for line in ch_content[:-1]:
            ch_matrix_r.append(line.split('\t')[10:])

        ch_matrix = zip(*ch_matrix_r)

        t_date = '%s %s %s' % (dd, month_abbr[int(mm)], startTime.year)

        for channel in ch_matrix:

            ch_filename = '%s%sM%sC%s' % (mm,dd,mon, str(ch).zfill(2) )
            header = '%s   %s\n' % (ch_filename, t_date)
            header += '%s\n' % lineCount
            header += '%s\n' % 1 # what is this 1?
            header += '%s%s\n' % (str(startTime.hour).zfill(2), str(startTime.minute).zfill(2))
            header += ('\n'.join(channel))
            header += '\n'
            ch +=1

            ch_outFile = outFile[:outFile.index(FILE_PREFIX)] + ch_filename + '.txt'

            try:
                outputfile = open(ch_outFile, 'w')
                outputfile.write(header)
                outputfile.close()
            except:
                log.error ( 'Cannot open or write into the channel destination file %s\n' % outFile )


    if cleanInput and not log.hasError():
        try:
            RAWfile = open(inFile, 'w')
            RAWfile.write(remains)
            RAWfile.close()
        except:
            log.error ( 'Cannot open or write into the original raw file %s\n' % inFile )


if __name__ == "__main__":

    log = customLogger()

    usage =  '%prog [options] [argument]\nNo options\t\tfetch yesterday\'s data with settings specified in config file'
    version= '%prog version ' + str(__version__)
    
    parser = optparse.OptionParser(usage=usage, version=version )
    parser.add_option('-d', '--date', dest='date', metavar="YYYY-MM-DD", help="Fetch data for specified date")
    parser.add_option('-p', '--period', dest='period', metavar="YYYY-MM-DD/YYYY-MM-DD", help="Fetch data for specified period")
    parser.add_option('-i', '--input', dest='path', metavar="PATH", help="Use specified path as inputpath")
    parser.add_option('-c', '--config', dest='cfg_file', metavar="CONFIG", help="Use specified config file")
    parser.add_option('--overwrite', action="store_true", default=False, dest='overwrite', help="Write over currently existing files and directories")

    (options, args) = parser.parse_args()

    ### Getting date or period

    cfg_file = options.cfg_file or 'copyfiles.cfg'
    opts = cp_config(cfg_file)
    
    startHour, startMinute = [int(v) for v in opts.GetOption('startTime').split(':')]

    if options.date:
        year_s, month_s, day_s = [int(v) for v in options.date.split('-')]
        startTime = datetime.datetime(year_s,month_s,day_s,startHour,startMinute,00)
        collectDays = 1
    else:
        startTime = datetime.datetime.combine(datetime.date.today()-datetime.timedelta(days=1), datetime.time( startHour, startMinute ) )
        collectDays = 1
        

    if options.period:
        startdate, enddate = options.period.split('/')
        year_s, month_s, day_s = [int(v) for v in startdate.split('-')]
        year_e, month_e, day_e = [int(v) for v in enddate.split('-')]
        startTime = datetime.datetime(year_s,month_s,day_s,startHour,startMinute,00)
        endDate = datetime.datetime(year_e,month_e,day_e,startHour,startMinute,00)
        collectDays = (endDate - startTime).days + 1

    ###
    
    ### Getting input Files, output path and monitors to collect
    monitors = []
    mons = opts.GetOption('monitors').split(';')
    FILE_PREFIX = opts.GetOption('file_prefix')
    
    for series in mons:
        if '-' in series:
            m_s, m_e = [ int(v) for v in series.split('-') ]
        elif ',' in series:
            m_s, m_e = [ int(v) for v in series.split(',') ]
        else:
            m_s = m_e = int(series)
        monitors = list(set(monitors + range(m_s, m_e + 1)))
    

    if options.path and os.path.exists(options.path):
        inputPath = options.path
    else:
        inputPath = opts.GetOption('inputPath')

    log.output( 'Using input directory %s' % inputPath )
    
    dam_filelist = glob.glob(os.path.join(inputPath, '%s*.txt' % FILE_PREFIX) )
    #dam_filelist = [f for f in os.listdir(os.path.join(inputPath)) if FILE_PREFIX in f] 
    rootOutputPath = opts.GetOption('outputPath')

    ###
    
    mail_send = opts.GetOption('send_email')
    mail_attach = opts.GetOption('attach_zipfile')

    mail_rcpt = [opts.GetOption('email_rcpts')]
    mail_server = opts.GetOption('SMTPmailserver')
    mail_username = opts.GetOption('email_username') or None
    mail_password = opts.GetOption('email_password') or None


    #DAM monitors
    for day in range(collectDays):

        log.output( 'Processing data for date: %s/%s/%s' % (startTime.year, startTime.month, startTime.day) )
        outputPath = createDayDir(rootOutputPath, startTime, options.overwrite)
        
        if outputPath:
            if len(dam_filelist) < len(monitors):
                log.error ( 'Will not import all data: %s monitor(s) were found. Expecting %s\n' % ( len(dam_filelist), len(monitors) ) )

            for n, monFile in enumerate(dam_filelist):
                fname = os.path.split(monFile)[-1]

                #log.output ( 'Found file %s/%s: %s' % (n+1, len(dam_filelist), fname) )
                    
                try:
                    mon = int(fname[fname.index(FILE_PREFIX)+len(FILE_PREFIX):-4])
                except:
                    log.error( 'Could not determine monitor number. Check that your files are properly named (e.g.: Monitor001.txt)' )
                
                if monitors.count(mon):
                    log.output ( 'Processing file: %s' % (fname) )
                    processFile( monFile, os.path.join(outputPath, fname), startTime, correctErrors=opts.GetOption('correctErrors'), cleanInput=opts.GetOption('cleanInput') )
                else:
                    log.output ( 'Skipping file: %s' % (fname) )
                    
        else:
            log.error ( 'The output folder already exists! Process Aborted.' )


        zipFileName = str(startTime).split(' ')[0]+'.zip'
        zipFileName = os.path.join(opts.GetOption('zipPath'), zipFileName)
        zipFile(outputPath, zipFileName)
        
        log.write( outputPath )

        if mail_attach:
            mail_attachzip = [zipFileName]
        else:
            mail_attachzip = []
        
        if mail_send:
            sendMail(mail_rcpt, '[DAM Data] %s' % startTime, log.getLog(), files=mail_attachzip, server=mail_server, username=mail_username, password=mail_password)

        startTime += datetime.timedelta(days=1)


        
