#last modified 14/09/2025

import argparse
import logging
import cmasher as cmr
import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np
from scipy.interpolate import griddata
from . import scan_io
from ..io_utils import logger, error_exit, check_dir, check_type

def quick_gridscan(bet:np.array, lam:np.array, chi:np.array,
                maxlevel:float=1.5, res:float=1, lines:list=[],
                cmp:str='cmr.sunburst', save:str=None, show:bool=True):
    
    pole_mask = np.logical_or(bet==90, bet==-90)

    lon_plot, lat_plot, chi_plot = _q_interpolate_chi_sphere(bet, lam, chi, res=res)
    
    minchi = chi_plot.min()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    col_contours = np.arange(minchi, minchi * maxlevel,
                            (minchi * maxlevel - minchi) / 15)
    ax.plot(lam,bet,'g.',alpha=1,markersize=1)
    cf = ax.contourf(lon_plot, lat_plot, chi_plot, cmap=cmp, levels=col_contours)
    if lines:
        lin_contours = np.min(chi) * (1 + (np.array(lines) / 100))
        cl = ax.contour(lon_plot,lat_plot, chi_plot, levels=lin_contours,
                    colors='deepskyblue', linestyles=['-','--',':'])

    # add colorbar linked to the contour plot
    cbar = fig.colorbar(cf, ax=ax)
    cbar.set_label("Objective Function", fontsize=14)
        
    ax.set_xticks(np.arange(0, 361, 60))
    ax.set_yticks(np.arange(-90, 91, 30))
    ax.set_xlabel("Longitude", fontsize=20)
    ax.set_ylabel("Latitude", fontsize=20)
    ax.set_xlim(np.min(lam[~pole_mask]), np.max(lam[~pole_mask]))
    ax.set_ylim(np.min(bet), np.max(bet))
    ax.set_title(f'({bet[np.nanargmin(chi)]}, {lam[np.nanargmin(chi)]}) : {minchi}', fontsize=30)

    if save:
        fig.savefig(save)
    if show:
        fig.show()

    return 1
    

#Quick interpolate does not use spherical interpolation
def _q_interpolate_chi_sphere(bet,lam,chi, res=1):
    
    mask = ~np.isnan(chi)
    bet, lam, chi = np.asarray(bet)[mask], np.asarray(lam)[mask], np.asarray(chi)[mask]

    lon_vals = np.arange(0, 360 + res, res)
    lat_vals = np.arange(-90, 90 + res, res)
    lon_grid, lat_grid = np.meshgrid(lon_vals, lat_vals)

    chi_grid = griddata(
        points=np.column_stack((lam, bet)), 
        values=chi,
        xi=(lon_grid, lat_grid),
        method="linear"
    )

    return lon_grid, lat_grid, chi_grid
    
#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Plot grid scan result")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Plot args
    plot_group = parser.add_argument_group('Arguments for creating a grid scan plot')
    plot_group.add_argument('--dirname', type=str,
                            help='Directory of logfiles of the grid scan. Defaults to CWD')
    plot_group.add_argument('--fig-name', type=str,
                            help="Specify name of output jpg file. Defaults to grid_scan.jpg")
    plot_group.add_argument('--max-level', type=str,
                            help='Multiple of minimum chisqr that appears coloured on plot. Default 1.1')
    plot_group.add_argument('--lines', nargs='*', type=float, default=None,
                            help='Additional contours to plot as percentages above minimum chi-sqr. e.g., --lines 1 2.5 5')
    
    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')
    
    #Check directory exists and has files in
    if not args.dirname:
        args.dirname = '.'
    args.dirname = check_dir(args.dirname)
    no_files = len([f for f in args.dirname.iterdir() if f.is_file()])
    if no_files == 0:
        error_exit(f'Directory {args.dirname} has no files in')

    if not args.fig_name:
        args.fig_name = './grid_scan.jpg'

    #Maxlevel
    if not args.max_level:
        args.max_level = 1.1
    args.max_level = check_type(args.max_level,'--max-level',float) 
    #Lines
    if args.lines == []:
        args.lines = [1.0, 2.5, 5.0]

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)


    logger.debug(f'Scanning files in {args.dirname}')
    bet,lam,chi,_,_ = scan_io.polescan_results(args.dirname)

    bet,lam = bet[~np.isnan(chi)],lam[~np.isnan(chi)]
    chi = chi[~np.isnan(chi)]
    
    #Duplicate values across from 0 to 360 degrees, for interpolation to be more complete
    lam_new = np.ones(len(lam[lam==0]))*360
    bet_new = bet[lam==0]
    chi_new = chi[lam==0]
    
    bet = np.concatenate([bet,bet_new])
    lam = np.concatenate([lam,lam_new])
    chi = np.concatenate([chi,chi_new])
    
    #Plot
    quick_gridscan(bet,lam,chi,
                maxlevel=args.max_level, lines=args.lines, res=1,
                cmp='cmr.sunburst',show=False,save=args.fig_name)
    # plot_quick(args.dirname,args.fig_name,args.max_level,args.lines)

if __name__ == "__main__":
    main()


