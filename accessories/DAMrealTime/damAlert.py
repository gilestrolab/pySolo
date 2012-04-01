#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  damAlert.py
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


from DAMrealtime import DAMrealtime

base_path = '/home/gg/Desktop/test/'

email = dict (
              sender = 'g.gilestro@imperial.ac.uk',
              recipient  = 'giorgio.gilestro@gmail.com',
              server = 'automail.cc.ic.ac.uk'
              )


d = DAMrealtime(path=base_path, email=email, useEnvironmental=True)

DAM_problems = [( fname, d.getDAMStatus(fname) ) for fname in d.listDAMMonitors() if d.getDAMStatus(fname) == '50']
ENV_problems = [( fname, d.hasEnvProblem(fname) ) for fname in d.listEnvMonitors() if d.hasEnvProblem(fname)]


if DAM_problems: d.alert(DAM_problems)
if ENV_problems: d.alert(ENV_problems)





