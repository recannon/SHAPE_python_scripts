#Last modified by @recannon 08/10/2026

#08/10/2026 - Added functionality with map action
#27/08/2026 - More Documentation

#Used to change the freeze state of sets of parameters in a modfile, or directory of modfiles
#python -m freeze_mod modfiles v f      #Sets all vertex parameters to free (f) in all .mod files in modfiles
#python -m freeze_mod test.mod s =      #Sets all spin state parameters to equal (=) in test.mod
#python -m freeze_mod test.mod e c -c 0  #Sets all ellipsoid parameters to constant (c) in test.mod in component 0 only

#Customisable, but cannot use e, v, or h (these are for shape)
SPIN_DEFAULTS = {
    's': ('lam', 'bet', 'phi', 'P'),
    'p': ('phi', 'P'),
}

MOD_DICT = {
    'e' : 'ellipse',
    'h' : 'harmonic',
    'v' : 'vertex',
}

import argparse
import itertools
import logging
import numpy as np
from pathlib import Path
import re
from .mod_io import modFile
from ..cli.cli_config import logger, error_exit
from ..utils import check_file

def freeze_mod(fname, mod_type, freeze, components=None, map_file=None):
    '''
    Takes modfile {fname} and freezes or unfreezes all variable factors for specified components. 

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

    if map_file is not None and mod_type == 'v':

        component_list = mod_info.components
        
        #Reads facets and sorted by component first, then facet number. Removes duplicates
        facets = sorted({(int(m.group(1)), int(m.group(2))) for l in open(map_file)
                 if (m := re.match(r'# comp (\d+) facet\s+(\d+)', l))})
        logger.info(f'{len(facets)} facets found in map file {map_file}')
        
        for comp_no, group in itertools.groupby(facets, key=lambda x: x[0]):
            if components is not None and comp_no not in components:
                continue
            comp = component_list[comp_no]
            listed = set(np.unique(comp.facets[[f for _, f in group]]).tolist())
            comp.vertices_freeze = [freeze if i in listed else s
                                    for i, s in enumerate(comp.vertices_freeze)]        
            logger.info(f'Changing {len(listed)} vertices in component {comp_no} to {freeze}')
        
    elif mod_type in MOD_DICT:
        
        comp_type = MOD_DICT[mod_type]
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
    '''Parse command-line arguments.'''
    parser = argparse.ArgumentParser(description='Freeze or unfreeze all variable factors of listed components in a modfile.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')

    #Beta and lambda ranges and steps
    parser.add_argument('fname',    type=str, help='Name of file to affect. If directory, will affect all .mod files in directory')
    parser.add_argument('mod_type', type=str, help='Type of component expected')
    parser.add_argument('freeze',   type=str, help='[ f, c, = ] . Change variables to this str')
    parser.add_argument('--map', type=str, default=None, 
                        help='Can be used to affect only vertices visible in provided map file. Use with mod_type = v')

    parser.add_argument('-c', '--components', nargs='+', type=int, default=None,
                        help='Optional list of components to affect')

    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    if args.mod_type not in MOD_DICT and args.mod_type not in SPIN_DEFAULTS:
        error_exit('Cannot understand input mod_type. Check documentation for valid inputs')
    elif args.map is not None:
        if args.mod_type != 'v':
            error_exit('Cannot use --map without mod_type = v')
        args.map = check_file(args.map)
        
    if args.freeze not in ['f','c','=']:
        error_exit('freeze string must be one of "f", "c", or "="')

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    if Path(args.fname).is_file():
        logger.info(f'Running script on file {args.fname}')
        freeze_mod(args.fname,args.mod_type,args.freeze,args.components,args.map)
    elif Path(args.fname).is_dir():
        logger.info(f'Running script on directory {args.fname}/*.mod')
        modfiles = Path(args.fname).glob('*.mod')
        for mod in modfiles:
            freeze_mod(mod,args.mod_type,args.freeze,args.components,args.map)
    else:
        raise error_exit('Cannot find file or directory with name [fname]')


if __name__ == '__main__':
    main()

