#Last modified 10/07/25

import argparse
import dataclasses
import logging
import os
import shutil
import subprocess
from pathlib import Path
import numpy as np
from pyshape import mod_file
from pyshape.outfmt import logger, error_exit
from pyshape.utils import check_scan_param_vals, check_no_files

def line_scan_setup(p,mod_template,obs_template,outf):

    mod_info = mod_file.read(mod_template)

    #Delete files in mod or obsfiles

    components   = mod_info.components
    optical_laws = mod_info.optical_laws
    radar_laws   = mod_info.radar_laws
    spin_state   = mod_info.spin_state

    p_vals = np.arange(p.min,p.max,p.step)        

    #Find whether param is in spin state or shape
    param_owner_index = None
    variable_mods = [components[0], spin_state]
    for i, dclass in enumerate(variable_mods):
        
        #Often the useful values are stored as properties, rather than fields (in spin state atleast)
        field_names = [f.name for f in dataclasses.fields(dclass)]
        property_names = [k for k, v in vars(dclass.__class__).items() if isinstance(v, property)]
        all_names = field_names + property_names

        if p.name in all_names:
            logger.debug(f'{p.name} found in {dclass.__class__.__name__}')
            param_owner_index = i
            break

    if param_owner_index == None:
        error_exit(f'Could not match param {p.name} to a dataclass')

    if param_owner_index == 0 and len(components) != 1:
        error_exit('Expected a single component when scanning over shape parameter')


    #Create files
    with open(f'{outf}/namecores.txt','w') as namecores:
        #Create new files
        for p_val in p_vals:
            
            #Update value and freeze
            setattr(variable_mods[param_owner_index], p.name, p_val)
            setattr(variable_mods[param_owner_index].freeze_state, p.name, 'c')
            
            new_ModFile = mod_file.ModFile(
                components=[variable_mods[0]],
                spin_state=variable_mods[1],
                optical_laws=optical_laws,
                radar_laws=radar_laws)
            
            #Write new file
            if p.name == 'angle2':
                namecore = f'zscan{p_val:.3f}'
            else:
                namecore = f'{p.name}_{p_val:+.3f}'
            mod_file.write(new_ModFile,f'{outf}/modfiles/{namecore}.mod')
            shutil.copy(obs_template, f'{outf}/obsfiles/{namecore}.obs')
            namecores.write(f'{namecore}\n')

    no_files = len(p_vals)
    return no_files

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Create mod and obs files in modfiles and obsfiles for a line scan",
                                    epilog="Either --z-scan or --param must be specified.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #param ranges and steps
    param_options = parser.add_argument_group('Parameter input formats. Z-scan used to avoid specifying scale2')
    param_options.add_argument('-p', '--param', nargs=4, metavar=('NAME', 'MIN', 'MAX', 'STEP'),
                            help="Parameter and scan range: e.g. scale2 0.9 1.1 0.02")
    param_options.add_argument('-z', '--z-scan', nargs=3, metavar=('ZMIN', 'ZMAX', 'ZSTEP'),
                            help="Z-scan mode: provide z scale min, max, step as 3 floats")

    #Template files
    file_group = parser.add_argument_group("Optional file inputs. Defaults to [type].template")
    file_group.add_argument("-mod", "--mod-template", type=Path, default=Path('./mod.template'),
                            help="The template mod file. Will keep f/c state and freeze new param value")
    file_group.add_argument("-obs", "--obs-template", type=Path, default=Path('./obs.template'),
                            help="The template obs file. Will not be changed")

    return parser.parse_args()

def validate_args(args):
    
    #check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #If --param is called
    if args.param:
        #Dont let z-scan is called:
        if args.z_scan:
            error_exit('Cannot use --z-scan mode when specifying --param')
        #Check values are floats and min<max and step>0
        args.param = check_param_vals(args.param,float)
    
    #Else if z_scan
    elif args.z_scan:

        #Check values and set to param
        z_info = ['scale2',*args.z_scan]
        args.param = check_param_vals(z_info,float)

        if args.param.min <= 0:
            error_exit('Minimum z-scale value must be greater than 0')
    
    else:
        error_exit('This message should never appear so its time to cry')

    #check files exist
    if not args.mod_template.exists():
        error_exit(f"Mod template not found: {args.mod_template}")
    if not args.obs_template.exists():
        error_exit(f"Obs template not found: {args.obs_template}")
    args.mod_template = args.mod_template.resolve()
    args.obs_template = args.obs_template.resolve()

    return args

def main():

    args = parse_args()
    args = validate_args(args)

    logger.info(f'Using templates: {args.mod_template} and {args.obs_template}')

    cwd = Path.cwd()
    
    #Check directories exist
    Path(f'{cwd}/modfiles').mkdir(exist_ok=True)
    Path(f'{cwd}/obsfiles').mkdir(exist_ok=True)
    Path(f'{cwd}/logfiles').mkdir(exist_ok=True)
    
    #Run line_scan
    no_files = line_scan_setup(args.param,
                               args.mod_template, args.obs_template,
                               cwd)
    
    check_no_files(no_files)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    subprocess.run(["sbatch", f"--array=1-{no_files}", f'{script_dir}/launch_fitting.sbatch'])
    logger.info(f'Submitted SLURM array jobs 1-{no_files}')

    return True

if __name__ == "__main__":
    main()
