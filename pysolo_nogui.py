#!/usr/bin/env python
from pysolo_lib import *

filename = '/data/Work/sleepData/test4.dad'
allDAMs = LoadDADFile(filename) #allDAMs is a list of DAMslices

fake_tree_selection = [0,0,0,-1,-1] #see the tree coordinates section in the documentation
g, m, d, f = fake_tree_selection[1:]

cSEL = allDAMs[g]           
fs, fe = cSEL.getFliesInInterval(m, f)
ds, de = cSEL.getDaysInInterval(d)
t0, t1 = 0, 1440

ax, s5, s30 = cSEL.filterbyStatus(ds,de,fs,fe,t0,t1, status=5)
print ax.shape                                  
                                  
#ax, s5 and s30 are all numpy masked 3-dimensional arrays
#containing
#ax ->  activity count
#s5 ->  sleep for 5 mins
#s30 -> sleep for 30 mins
