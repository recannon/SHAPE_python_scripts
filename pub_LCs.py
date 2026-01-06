#Last modified by @recannon 20/12/2025

from pyshape import plotting
from pyshape.mod.mod_io import modFile
from pyshape.io_utils import logger

import logging

logger.setLevel(logging.INFO)

target = '2000rs11'
no = 1
lc_filename = f'/cephfs/rcannon/{target}/lightcurves/{target}.lc.txt'
mod_filename = f'/home/rcannon/Code/Radar/SHAPE/{target}/PS2/FF/modfiles/FF.mod'

out_path = f'../figures/{target}/M{no}' #For figures

mod_info = modFile.from_file(mod_filename)

mod_vx = mod_info.components[0]
V,F,FN,FNa = mod_vx.vertices, mod_vx.facets, mod_vx.FN, mod_vx.FNa

mod_ss = mod_info.spinstate
t0,P = mod_ss.t0.jd, mod_ss.P
lam,bet,phi = mod_ss.lam, mod_ss.bet, mod_ss.phi+90

mod_ol = mod_info.phot_functions[1][0] #Assume only one scattering law for optical

scattering_law = mod_ol.type
scattering_params = mod_ol.values_to_dict()

# Hapke values not required, but can be given in a list
results = plotting.pub_lightcurve_generator(out_path,lc_filename,t0,lam,bet,phi,P,FN,FNa,V=V,F=F,shadowing=True,plot=True,show_plot=False)
