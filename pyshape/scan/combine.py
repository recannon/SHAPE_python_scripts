#Last modified 05/04/2026 by @recannon

import argparse
import logging
import numpy as np
from pathlib import Path
import shutil
from rich.progress import Progress
from ..cli_config import logger,error_exit,console
from ..utils import check_dir
from . import scan_io

def combine_gridscan(fit_dirs, out_dir):
    logger.debug(f'Combining gridscans from {fit_dirs}')

    #Create output directories if doesn't exist
    for f_type in ['mod', 'obs', 'log']:
        Path(f'{out_dir}/{f_type}files').mkdir(exist_ok=True)

    #Read all fits
    p1_parts, p2_parts, chi_parts, loc_parts = [], [], [], []
    with Progress(console=console, transient=True) as pb:
        t1 = pb.add_task('Reading scan directories', total=len(fit_dirs))
        for i, scan_dir in enumerate(fit_dirs):
            p1, p2, chi, _ = scan_io.scan_results(scan_dir)
            p1_parts.append(p1)
            p2_parts.append(p2)
            chi_parts.append(chi)
            loc_parts.append(np.full_like(chi, i, dtype=int))
            pb.update(task_id=t1, advance=1)
    p1_all  = np.concatenate(p1_parts)
    p2_all  = np.concatenate(p2_parts)
    chi_all = np.concatenate(chi_parts)
    loc_all = np.concatenate(loc_parts)


    #Combine and sort for each (p1, p2) and keep best chi
    combined          = np.rec.fromarrays([p1_all, p2_all, chi_all, loc_all], names=('p1', 'p2', 'chi', 'loc'))
    sorted_indices    = np.lexsort((combined.chi, combined.p2, combined.p1))
    sorted_combined   = combined[sorted_indices]
    coord_array       = np.stack((sorted_combined.p1, sorted_combined.p2), axis=1)
    _, unique_indices = np.unique(coord_array, axis=0, return_index=True)
    combined_best     = sorted_combined[unique_indices]

    #Write namecores.txt and copy files to new dir
    with Progress(console=console, transient=True) as pb:
        t2 = pb.add_task('Copying files', total=len(combined_best))

        with open(f'{out_dir}/namecores.txt', 'w') as namecore_file:
            for coord in combined_best:
                p1_val   = coord.p1
                p2_val   = coord.p2
                orig_dir = fit_dirs[coord.loc]

                #Read namecore from original namecores.txt (non polescans have more complex names, easier to copy)
                #Skips this file if namecores not found in its supposed parent dir
                orig_namecores = Path(orig_dir) / 'namecores.txt'
                if not orig_namecores.exists():
                    logger.warning(f'namecores.txt not found in {orig_dir}')
                    pb.update(task_id=t2, advance=1)
                    continue

                #Find matching namecore line and parses file name
                namecore = None
                with open(orig_namecores) as f:
                    for line in f:
                        parts = line.strip().split()
                        if float(parts[1]) == p1_val and float(parts[2]) == p2_val:
                            namecore = parts[0]
                            break

                #Skips this file if couldn't find a match
                if namecore is None:
                    logger.warning(f'Could not find namecore for p1={p1_val}, p2={p2_val} in {orig_dir}')
                    pb.update(task_id=t2, advance=1)
                    continue

                #Finally copy file and write new namecore line
                for f_type in ['mod', 'obs', 'log']:
                    f_orig = Path(f'{orig_dir}/{f_type}files/{namecore}.{f_type}')
                    if not f_orig.exists():
                        logger.warning(f'File not found: {f_orig}')
                        continue
                    shutil.copy(f_orig, f'{out_dir}/{f_type}files/')
                namecore_file.write(f'{namecore} {p1_val} {p2_val}\n')

                pb.update(task_id=t2, advance=1)

    return combined_best.p1, combined_best.p2, combined_best.chi, combined_best.loc
    
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
    combine_group.add_argument('--outdir',type=str,default=None,
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
        if not args.outdir:
            args.outdir = Path.cwd()
        else:
            args.outdir = check_dir(args.outdir)
    
    elif args.dirs:
        args.dirs = [check_dir(dir) for dir in args.dirs]
        if not args.outdir:
            error_exit('Must provide --outdir if not using --subscan')    
        args.outdir = check_dir(args.outdir)
        
    else:
        error_exit('Must provide either --subscan or a list of --dirs')     


    return args


#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    p1, p2, chi, loc = combine_gridscan(args.dirs, args.outdir)
    logger.info(f'Combined {len(chi)} unique grid solutions into {args.outdir}')

    return 


if __name__ == "__main__":
    main()

