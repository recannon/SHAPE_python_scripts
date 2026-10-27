#Last modified by @recannon 27/08/2026

#15/06/2026 - Added functionality to change theta. This can help produce low res vertex models, where it doesn't work with higher thetas.
#23/06/2026 - Added capability to do components separately
#27/08/2026 - More Documentation

#Applies mkvertmod and mkharmod to a file, or directory of files.
#It can apply this to create a single component model, or apply the command to individual components in a modfile.
#For what the arguments after -hmod and -vmod mean, run mkvertmod or mkharmod in terminal with no arguments (These are native SHAPE commands)
#python -m convert_type test.mod -hmod 5 30   #Creates harmod file for test.mod
#python -m convert_type modfiles -vmod 500 n -s #Creates vertex file for all files in directory modfiles, and shuffles vertex order
#python -m convert_Type test.mod -vmod 1000 n -c -1  #Creates a multicomponent vertex file
#python -m convert_Type test.mod -vmod 1000 n -c 2   #Turns only the 3rd component in a file to a vertex component, leaving others untouched.

import argparse
import glob
import logging
from pathlib import Path
import subprocess
import numpy as np
from . import shuffle_vertices
from ..cli.cli_config import logger, error_exit
from .mod_io import modFile
import tempfile

def convert_type(fname,command_info,shuffle,theta,components):

    command, *command_args = command_info
    logger.debug(f'Applying {command} to {fname}')

    #Case for components listed
    save_c = []
    if components:
        
        mod_file = modFile.from_file(fname)
        comp_list = mod_file.components
        
        #Component check
        if np.max(components) >= len(comp_list):
            error_exit(f'{fname} does not have {np.max(components)} components')
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp = Path(tmp_dir) / 'temp_modfile.mod'
            
            if components == [-1]:
                components = np.arange(0,len(comp_list))
            
            #Loop components
            for idx in components:
                c = comp_list[idx]
                if theta:
                    c.theta = theta
            
                #Save CoM for reinsertion after command applied
                c_com = np.array([
                    c.linoff0, c.linoff1, c.linoff2
                ])
                
                for i in range(3):
                    setattr(c, f'linoff{i}', 0)
                
                mod_file.components = [c]
                mod_file.write(temp)
                
                #Running command
                subprocess.run([command, str(temp), str(temp), *map(str, command_args)], check=True)
                
                #Shuffle vertices if required
                if command == 'mkvertmod' and shuffle:
                    shuffle_vertices.shuffle_vertices(temp)

                mod_file_new = modFile.from_file(temp)
                c_new = mod_file_new.components[0]
                for i in range(0,3):
                    setattr(c_new, f'linoff{i}', c_com[i])
                save_c.append(mod_file_new.components[0])
        
        mod_file.components = save_c
        mod_file.write(fname)       
        
        return True
        
    #Case for no components listed (just apply command normally)
    else:
    
        #Changing theta
        if theta:
            mod_file = modFile.from_file(fname)
            for c in mod_file.components:
                c.theta = theta
            mod_file.write(fname)

        #Running command
        subprocess.run([command, fname, fname, *map(str, command_args)], check=True)

        #Shuffle vertices if required
        if command == 'mkvertmod' and shuffle:
            shuffle_vertices.shuffle_vertices(fname)

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
    parser.add_argument('--theta',type=int,default=None,
                        help='Changes theta value for all components prior to applying shape command')
    parser.add_argument('-c','--components', nargs='+', type=int, default=None,
                        help="Optional list of components to affect (-1 affects all individually)")

    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    if args.theta:
        logger.warning(f'Changing all components to have theta = {args.theta}')

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
        convert_type(args.fname,args.command,args.shuffle_vertices,args.theta,args.components)
    elif Path(args.fname).is_dir():
        logger.info(f'Running script on directory {args.fname}/*.mod')
        modfiles = glob.glob(f'{args.fname}/*.mod')
        for mod in modfiles:
            convert_type(mod,args.command,args.shuffle_vertices,args.theta,args.components)
    else:
        raise error_exit('Cannot find file or directory with name [fname]')

    return True

if __name__ == "__main__":
    main()

