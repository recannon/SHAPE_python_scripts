#Last modified 14/09/2025

import argparse
import logging
import cartopy.crs as ccrs
import cmasher as cmr
import healpy as hp
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.tri as tri
import numpy as np
from scipy.interpolate import griddata
from ..io_utils import logger, error_exit
from .. import io_utils
from . import scan_io

def pub_gridscan(bet:np.array, lam:np.array, chi:np.array, 
                cmp_array:list, cmp:str='magma', save:bool=False):

    lon_plot,lat_plot,chi_plot = _p_interpolate_chi_sphere(bet,lam,chi)
    coords_plot = tri.Triangulation(lon_plot, lat_plot)

    proj = ['N','S']
    ortho_N = ccrs.Orthographic(central_longitude=180,central_latitude=+90)
    ortho_S = ccrs.Orthographic(central_longitude=0,central_latitude=-90)
    moll    = ccrs.Mollweide(central_longitude=180)
    sine    = ccrs.Sinusoidal()
    pltcrr  = ccrs.PlateCarree()

    # col_contours = np.linspace(np.min(coords_chi), perc_levels[0], 11)
    col_contours = cmp_array

    fig = plt.figure(figsize=[3.37689*2,3.7689*9/8*2])
    ax1 = plt.subplot2grid(shape=(2, 2), loc=(0, 0), colspan=1, projection=ortho_N)
    ax2 = plt.subplot2grid(shape=(2, 2), loc=(0, 1), colspan=1, projection=ortho_S)
    ax3 = plt.subplot2grid(shape=(2, 2), loc=(1, 0), colspan=2, projection=sine)   

    for i,ax in enumerate([ax1,ax2,ax3]):
        ax.set_global()
        
        cont = ax.tricontourf(coords_plot, chi_plot, cmap=cmp, levels=col_contours,transform=pltcrr)
        # ax.tricontour(coords_plot, chi_plot, levels=perc_levels,
                #    colors=['r','g','b'], linestyles=['-','--',':'],transform=pltcrr)

        gl = ax.gridlines(draw_labels=True, linestyle='-')
        
        gl.xlocator = mticker.FixedLocator([-120,-60,0,60,120,179.999])
        gl.ylocator = mticker.FixedLocator([-90,-60,-30,0,30,60,90])

        gl.xformatter = mticker.FuncFormatter(lambda x, pos: f"{x % 360:.0f}°")
        gl.yformatter = mticker.FuncFormatter(lambda x, pos: f"{x:.0f}°")

        #N/S labels
        if i!=2:
            ax.text(0.1, 0.9, proj[i], transform=ax.transAxes, fontsize=20, fontweight='bold', ha='center', va='center')
    
    #Colour bar
    cbar = fig.colorbar(cont, ax=ax3, orientation='horizontal', pad=0.1)
    cbar.set_label("Objective function")
    
    plt.tight_layout()
    
    if save:
        logger.debug(f'Saved pubplot to {save}')
        plt.savefig(save)
    plt.show()
        
    return 1


def _p_interpolate_chi_sphere(bet,lam,chi, nside=32):
    
    #Duplicate values across from 0 to 360 degrees, for interpolation to be more complete
    lam_new = np.ones(len(lam[lam==0]))*360
    bet_new = bet[lam==0]
    chi_new = chi[lam==0]
    
    bet = np.concatenate([bet,bet_new])
    lam = np.concatenate([lam,lam_new])
    chi = np.concatenate([chi,chi_new])
    
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


#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Plot grid scan result for publication",
                                     epilog="This script will edit the colour levels to be in round number intervals")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Plot args
    plot_group = parser.add_argument_group('Arguments for creating a grid scan plot')
    plot_group.add_argument('--dirname', type=str,
                            help='Directory of logfiles of the grid scan. Defaults to CWD')
    plot_group.add_argument('--fig-name', type=str,
                            help="Specify name of output jpg file. Defaults to grid_scan_pub.jpg")
    plot_group.add_argument('--max-level', type=str,
                            help='Multiple of minimum chisqr that appears coloured on plot. Default 1.1')

    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')
    
    #Check directory exists and has files in
    if not args.dirname:
        args.dirname = '.'
    args.dirname = io_utils.check_dir(args.dirname)
    no_files = len([f for f in args.dirname.iterdir() if f.is_file()])
    if no_files == 0:
        error_exit(f'Directory {args.dirname} has no files in')

    if not args.fig_name:
        args.fig_name = './grid_scan_pub.jpg'

    #Maxlevel
    if not args.max_level:
        args.max_level = 1.1
    args.max_level = io_utils.check_type(args.max_level,'--max-level',float) 

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)


    logger.debug(f'Scanning files in {args.dirname}')
    bet,lam,chi = scan_io.polescan_results(args.dirname)

    bet,lam = bet[~np.isnan(chi)],lam[~np.isnan(chi)]
    chi = chi[~np.isnan(chi)]
    
    cmp_array = np.linspace(np.min(chi),np.min(chi)*args.max_level,10)
    
    #Plot
    pub_gridscan(bet,lam,chi,
             cmp_array=cmp_array,
             cmp='cmr.sunburst',save=args.fig_name)

if __name__ == "__main__":
    main()


