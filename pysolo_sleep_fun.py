#####
## ARRAY MANIPULATIVE FUNCTIONS
#####
## The current numpy/scipy version seem to have some problem manipulating some
## masked arrays or nan arrays so here we overcome with custom made functions
## hopefully they soon will be obsolete

import numpy as np
import scipy.stats.stats as stats
from numpy.ma import *


def hasMasked(a, axis=None):
    '''
    Return True if there are Masked values along the given axis.
    '''

    a, axis = _chk_asarray (a, axis)

    if axis == None:
        a = a.ravel()
        axis = 0

    return (np.ma.getmask(a).sum(axis) != 0 )

def permute(listPerm):
    '''
    Return all possible and different permutations of a list
    '''
    np = []

    for i in range(0,len(listPerm)):
        for p in range (i, len(listPerm)):
            if i != p:
                np.append((listPerm[i], listPerm[p]))

    return np

def hasNaN(a):
    '''
    return True if the target is a NaN or if it's an array containing NaNs
    '''

    a = np.asarray(a)
    return np.isnan(a).any()

def std(a, axis=None):
    '''
    Return std value along the given axis.
    It is able to discriminate between masked and unmaked array and
    behave accordingly
    '''

    a, axis = _chk_asarray (a, axis)

    if axis == None:
        a = a.ravel()

    if np.shape(a) == ():
        axis = None

    if not np.isscalar(a):
        std_out =  a.std(axis)
    else:
        std_out = 0.

    return std_out

def stde(a, axis=None):
    '''
    Calculates the standard error of a distribution
    '''
    if axis == None:
        a = a.ravel()
        axis = 0

    if np.shape(a) == ():
        stde_out = 0.0

    else:
        masked = np.ma.getmask(a).any()

        if masked:
            stde_out =  (a.std(axis) / np.sqrt(a.count(axis)))
        else:
            stde_out = ( std(a, axis) / np.sqrt(a.shape[axis]))

    return stde_out


## Sleep Specific Functions

def isAllMasked(a):
    '''
    Return true if all the contents of the given array are masked objects
    '''
    return np.ma.getmask(a).all()



def SleepAmountByFly(s5, t0=None, t1=None ):
    '''
    SleepAmountByFly(s5, t0=None, t1=None )

    Takes the 3D array s5 and returns a 2D array containing
    the amount of sleep for each fly, for each day between the time interval t0, t1

    '''
    return s5[:,:,t0:t1].sum(axis=2)

def ActivityIndexByFly(ax, s5, t0=None, t1=None):
    '''
    ActivityIndexByFly(ax, s5, t0=None, t1=None)

    Takes the 3D arrays ax and s5 and returns a 2D array containing
    the AI for each fly, for each day between the time interval t0, t1

    '''

    tot_activity = ax[:,:,t0:t1].sum(axis=2)
    tot_wake_time = float(ax.shape[2]) - s5[:,:,t0:t1].sum(axis=2)

    return tot_activity / tot_wake_time


def number_sleep_episodes(s5, t0 = None, t1 = None):
    '''
    Returns the length of all sleep episodes in the given interval (t0,t1)
    '''
    d = len(s5.shape)
    if d == 1: s5 = s5.reshape((1,1,-1))
    if d == 2: s5 = s5.reshape((1,-1,-1))
    
    s5_1 = s5[:,:,t0:t1]

    s5_1[:,:,0]=0 #WE NEED TO DO THIS
    s5_2 = np.roll(s5_1, -1, axis=2) #copy and roll everything 1 position on the left
    # subtract the two.
    trans = s5_1 - s5_2
    # in the resulting array 
    # 0 indicates continuity
    # -1 indicates W->S transition
    # +1 indicates S->W transition
    w2s = (trans == -1)

    return w2s.sum(axis = 2)

def sleep_latency(s5, lightsoff=720):
    """
    returns sleep latency in minutes, that is time between lights off and first recorded sleep episode of at least 5 minutes
    """
    grid = np.indices(s5.shape)[-1] # compile a grid containing the indices of the array
    k = grid * s5 # keep only the indices where s5 is 1
    
    sl = np.argmax(k > lightsoff, axis=-1) - lightsoff
    return np.ma.masked_less(sl, 0)
    

def all_sleep_episodes(s5, t0 = None, t1 = None):
    '''
    Returns the length of all sleep episodes in the given interval (t0,t1)
    '''
    d = len(s5.shape)
    if d == 1: s5 = s5.reshape((1,1,-1))
    if d == 2: s5 = s5.reshape((1,-1,-1))
    
    s5_1 = s5[:,:,t0:t1]

    s5_1[:,:,0]=0 #WE NEED TO DO THIS
    s5_2 = np.roll(s5_1, -1, axis=2) #copy and roll everything 1 position on the left
    # subtract the two.
    trans = s5_1 - s5_2
    # in the resulting array 
    # 0 indicates continuity
    # -1 indicates W->S transition
    # +1 indicates S->W transition
    
    # now takes the coordinates on the third dimension of where the transition w2s occurred
    w2s = np.ma.where(trans == -1)[2]
    #do the same on the other transition
    s2w = np.ma.where(trans == 1)[2]

    #subtract one from the other to know length in minutes
    return (s2w - w2s)

def ba(s5, t0 = None, t1 = None):
    '''
    Compute brief awakenings analysis.
    A brief awakening is defined as 1 minute of activity between two stretches of sleep.
    returns an array "ba". the number of ba can be obtained as ba.sum(axis=2) 
    '''
    
    s5_1 = s5[:,:,t0:t1]
    s5_2 = np.roll(s5_1, -1, axis=2)
    s5_3 = np.roll(s5_1, +1, axis=2)
    
    # we subtract the value of position +1 and -1 frm position 0
    ba_1 = s5_1 - (s5_2 + s5_3)
    ba_2 = (ba_1 == -2)
    
    # lastly we convert the data_type from boolean to integer and we return it 
    dt = s5.dtype
    return ba_2.astype(dt)


def concatenate(arrays, axis=0):
    '''
    We need to bypass the crash in case the user is doing a concatenation he should not
    this functions try to understand on which axis do the concatenation 
    axis can be the number referring to the axis or 'auto'
    '''
    try:
        return np.ma.concatenate (arrays, axis)
    except:
        return arrays[0]
         

def _chk_asarray(a, axis = None):

    a = np.ma.asarray(a)

    if axis is None:
        a = a.ravel()
        outaxis = 0
    else:
        outaxis = axis
    return a, outaxis

def _chk2_asarray(a, b, axis = None):
    if axis is None:
        a = a.ravel()
        b = b.ravel()
        outaxis = 0
    else:
        a = np.ma.asarray(a)
        b = np.ma.asarray(b)
        outaxis = axis
    return a, b, outaxis


def ttest_ind(a, b, axis=0):
    """Calculates the t-obtained T-test on TWO INDEPENDENT samples of scores
    a, and b.  From Numerical Recipies, p.483. Axis can equal None (ravel
    array first), or an integer (the axis over which to operate on a and b).

    Returns: t-value, two-tailed p-value
    """


    a, b, axis = _chk2_asarray(a, b, axis)

    x1 = np.average( a, axis)
    x2 = np.average( b, axis)
    v1 = a.var(axis)
    v2 = b.var(axis)

    if np.ma.getmask(a).any():
        n1 = a.shape[axis] - a.mask.sum(axis)
    else:
        n1 = a.shape[axis]

    if np.ma.getmask(b).any():
        n2 = b.shape[axis] - b.mask.sum(axis)
    else:
        n2 = b.shape[axis]



    df = n1+n2-2
    svar = ((n1-1.0)*v1+(n2-1.0)*v2) / df
    zerodivproblem = svar == 0
    t = (x1-x2)/np.sqrt(svar*(1.0/n1 + 1.0/n2))  # N-D COMPUTATION HERE!!!!!!

    t = np.where(zerodivproblem, 1.0, t)           # replace NaN t-values with 1.0
    probs = stats.betai(0.5*df, 0.5, df /(df+t*t))

    if not np.isscalar(t):
        probs = probs.reshape(t.shape)
    if not np.isscalar(probs) and len(probs) == 1:
        probs = probs[0]
    return t, probs

