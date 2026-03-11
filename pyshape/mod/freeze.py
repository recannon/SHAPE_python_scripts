#Last modified 11/01/2026

import argparse
import glob
import logging
from pathlib import Path
from ..cli_config import logger, error_exit
from .mod_io import modFile

#python -m freeze_mod modfiles v 1
#python -m freeze_mod test.mod e 0 1

#Customisable, but cannot use e, v, or h
SPIN_DEFAULTS = {
    's': ('lam', 'bet', 'phi', 'P'),
    'p': ('phi', 'P'),
}

def freeze_mod(fname, mod_type, freeze, components=None):
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
        freeze     : c, f, or = . Whatever it will be set to
        components : Optional list of entries for ellipsoid/harmonic components numbers you want to affect. If none, affects all.
    '''

    logger.debug(f'{fname} : Setting group {mod_type} to {freeze}')

    mod_info = modFile.from_file(fname)

    mod_type = mod_type.lower()

    mod_dict = {
        'e' : 'ellipse',
        'h' : 'harmonic',
        'v' : 'vertex',
    }

    if mod_type in ['e','v','h']:
        
        comp_type = mod_dict[mod_type]
        _freeze_components(
            mod_info=mod_info,
            freeze=freeze,
            components=components,
            comp_type=comp_type,
            )
    
    #Spin state objects (customisable above)
    elif mod_type in SPIN_DEFAULTS:
        mod_info.spinstate.freeze_params(freeze, fields=SPIN_DEFAULTS[mod_type])

    mod_info.write(fname)

    logger.debug('Done')
    return 1

def _freeze_components(mod_info, freeze, components, comp_type):
    
    component_list = mod_info.components
    no_components = len(component_list)

    if components is None:
        components = range(no_components)
    elif max(components) >= no_components:
        error_exit(f'File does not have {max(components) + 1} components')

    for idx in components:
        if component_list[idx].type != comp_type:
            error_exit(f'Component {idx} is not of type {comp_type}')

    for idx in components:
        component_list[idx].freeze_params(freeze)
        

#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Freeze or unfreeze all variable factors of listed components in a modfile.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Beta and lambda ranges and steps
    parser.add_argument("fname",    type=str, help="Name of file to affect. If directory, will affect all .mod files in directory")
    parser.add_argument("mod_type", type=str, help="Type of component expected")
    parser.add_argument("freeze",   type=str, help="[ f, c, = ] . Change variables to this str")

    parser.add_argument("-c", "--components", nargs='+', type=int, default=None,
                        help="Optional list of components to affect (ellipse only)")

    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    if args.mod_type not in ['e','v','h','s','p']:
        error_exit('Cannot understand input mod_type. Check documentation for valid inputs')

    if args.freeze not in ['f','c','=']:
        error_exit('freeze string must be one of "f", "c", or "="')

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    if Path(args.fname).is_file():
        logger.info(f'Running script on file {args.fname}')
        freeze_mod(args.fname,args.mod_type,args.freeze,args.components)
    elif Path(args.fname).is_dir():
        logger.info(f'Running script on directory {args.fname}/*.mod')
        modfiles = glob.glob(f'{args.fname}/*.mod')
        for mod in modfiles:
            freeze_mod(mod,args.mod_type,args.freeze,args.components)
    else:
        raise error_exit('Cannot find file or directory with name [fname]')


if __name__ == "__main__":
    main()

