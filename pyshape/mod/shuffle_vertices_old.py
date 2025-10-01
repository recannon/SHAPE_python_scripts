
import argparse
import glob
import logging
from pathlib import Path
import numpy as np
from . import mod_io
from ..io_utils import logger, error_exit

#python -m convert_type modfiles -vmod 500 n 
#python -m convert_type test.mod -hmod 5 30 
#For what the arguments after -hmod and -vmod mean, run mkvertmod or mkharmod in terminal with no arguments 

def shuffle_vertices(fname):

    logger.debug('Shuffling vertices')
    logger.debug(f'{fname}')
    mod_info = mod_io.read(fname)
    vertex_comp = mod_info.components[0]  #mkvertmod always produces 1 component

    #Random permutation
    perm = np.random.permutation(len(vertex_comp.base_disp))
    #Update
    vertex_comp.base_disp = vertex_comp.base_disp[perm]
    vertex_comp.dev_dirs = vertex_comp.dev_dirs[perm]
    vertex_comp.deviations = vertex_comp.deviations[perm]
    index_map = np.zeros_like(perm)
    index_map[perm] = np.arange(len(perm))
    vertex_comp.facets = index_map[vertex_comp.facets]
    mod_info.components = [vertex_comp]

    mod_io.write(mod_info, fname)

    return True


#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Shuffle vertices of one or multiple files at once")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Beta and lambda ranges and steps
    parser.add_argument("fname", type=str, 
                        help="Name of file to affect. If directory, will affect all .mod files in directory. Runs IN PLACE")
    
    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    if Path(args.fname).is_file():
        logger.info(f'Running script on file {args.fname}')
        shuffle_vertices(args.fname)
    elif Path(args.fname).is_dir():
        logger.info(f'Running script on directory {args.fname}/*.mod')
        modfiles = glob.glob(f'{args.fname}/*.mod')
        for mod in modfiles:
            shuffle_vertices(mod)
    else:
        raise error_exit('Cannot find file or directory with name [fname]')

    return True

if __name__ == "__main__":
    main()

