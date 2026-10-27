#Last modified by @recannon 27/08/2026

#27/08/2026 - More documentation

#Used to shuffle the vertices of a vertex modfile/directory. Can also be used to reorder vertices (for plotting)
#Cannot choose specific components just yet
#python -m pyshape.mod.shuffle_vertices test.mod  #Shuffles vertices in test.mod
#python -m pyshape.mod.shuffle_vertices modfiles -r  #Reorders all verties in .mod files in modfiles.

import argparse
import glob
import logging
from pathlib import Path
import numpy as np
from . import mod_io
from ..cli.config import logger, error_exit

def shuffle_vertices(fname, reorder=False, rng=None):
    
    logger.debug('Shuffling vertices')
    logger.debug(f'{fname}')
    mod_info = mod_io.modFile.from_file(fname)
    
    for comp in mod_info.components:
        if comp.type == "vertex":
            if reorder == True:
                comp.reorder_vertices()
            else:
                comp.shuffle_vertices(rng=rng)
    
    mod_info.write(fname)
    return True


#===Functions for parsing args below this point===
def parse_args():
    '''Parse command-line arguments.'''
    parser = argparse.ArgumentParser(description='Shuffle vertices of one or multiple files at once')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')
    parser.add_argument('fname', type=str, 
                        help='Name of file to affect. If directory, will affect all .mod files in directory. Runs IN PLACE')
    parser.add_argument('-r','--reorder', action='store_true',
                        help='Re-orders according to SHAPE structure (north to south pole)')

    
    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    if args.reorder:
        logger.info('Re-ordering from north to south')

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    if Path(args.fname).is_file():
        logger.info(f'Running script on file {args.fname}')
        shuffle_vertices(args.fname, args.reorder)
    elif Path(args.fname).is_dir():
        logger.info(f'Running script on directory {args.fname}/*.mod')
        modfiles = glob.glob(f'{args.fname}/*.mod')
        for mod in modfiles:
            #Set to shuffle the same for all things in file?
            shuffle_vertices(mod, args.reorder)#, rng=np.random.default_rng(25))
    else:
        raise error_exit('Cannot find file or directory with name [fname]')

    return True

if __name__ == '__main__':
    main()

