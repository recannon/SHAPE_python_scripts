#Last modified by @recannon 20261124

import argparse
import logging
from .config import logger
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SBATCH_FILE = SCRIPT_DIR.parent / 'templates' / 'slurm' / 'launch_fitting.sbatch'

def slurm_pshape(args):
        
    sbatch_command = [
        'sbatch',
        f'--array={"-".join(args.array)}',
        f'--job-name={args.name}',
        f'--time={args.time}:00:00',
        f'--nodes={args.nodes}',
        f'--ntasks-per-node={args.n_cores}',
        f'--mem={args.mem}G',
        f'{str(SBATCH_FILE)}'
    ]
    
    logger.info(f'Running:\n{" ".join(sbatch_command)}')
    
    subprocess.run(sbatch_command, check=True, text=True)
    
    return

def parse_args():
    '''Parse command-line arguments.'''
    parser = argparse.ArgumentParser(description='Runs a slurm array job with given input parameters',
                                     epilog='Saves error and job output files to ./faction')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')
    
    input_group = parser.add_argument_group('Input parameters for the job')  
    input_group.add_argument('name', type=str,
                             help='SBATCH --job-name : Required')
    input_group.add_argument('array', nargs=2,
                             help='Two inputs, array start and end (e.g. 1 46)')
    input_group.add_argument('--time', type=float, default=2,
                             help='SBATCH --time : Default: 2')
    input_group.add_argument('--mem', type=float, default=2,
                             help='SBATCH --mem : Default: 2')
    input_group.add_argument('--nodes', type=int, default=1,
                             help='SBATCH --nodes : Default 1')
    input_group.add_argument('--n-cores', type=int, default=12,
                             help='SBATCH --ntasks-per-node : Default: 12')

    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    return args

def main():
    args = parse_args()
    args = validate_args(args)    
    
    slurm_pshape(args)

if __name__ == "__main__":
    main()
