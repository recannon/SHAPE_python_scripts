#Last modified 03/05/2025

from . import log_file
import numpy as np
import glob
import shutil
from scipy.interpolate import griddata
from .outfmt import logger,error_exit
import healpy as hp


def results(scan_dir):

    # #First check jobs finished
    # faction_path = f'{scan_dir}/faction/job_output*'
    # faction_files = sorted(glob.glob(faction_path))
    # # print(f'Found {len(faction_path)} faction files')
    # for fac in faction_files:
    #     f = open(fac,'r')
    #     lines = [l.strip().split() for l in f.readlines()]
    #     f.close()
    #     if lines[-1][0] != 'Done':
    #         logger.warning(f'Warning: {fac} not completed. {lines[-2][3]}')


    log_file_path = f'{scan_dir}/logfiles/lat*.log'
    log_files = sorted(glob.glob(log_file_path))
    if len(log_files) == 0:
        logger.warning(f'Could not find any polescan log files ({log_file_path})')
        return [],[],[]
    else:
        logger.debug(f'Found {len(log_files)} log files')


    chi,bet,lam,unreduced,dof = [],[],[],[],[]
    for f in log_files:
        try:
            log_info = log_file.read(f)
            chi.append(log_info['ALLDATA'])
            unreduced.append(log_info['unreduced'])
            dof.append(log_info['dof'])
            bet.append(int(f[-13:-10]))
            lam.append(int(f[-7:-4]))
        except:
            # chi.append(np.nan)
            logger.warning(f'Found NaN chisqr in {f}')

    chi,bet,lam = np.array(chi),np.array(bet),np.array(lam)
    unreduced,dof = np.array(unreduced),np.array(dof)
    
    #Duplicate values across from 0 to 360 degrees, for interpolation to be more complete
    lam_new = np.ones(len(lam[lam==0]))*360
    bet_new = bet[lam==0]
    chi_new = chi[lam==0]
    unreduced_new = unreduced[lam==0]
    dof_new = dof[lam==0]
    
    bet = np.concatenate([bet,bet_new])
    lam = np.concatenate([lam,lam_new])
    chi = np.concatenate([chi,chi_new])
    unreduced = np.concatenate([unreduced,unreduced_new])
    dof = np.concatenate([dof,dof_new])

    return bet,lam,chi,unreduced,dof

def combine(scan_dirs, combine_dir=None):

    chi_all = np.empty((0,), dtype=float)
    bet_all = np.empty((0,), dtype=float)
    lam_all = np.empty((0,), dtype=float)
    loc_all = np.empty((0,), dtype=int)

    for i,scan_dir in enumerate(scan_dirs):
            
        bet,lam,chi,_,_ = results(scan_dir)

        chi_all = np.concatenate([chi_all, chi])
        bet_all = np.concatenate([bet_all, bet])
        lam_all = np.concatenate([lam_all, lam])
        loc_all = np.concatenate([loc_all, np.full_like(chi,i, dtype=int)])

    #Then combine and sort
    combined         = np.rec.fromarrays([bet_all, lam_all, chi_all, loc_all], names=('bet', 'lam', 'chi', 'loc'))
    sorted_indices   = np.lexsort((combined.chi, combined.lam, combined.bet))
    sorted_combined  = combined[sorted_indices] #sorted array of coords, then by chisqr
    coord_array      = np.stack((sorted_combined.bet, sorted_combined.lam), axis=1)
    _,unique_indices = np.unique(coord_array, axis=0, return_index=True) #Index of each pairs first appearance
    combined_best    = sorted_combined[unique_indices]

    if combine_dir:
        
        f = open(f'{combine_dir}/namecores.txt', 'w')

        for coord in combined_best:
            
            if coord.lam == 360:
                continue

            namecore = f'lat{coord.bet:+03.0f}lon{coord.lam:03.0f}'
            orig_dir = scan_dirs[coord.loc]

            f.write(namecore + '\n')

            for f_type in ['mod','obs','log']:
                f_orig = f'{orig_dir}/{f_type}files/{namecore}.{f_type}'
                shutil.copy(f_orig, f'{combine_dir}/{f_type}files/')

        f.close()

    return combined_best.bet,combined_best.lam,combined_best.chi, combined_best.loc

def interpolate_chi(bet,lam,chi, nside=32):
    
    #Interpolate onto spherical healpy grid
    npix = hp.nside2npix(nside)

    theta, phi = hp.pix2ang(nside, np.arange(npix))
    lat = np.rad2deg(np.pi/2 - theta)   # latitude [-90, +90]
    lon = np.rad2deg(phi)               # longitude [0, 360)

    # interpolate onto HEALPix points
    chiall = griddata(
        np.column_stack([lam, bet]),        # input scattered coords
        chi,                                # values at those coords
        np.column_stack([lon, lat]),        # HEALPix coords
        method='linear'
    )

    coords_lon = lon.copy()
    coords_lat = lat.copy()
    coords_chi = chiall.copy()

    #Adds where initial scan was lon = 0
    lon_wrap = np.concatenate([coords_lon, lam[lam==0]])
    lat_wrap = np.concatenate([coords_lat, bet[lam==0]])
    chi_wrap = np.concatenate([coords_chi, chi[lam==0]])
    #Duplicate to 360
    lon_wrap2 = np.concatenate([lon_wrap, lon_wrap[lon_wrap==0]+360])
    lat_wrap2 = np.concatenate([lat_wrap, lat_wrap[lon_wrap==0]])
    chi_wrap2 = np.concatenate([chi_wrap, chi_wrap[lon_wrap==0]])

    #Pole values
    minval = np.min(coords_chi)
    lon_poles = np.concatenate([lam[bet==-90],lam[bet==90]])
    lat_poles = np.concatenate([bet[bet==-90],bet[bet==90]])
    chi_poles = np.concatenate([chi[bet==-90],chi[bet==90]])
    # chi_poles = np.concatenate([chi[bet==-90],np.array([10,10])])

    #plot arrays
    lon_plot = np.concatenate([lon_wrap2, lon_poles])
    lat_plot = np.concatenate([lat_wrap2, lat_poles])
    chi_plot = np.concatenate([chi_wrap2, chi_poles])

    #remove nans
    lon_plot = lon_plot[~np.isnan(chi_plot)]
    lat_plot = lat_plot[~np.isnan(chi_plot)]
    chi_plot = chi_plot[~np.isnan(chi_plot)]

    return lon_plot,lat_plot,chi_plot