#last modified by @recannon 06/03/2026

import argparse
import logging
import numpy as np
from scipy.interpolate import griddata
from . import scan_io
from ..plotting import quick_routines as pq
from ..cli_config import logger, error_exit
from ..utils import check_dir, check_type

def config_quick_scan(p1: np.array, p2: np.array, chi: np.array,
                      p1_label: str = 'p1', p2_label: str = 'p2',
                      polescan: bool = False,
                      maxlevel: float = 1.5, lines: list = [],
                      cmp: str = 'cmr.sunburst', save: str = None, show: bool = True):

    p1, p2 = p1[~np.isnan(chi)], p2[~np.isnan(chi)]
    chi = chi[~np.isnan(chi)]

    if polescan:
        logger.debug('Plotting polescan')
        # Duplicate lam=0 values at 360 for interpolation continuity
        p1_new = np.ones(len(p1[p1==0])) * 360
        p2_new = p2[p1==0]
        chi_new = chi[p1==0]
        p1 = np.concatenate([p1, p1_new])
        p2 = np.concatenate([p2, p2_new])
        chi = np.concatenate([chi, chi_new])
        p1_label, p2_label = 'Latitude', 'Longitude'
        p1_ticks = np.arange(0, 361, 60)
        p2_ticks = np.arange(-90, 91, 30)
        res=1
    else:
        logger.debug('Plotting gridscan')
        p1_ticks = None
        p2_ticks = None
        p1_res = np.min(np.diff(np.unique(p1))) /2
        p2_res = np.min(np.diff(np.unique(p2))) /2
        res = np.min([p1_res,p2_res])

    p1_grid, p2_grid, chi_grid = _q_interpolate_chi_grid(p1, p2, chi, res=res)
    minchi = np.nanmin(chi)
    logger.debug(f'Minchi = {minchi}')

    pq.quick_gridscan(p1, p2, chi,
                   p1_grid, p2_grid, chi_grid,
                   minchi, maxlevel, cmp, lines=lines,
                   p1_label=p1_label, p2_label=p2_label,
                   p1_ticks=p1_ticks, p2_ticks=p2_ticks,
                   save=save, show=show)


#Quick interpolate does not use spherical interpolation
def _q_interpolate_chi_grid(p1_arr,p2_arr,chi, res=1):
    
    mask = ~np.isnan(chi)
    p1_arr, p2_arr, chi = np.asarray(p1_arr)[mask], np.asarray(p2_arr)[mask], np.asarray(chi)[mask]

    p1_vals = np.arange(np.nanmin(p1_arr), np.nanmax(p1_arr) + res, res)
    p2_vals = np.arange(np.nanmin(p2_arr), np.nanmax(p2_arr) + res, res)
    p2_grid, p1_grid = np.meshgrid(p2_vals, p1_vals)

    chi_grid = griddata(
        points=np.column_stack((p1_arr, p2_arr)), 
        values=chi,
        xi=(p1_grid, p2_grid),
        method="linear",
        # fill_value=1e7,
        fill_value=np.nan,
    )

    return p1_grid, p2_grid, chi_grid
    
#===Functions for parsing args below this point===
def parse_args():
    parser = argparse.ArgumentParser(description='Plot grid scan result')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')

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

    p1, p2, chi, polescan_toggle = scan_io.scan_results(args.dirname)

    config_quick_scan(p1, p2, chi,
                      polescan=polescan_toggle,
                      maxlevel=args.max_level, lines=args.lines,
                      cmp='cmr.sunburst', show=False, save=args.fig_name)

if __name__ == "__main__":
    main()


