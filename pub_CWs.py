#Last modified by @recannon 09/01/2026

#This is very scuffed. Only works for one CW per set. Will break otherwise
#Requires a full revamp of obs_io really.

import pyshape.plotting.pub_routines as pp
from pyshape.io_utils import logger, error_exit
from pyshape.obs import obs_io
from pathlib import Path
import logging
from astropy.time import Time
from pyshape.utils import time_shape2astropy

temp_dir = Path.cwd() / 'waction' / 'temp'
obsfile = Path.cwd() / 'obsfiles' / 'FF.obs'
cw_test_dir = Path.cwd() / 'waction' / 'cw_test'

#Read obsfile to check for which data types are present
obs_sets  = obs_io.read(obsfile)
set_types = set(obs_set.type for obs_set in obs_sets) 
    
if 'doppler' not in set_types:
    error_exit('Cannot find doppler frames')

cw_sets = [o for o in obs_sets if o.type=='doppler']
cw_fits = sorted(temp_dir.glob("fit_??_??.dat"))

#Create plot
for i,cw in enumerate(cw_fits):
    
    entry_line = cw_sets[i].lines[-3]
    date = " ".join(entry_line.split()[1:7])
    cw_start = time_shape2astropy(date)
    
    start_jd   = cw_start.jd
    start_date = cw_start.isot.split('T')[0]
    
    fig_title = f'{i+1} $\\bullet$ {start_date} $\\bullet {start_jd:.3f}$ '
    
    pp.pub_doppler(cw,fig_title,save=cw_test_dir/f'{i+1}.png')
    
