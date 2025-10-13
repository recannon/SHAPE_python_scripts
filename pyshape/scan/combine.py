#Last modified 12/09/2025

import argparse
import logging
from pathlib import Path
import shutil
import numpy as np
from ..io_utils import logger,error_exit,check_dir
from . import scan_io


def combine_polescan(fit_dirs,out_dir):
    
    logger.debug(f'Combining polescans from {fit_dirs}')

    chi_all = np.empty((0,), dtype=float)
    bet_all = np.empty((0,), dtype=float)
    lam_all = np.empty((0,), dtype=float)
    loc_all = np.empty((0,), dtype=int)

    for i,scan_dir in enumerate(fit_dirs):
            
        bet,lam,chi = scan_io.polescan_results(scan_dir)

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

    #Write namecores
    f = open(f'{out_dir}/namecores.txt', 'w')
    for coord in combined_best:

        namecore = f'lat{coord.bet:+03.0f}lon{coord.lam:03.0f}'
        orig_dir = fit_dirs[coord.loc]

        f.write(namecore + '\n')

        for f_type in ['mod','obs','log']:
            f_orig = f'{orig_dir}/{f_type}files/{namecore}.{f_type}'
            shutil.copy(f_orig, f'{out_dir}/{f_type}files/')

    f.close()

    return combined_best.bet,combined_best.lam,combined_best.chi, combined_best.loc
    
    
#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Combine grid scans or multiple fit directories")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")
    
    #Combine args
    combine_group = parser.add_argument_group('Arguments for combining fit directories.')
    combine_group.add_argument('--subscan',action='store_true',
                               help='If toggled will combine all polescans in ./subscans into ./')
    combine_group.add_argument('--dirs',nargs='+',default=None,
                               help='List of paths to polescans to be combined. Cannot use with --subscans')
    combine_group.add_argument('--out-dir',type=str,default=None,
                               help='Out directory to save combined results. Not required, but optional, if using --subscans')
    
    return parser.parse_args()


def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    if args.subscan:
        if args.dirs:
            error_exit('Cannot combine subscans with other polescans. Do this separately')            
        args.dirs    = sorted(list(Path.cwd().joinpath("subscans").glob("*")))
        if not args.out_dir:
            args.out_dir = Path.cwd()
        else:
            args.out_dir = check_dir(args.out_dir)
    
    elif args.dirs:
        args.dirs = [check_dir(dir) for dir in args.dirs]
        if not args.out_dir:
            error_exit('Must provide --out-dir if not using --subscan')    
        args.out_dir = check_dir(args.out_dir)
        
    else:
        error_exit('Must provide either --subscan or a list of --dirs')     


    return args


#===Main===
def main():

    args = parse_args()
    args = validate_args(args)


    combine_polescan(args.dirs,args.out_dir)


if __name__ == "__main__":
    main()

