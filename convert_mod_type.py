import numpy as np
import argparse
from pyshape.outfmt import logger, error_exit
import logging
from pathlib import Path
import glob
import subprocess
from pyshape import mod_file

def convert_mod_type(fname,command_info,shuffle):

    command, *command_args = command_info
    logger.debug(f'Applying {command} to {fname}')

    #Running command
    subprocess.run([command, fname, fname, *map(str, command_args)], check=True)

    # Shuffle vertices if required
    if command == 'mkvertmod' and shuffle:
        logger.debug('Shuffling vertices')
        mod_info = mod_file.read(fname)
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

        mod_file.write(mod_info, fname)

    return True


#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Apply mkvertmod to mkharmod to multiple files at once",
                                     epilog='For more details of commands, run [command] in terminal')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Beta and lambda ranges and steps
    parser.add_argument("fname", type=str, 
                        help="Name of file to affect. If directory, will affect all .mod files in directory. Runs IN PLACE")
    
    command_group = parser.add_argument_group('Command to use')
    command_group.add_argument("-vmod", "--vertex-model", nargs=2,
        metavar=('N_VERTICES', 'BASIS'),
        help="Applies command mkvertmod: requires number of vertices and normal basis")
    command_group.add_argument("-hmod", "--harmonics-model", nargs=2,
        metavar=('N_HARMONICS', 'THETA'),
        help="Applies command mkharmod: requires number of harmonics and theta (resolution)")

    parser.add_argument('-s','--shuffle-vertices', action='store_true',
                        help='Only considered if mkvertmod is chosen. Will randomise vertex order')

    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    if args.vertex_model and args.harmonics_model:
        error_exit("I can't make a file a vertex and harmonics model at the same time!")

    elif args.vertex_model:
        try:
            args.vertex_model[0] = int(args.vertex_model[0])
        except:
            error_exit('Number of vertices must be an integer')
        if args.vertex_model[1] not in ['s','e','n']:
            error_exit('Normal basis must be one of: s n e')
        args.command = ['mkvertmod', args.vertex_model[0], args.vertex_model[1]]

    elif args.harmonics_model:
        try:
            args.harmonics_model[0] = int(args.harmonics_model[0])
            args.harmonics_model[1] = int(args.harmonics_model[1])
        except:
            error_exit('Both No. Harmonics and Theta must be integers')
        args.command = ['mkharmod', args.harmonics_model[0], args.harmonics_model[1]]
    
    else:
        error_exit("This message shouldn't appear, so its time to cry :(")

    logger.debug(args.command)

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    if Path(args.fname).is_file():
        logger.info(f'Running script on file {args.fname}')
        convert_mod_type(args.fname,args.command,args.shuffle_vertices)
    elif Path(args.fname).is_dir():
        logger.info(f'Running script on directory {args.fname}/*.mod')
        modfiles = glob.glob(f'{args.fname}/*.mod')
        for mod in modfiles:
            convert_mod_type(mod,args.command,args.shuffle_vertices)
    else:
        raise error_exit('Cannot find file or directory with name [fname]')

    return True

if __name__ == "__main__":
    main()

