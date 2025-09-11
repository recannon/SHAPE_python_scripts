
#Last modified 10/07/25

import argparse
import dataclasses
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
from rich.progress import Progress
from pyshape import mod_file
from pyshape.outfmt import logger, error_exit, console
from pyshape.utils import check_scan_param_vals, check_no_files

#python -m grid_scan -ps -90 90 10 0 360 10 -mod mod.h.template -obs obs.h.template
#python -m grid_scan -ps -90 90 10 0 360 10 -a2r 0 355 5
#non polescan grid searches are untested but should work. Let me know if not
#This code (and everything handling mod files) is currently quite inefficient, so is on the list to be improved. 
#But it works

#===Pole/gridscan functions===
def grid_scan_setup(p1,p2,mod_template,obs_template,outf,angle2=0):

    mod_info = mod_file.read(mod_template)

    components   = mod_info.components
    optical_laws = mod_info.optical_laws
    radar_laws   = mod_info.radar_laws
    spin_state   = mod_info.spin_state

    param_names = [p1.name, p2.name]

    if param_names == ['bet', 'lam']:
        p1_vals,p2_vals = setup_polescan_lists(p1.min,p1.max,p1.step,p2.min,p2.max,p2.step)
        polescan = True
    elif param_names == ['lam','bet']:
        p2_vals,p1_vals = setup_polescan_lists(p2.min,p2.max,p2.step,p1.min,p1.max,p1.step)
        polescan = True
    else:
        p1_vals = np.arange(p1.min,p1.max+p1.step,p1.step)
        p2_vals = np.arange(p2.min,p2.max+p2.step,p2.step)
        P1, P2 = np.meshgrid(p1_vals, p2_vals, indexing='ij')
        p1_vals = P1.flatten()
        p2_vals = P2.flatten()
        polescan = False

    #Find whether param is in spin state or shape
    param_owner_indices = []
    for param in param_names:
        param_owner_index = None
        variable_mods = [*components, spin_state]
        for i, dclass in enumerate(variable_mods):
            
            #Often the useful values are stored as properties, rather than fields (in spin state atleast)
            field_names = [f.name for f in dataclasses.fields(dclass)]
            property_names = [k for k, v in vars(dclass.__class__).items() if isinstance(v, property)]
            all_names = field_names + property_names

            if param in all_names:
                logger.debug(f'{param} found in {dclass.__class__.__name__}')
                param_owner_index = i
                break

        if param_owner_index == None:
            error_exit(f'Could not match param {param} to a dataclass')

        if param_owner_index == 0 and len(components) != 1:
            error_exit('Expected a single component when scanning over shape parameter')

        param_owner_indices.append(param_owner_index)

    #Create files
    with open(f'{outf}/namecores.txt','w') as namecores:
        #Create new files
        for p1_val,p2_val in zip(p1_vals,p2_vals):
            
            #Update values and freeze states
            setattr(variable_mods[param_owner_indices[0]], param_names[0], p1_val)
            setattr(variable_mods[param_owner_indices[0]].freeze_state, param_names[0], 'c')
            setattr(variable_mods[param_owner_indices[1]], param_names[1], p2_val)
            setattr(variable_mods[param_owner_indices[1]].freeze_state, param_names[1], 'c')
            
            #Adjust angle 2
            if polescan:
                setattr(variable_mods[-1], 'angle2', angle2)
                setattr(variable_mods[-1].freeze_state, 'angle2', 'f')

            new_ModFile = mod_file.ModFile(
                components=variable_mods[:-1],
                spin_state=variable_mods[-1],
                optical_laws=optical_laws,
                radar_laws=radar_laws)
            
            #Write new file
            if polescan:
                namecore = f'lat{p1_val:+03d}lon{p2_val:03d}'
            else:
                namecore = f'{p1.name}{p1_val:+.3f}{p2.name}{p2_val:+3f}'
            mod_file.write(new_ModFile,f'{outf}/modfiles/{namecore}.mod')
            shutil.copy(obs_template, f'{outf}/obsfiles/{namecore}.obs')
            namecores.write(f'{namecore}\n')

    no_files = len(p1_vals)
    return no_files

def setup_polescan_lists(bet_min,bet_max,bet_step,lam_min,lam_max,lam_step):
    #Bet values can be linear as all lines of longitude are great circles
    bet_array = np.arange(bet_min,bet_max+bet_step,bet_step)

    #Assuming lam_step is given for the largest small circle, we scale the others accordingly.
    #Do this by calculating the distance around the small circle for the largest small circle
    sc_radii = np.cos(np.deg2rad(bet_array))
    max_radii = np.max(sc_radii)
    lam_step_dist = 2*np.pi*max_radii * lam_step/360

    #Create a list of divisors for lambda range to round steps down to
    lam_range = int(lam_max-lam_min)
    divisors = [d for d in range(1,lam_range+1) if lam_range % d == 0]

    #Then change the step on other small circles to have the distance be the same
    lam_step_b = lam_step_dist*360/(2*np.pi*sc_radii)
    lam_step_b = [max([d for d in divisors if d <= el+1]) for el in lam_step_b]
    
    #Create beta and lambda arrays
    beta_list   = []
    lambda_list = []
    #And adjust to avoid duplicate values
    for bet,lam_s in zip(bet_array,lam_step_b):
        
        #Checks to not have duplicate files be made.
        if bet == 90 or bet == -90: #Poles only need one value
            lam_array = np.array([0])
        elif lam_min == 0 and lam_max == 360: #360 and 0 are the same
            lam_array = np.arange(lam_min,lam_max,lam_s)
        else:
            lam_array = np.arange(lam_min,lam_max+lam_s,lam_s)

        for l in lam_array:
            lambda_list.append(int(l))
            beta_list.append(int(bet))
    return beta_list,lambda_list


#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Create mod and obs files in modfiles and obsfiles for a grid scan",
                                    epilog="Either --polescan or both --param1 and --param2 must be specified.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Two param names and grid info
    param_group = parser.add_argument_group("Parameters to scan (not required if using --polescan)")
    param_group.add_argument('-p1', '--param1', nargs=4, metavar=('NAME', 'MIN', 'MAX', 'STEP'),
                            help="First parameter and scan range: e.g. scale2 0.9 1.1 0.02")
    param_group.add_argument('-p2', '--param2', nargs=4, metavar=('NAME', 'MIN', 'MAX', 'STEP'),
                            help="Second parameter and scan range: e.g. scale2 0.9 1.1 0.02")

    #Polescan, assume beta first
    polescan_group = parser.add_argument_group("Polescan usage with angle2 control (not used with --param1 and --param2)")
    polescan_group.add_argument('-ps', '--polescan', nargs=6, metavar=('BMIN', 'BMAX', 'BSTEP', 'LMIN', 'LMAX', 'LSTEP'),
                            help="Polescan mode: provide beta/lambda min, max, step as 6 integers")
    polescan_group.add_argument('-a2', '--angle2', type=int, default=None,
                            help='Set angle2 (float, degrees) for all files. Default: 0')
    polescan_group.add_argument('-a2r', '--angle2-range', nargs=3, metavar=('START', 'END', 'STEP'),
                            help="Run for a range of angle2 values (instead of --angle2).")

    #Template files
    file_group = parser.add_argument_group("Optional file inputs. Defaults to [type].template")
    file_group.add_argument("-mod", "--mod-template", type=Path, default=Path('./mod.template'),
                            help="The template mod file. Will keep f/c state and freeze new param value")
    file_group.add_argument("-obs", "--obs-template", type=Path, default=Path('./obs.template'),
                            help="The template obs file. Will not be changed")

    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logger.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #If param1 and param2 are called
    if args.param1 and args.param2:
        #Don't allow polescan to also be called
        if args.polescan:
            error_exit("Cannot use --polescan when using specifying --param1 and --param2")

        #Dont let angles be called
        if args.angle2_range or args.angle2:
            error_exit('Cannot use --angle2 or --angle2-range outside of --polescan mode')
        
        args.param1 = check_scan_param_vals(args.param1,float)
        args.param2 = check_scan_param_vals(args.param2,float)


    #Else if polescan is used:
    elif args.polescan:
        
        #If angle2_range is called
        if args.angle2_range:
            #Dont let angle2 be called as well
            if args.angle2 is not None:
                error_exit("Use only one of --angle2 or --angle2-range.")
            #Check vals
            a2_info = ['angle2-range',*args.angle2_range]
            args.angle2_range = check_scan_param_vals(a2_info,int)
        #Elif angle2 is not called
        elif args.angle2 is None:
            args.angle2 = 0

        #Check polescan vals and set to param1 and param2
        bet_info = ['bet',*args.polescan[:3]]
        lam_info = ['lam',*args.polescan[3:]]
        args.param1 = check_scan_param_vals(bet_info, int)
        args.param2 = check_scan_param_vals(lam_info, int)

        #Ranges of lam and bet
        if args.param1.min < -90 or args.param1.max > 90:
            error_exit('Invalid range for beta ( -90 =< bet =< 90)')
        if args.param2.min < 0 or args.param2.max > 360:
            error_exit('Invalid range for lambda ( 0 =< lam =< 360)')


    elif not args.polescan and not (args.param1 and args.param2):
        error_exit("You must specify either --polescan or both --param1 and --param2.")

    else:
        error_exit("This message should never appear so its time to cry")

    #check files exist
    if not args.mod_template.exists():
        error_exit(f"Mod template not found: {args.mod_template}")
    if not args.obs_template.exists():
        error_exit(f"Obs template not found: {args.obs_template}")
    args.mod_template = args.mod_template.resolve()
    args.obs_template = args.obs_template.resolve()

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    logger.info(f'Using templates: {args.mod_template} and {args.obs_template}')

    cwd = Path.cwd()
    

    if not args.angle2_range:
        
        Path(f'{cwd}/modfiles').mkdir(exist_ok=True)
        Path(f'{cwd}/obsfiles').mkdir(exist_ok=True)
        Path(f'{cwd}/logfiles').mkdir(exist_ok=True)

        no_files = grid_scan_setup(args.param1, args.param2,
                                   args.mod_template, args.obs_template,
                                   cwd,args.angle2)
        
        check_no_files(no_files)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.run(["sbatch", f"--array=1-{no_files}", f'{script_dir}/launch_fitting.sbatch'])
        logger.info(f'Submitted SLURM array jobs 1-{no_files}')

    elif args.angle2_range:
        
        #Make subscan folder if doesn't already exist
        Path(f'{cwd}/subscans').mkdir(exist_ok=True)
        #Then empty it from previous scans
        
        #Angle 2 list
        a2_min,a2_max,a2_step = args.angle2_range.min, args.angle2_range.max, args.angle2_range.step
        a2_list = np.arange(a2_min,a2_max+a2_step,a2_step)
        
        #Make directories
        with Progress(console=console,transient=True) as pb:
            t1 = pb.add_task('Creating subscan directories',total=len(a2_list))
            
            for a2 in a2_list:
                #Create a2 directory in subscans
                subdir = f'{cwd}/subscans/{a2:03d}'
                Path(subdir).mkdir(exist_ok=True)
                Path(f'{subdir}/modfiles').mkdir(exist_ok=True)
                Path(f'{subdir}/obsfiles').mkdir(exist_ok=True)
                Path(f'{subdir}/logfiles').mkdir(exist_ok=True)

                logging.info(f'Creating files in {subdir}')

                # shutil.copytree(f'{cwd}/par', f'{subdir}/par', dirs_exist_ok=True)  # dirs_exist_ok=True allows overwriting

                no_files = grid_scan_setup(args.param1, args.param2,
                                    args.mod_template, args.obs_template,
                                    subdir, a2)  
                
                pb.update(task_id=t1,advance=1)         

        shutil.copy(f'{subdir}/namecores.txt', f'{cwd}/namecores.txt')
        check_no_files(no_files)

        a2_strs = [str(angle) for angle in a2_list]
        script_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.run(["sbatch", f"--array=1-{no_files}", f'{script_dir}/launch_fitting.sbatch', ' '.join(a2_strs)])
        logger.info(f'Submitted SLURM array jobs 1-{no_files}')
        

    else:
        error_exit('This message shouldnt appear so its time to cry')

    return True

if __name__ == "__main__":
    main()
