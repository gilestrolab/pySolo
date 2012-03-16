#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  damAlert.py
#  
#  Copyright 2012 Giorgio Gilestro <gg@wolfson>
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


path = '/home/gg/Desktop/DAM/DAMSystem3Data'

email_sender = 'g.gilestro@imperial.ac.uk'
email_recipient = ['Giorgio Gilestro', 'giorgio.gilestro@gmail.com']
email_server = 'automail.cc.ic.ac.uk'


def scan(filename):
    '''
    scan given filename and return value for the last line
    '''
    fh = open (filename, 'r')
    lastline = fh.read().split('\n')[-2]
    fh.close()
    
    value = lastline.split('\t')[3]
    
    return value

def listFiles(path):
    '''
    '''
    dirList=os.listdir(path)
    l = [os.path.join(path, f) for f in dirList if 'Monitor' in f]
    return l

def alert(problems):
    '''
    '''
    
    now = datetime.datetime.now()
    message = 'At %s, found problems with the following monitors:\n' % now
    
    for (monitor, value) in problems:
        message += '%s\t%s\n' % (os.path.split(monitor)[1], value)


    sender = email_sender
    recipients = [ email_recipient[1] ]
    
    msg = MIMEMultipart()
    msg['From'] = 'Fly Dam Alert service'
    msg['To'] = '%s <%s>' % (email_recipient[0], email_recipient[1])
    msg['Subject'] = 'flyDAM alert!'


    try:
        text = MIMEText(message, 'plain')
        msg.attach(text)

        s = smtplib.SMTP(email_server)
        s.sendmail( sender, recipients, msg.as_string() )
        s.quit()

        print msg.as_string()

    except SMTPException:
       print "Error: unable to send email"


def main():
    
    problems = [( fname, scan(fname) ) for fname in listFiles(path) if scan(fname) == '50']
    if problems: alert(problems)

if __name__ == '__main__':
	main()

