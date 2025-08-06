#Last modified 11/07/2025

import argparse
import glob
import logging
from pathlib import Path
from pyshape import mod_file
from pyshape.outfmt import logger, error_exit

#python -m freeze_mod modfiles v 1
#python -m freeze_mod test.mod e 0 1

def freeze_mod(fname, mod_type, freeze, components=[]):
    '''
    Takes modfile {fname} and freezes or unfreezes all variable factors for specified components. 
    If scale factor was set to = then remains unchanged.

    Inputs:
        fname      : Filename to change, preferably from root path
        mod_type   : Type of file and what to freeze. 
                        - 'e' 'ellipse' for ellipsoid models (any number of components) 
                        - 'v' 'vertex' for vertex models (one component only)
                        - 's' 'spin' for spin state (Three pole angles, and period)
                        - 'p' for period and third pole angle only
        freeze     : 1 or -1 , 1 for freeze (f to c) and -1 for unfreeze (c to f)
        components : Optional list of entries for ellipsoid components numbers you want to affect. If none, affects all.
    '''
    
    # Can index to 1 or -1
    change = ['§','f ','c ']

    if type(mod_type) != str:
        raise TypeError('mod_type argument must be a string')
    if freeze != 1 and freeze != -1:
        raise ValueError('freeze instruction must be either 1 or -1')
    if type(components) != list:
        raise TypeError('components argument must be given as a list')

    logger.debug(f'{fname} : Replacing {change[freeze]}with {change[-freeze]}')

    # Open File
    f = open(fname,'r')
    file_lines = f.readlines()
    f.close()

    if mod_type == 'e' or mod_type == 'ellipse':

        #If no components given, create list of all.
        no_components = int(file_lines[3].strip().split()[0])

        if components == []:
            components = range(0,no_components)
        elif max(components) > (no_components-1):
            raise ValueError(f'File does not have {int(max(components))+1} components')
        
        #Loop through each elip.
        for elip in components:
            logger.debug(f'Component {elip}')
            start_ind = 4 + (elip*12)
            final_ind = 16 + (elip*12)
            file_lines[start_ind:final_ind] = [line.replace(change[freeze],change[-freeze]) for line in file_lines[start_ind:final_ind]]

    elif mod_type == 'v' or mod_type == 'vertex':

        #Check only one component
        no_components = int(file_lines[3].strip().split()[0])
        if no_components != 1:
            raise ValueError('Cannot change a vertex model with more than 1 component')

        no_vertex = int(file_lines[12].split()[0])
        logger.debug(f'{no_vertex} vertices')

        file_lines[13:17+(2*no_vertex)] = [line.replace(change[freeze],change[-freeze]) for line in file_lines[13:17+(2*no_vertex)]]


    elif mod_type == 'h' or mod_type == 'harmonic':

        #If no components given, create list of all.
        no_components = int(file_lines[3].strip().split()[0])

        if components == []:
            components = range(0,no_components)
        elif max(components) > (no_components-1):
            raise ValueError(f'File does not have {int(max(components))+1} components')
        
        #Loop through each elip.
        lines = [l.strip() for l in file_lines]
        for i in components:
            logger.debug(f'Component {i}')
            start_ind = int(lines.index(f'{{COMPONENT {i}}}'))
            no_harmonics = int(lines[start_ind+8].split()[0])
            final_ind = start_ind+11+int((no_harmonics+1)**2)+1
            file_lines[start_ind:start_ind+6] = [line.replace(change[freeze],change[-freeze]) for line in file_lines[start_ind:start_ind+6]]
            file_lines[start_ind+9:final_ind] = [line.replace(change[freeze],change[-freeze]) for line in file_lines[start_ind+9:final_ind]]



    elif mod_type == 's' or mod_type == 'spin':
        
        start_ind = file_lines.index('{SPIN STATE}\n')

        #Swap pole angles
        file_lines[start_ind+2:start_ind+5] = [line.replace(change[freeze],change[-freeze]) for line in file_lines[start_ind+2:start_ind+5]]
        
        #Swap period
        file_lines[start_ind+7] = file_lines[start_ind+7].replace(change[freeze],change[-freeze])

    elif mod_type == 'p':
        
        start_ind = file_lines.index('{SPIN STATE}\n')

        #Swap pole angle 3
        file_lines[start_ind+4] = file_lines[start_ind+4].replace(change[freeze],change[-freeze])

        #Swap period
        file_lines[start_ind+7] = file_lines[start_ind+7].replace(change[freeze],change[-freeze])

    else:
        raise ValueError('Not a valid mod_type')

    #Overwrite file with edits
    f = open(fname, 'w')
    f.writelines(file_lines)
    f.close()

    logger.debug('Done')
    return 1


#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Freeze or unfreeze all variable factors of listed components in a modfile.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Beta and lambda ranges and steps
    parser.add_argument("fname",    type=str, help="Name of file to affect. If directory, will affect all .mod files in directory")
    parser.add_argument("mod_type", type=str, help="Type of component expected")
    parser.add_argument("freeze",   type=int, help="1 or -1 , 1 for (f to c) and -1 for (c to f)")

    parser.add_argument("-c", "--components", nargs='+', type=int, default=[],
                        help="Optional list of components to affect (ellipse only)")

    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    if args.mod_type not in ['e','v','h','s','p']:
        error_exit('Cannot understand input mod_type. Check documentation for valid inputs')

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    if Path(args.fname).is_file():
        logger.info(f'Running script on file {args.fname}')
        freeze_mod(*vars(args).values())
    elif Path(args.fname).is_dir():
        logger.info(f'Running script on directory {args.fname}/*.mod')
        modfiles = glob.glob(f'{args.fname}/*.mod')
        for mod in modfiles:
            freeze_mod(mod,args.mod_type,args.freeze,args.components)
    else:
        raise error_exit('Cannot find file or directory with name [fname]')


if __name__ == "__main__":
    main()

