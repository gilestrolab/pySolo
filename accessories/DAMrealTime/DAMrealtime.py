#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  DAMrealtime.py
#  
#  Copyright 2012 Giorgio Gilestro <giorgio@gilest.ro>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import os, datetime, smtplib
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
import numpy as np
import serial

class DAMrealtime():
    def __init__(self, path, email=None):
        '''
        '''
        
        self.path = path
        
        if email:
            self.email_sender = email['sender']
            self.email_recipient = email['recipient']
            self.email_server = email['server']

    def getStatus(self, filename):
        '''
        scan given filename and return last recorded monitor status
        '''
        fh = open (filename, 'r')
        lastline = fh.read().split('\n')[-2]
        fh.close()
        
        value = lastline.split('\t')[3]
        
        return value

    def getAsleep(self, filename, interval=5):
        '''
        Scan the specified filename and return which one of the channels
        has not been moving for the past "interval" minutes
        Format of the DAM files is:
        1	09 Dec 11	19:02:19	1	0	1	0	0	0	?		[actual_activity]
        '''
        
        interval_for_dead = 30 #dead if they haven't moved in this time
        
        fh = open (filename, 'r')
        lastlines = fh.read().split('\n')[ - (2+interval_for_dead) : -2]
        fh.close()
        
        activity = np.array( [ line.split('\t')[10:] for line in lastlines ], dtype=np.int )
        
        # dead because they didn't move for the past 30 mins
        dead = ( activity.sum(axis=0) == 0 ) * 1
        # didn't move in the past 5
        asleep =  ( activity[-interval:].sum(axis=0) == 0 ) * 1
        # did move in the past 5
        awake = ( activity[-interval:].sum(axis=0) != 0 ) * 1
        # asleep but not dead
        sleepDep = asleep - dead
        
        return sleepDep
        
    
    def deprive(self, fname, port, interval=5, baud=57600):
        '''
        check which flies are asleep and send command to arduino
        connected on serial port
        '''
        
        asleep = self.getAsleep(fname, interval)
        command = [str(n+1) for (n,a) in enumerate(asleep) if a] 
        command = '\n'.join(command)
        
        try:
                ser = serial.Serial(port, baud)
                ser.write(commmand)
                ser.close()
        except:
                print 'Error communicating with the serial port!'
                os.sys.exit(404)
        
        return command

    def listFiles(self, prefix='Monitor'):
        '''
        list all monitor files in the specified path.
        prefix should match the file name
        filename        prefix

        Monitor01.txt   Monitor
        MON01.txt       MON
        '''
        
        l = ''
        
        if not os.path.isfile(self.path):
                dirList=os.listdir(self.path)
                l = [os.path.join(self.path, f) for f in dirList if prefix in f]
        
        elif prefix in self.path:
                l = [self.path]
                
                
        return l

    def alert(self, problems):
        '''
        problems is a list of tuples
        each tuple contains two values: the filename where the problem
        was detected, and the problem
        
        problems = [('Monitor1.txt','50')]
        
        '''
        
        now = datetime.datetime.now()
        message = 'At %s, found problems with the following monitors:\n' % now
        
        for (monitor, value) in problems:
            message += '%s\t%s\n' % (os.path.split(monitor)[1], value)


       
        msg = MIMEMultipart()
        msg['From'] = 'Fly Dam Alert service'
        msg['To'] = ','.join( self.email_recipient )
        msg['Subject'] = 'flyDAM alert!'


        try:
            text = MIMEText(message, 'plain')
            msg.attach(text)

            s = smtplib.SMTP(email_server)
            s.sendmail( self.email_sender, self.email_recipient, msg.as_string() )
            s.quit()

            print msg.as_string()

        except SMTPException:
           print "Error: unable to send email"

