#Last modified by @recannon on 26/10/2026

#Runs write action and compiles output into a single pdf

import argparse
import logging
from pathlib import Path
from pyshape.cli.cli_config import logger
from pyshape import utils
from pyshape.obs.obs_io import obsFile
import pyshape.log_file as log_file
import tempfile
import subprocess
from pyshape.plotting import quick_routines as qp

def run_and_compile_write(wparfile:str|Path, modfile:str|Path, obsfile:str|Path,
                          wpar_logfile:str|Path,
                          dd_no_cols:int, dd_res:bool, 
                          dd_figfile:str|Path, cw_figfile:str|Path, lc_figfile:str|Path)

    write_inputs =[Path(f).resolve() for f in [wparfile,modfile,obsfile]]

    with tempfile.TemporaryDirectory() as tmp:
        
        tmp_path = Path(tmp)
        logger.info('Running moments')
        utils.run_shape(write_inputs, run_dir=tmp_path, out_log=wpar_logfile)
        
        #Print chisqr. Can treat the wpar file as a log file for this purpose
        chisqr = log_file.read(wpar_logfile)['ALLDATA']
        logger.info(f'Chisqr: {chisqr}')
        
        #Read obsfile to check for which data types are present
        obs_sets  = obsFile.from_file(obsfile).datasets
        set_types = set(o.set_type for o in obs_sets) 
       
        logger.info('Creating jpgs')
        
        #delay-Doppler requires stacking of pgm images
        if 'delay-doppler' in set_types:
            
            obs_frames = sorted(tmp_path.glob('obs_*.pgm'))
            fit_frames = sorted(tmp_path.glob('fit_*.pgm'))
            res_frames = sorted(tmp_path.glob('res_*.pgm')) if dd_res else []
            sky_frames = [Path(str(f).replace('obs_', 'sky_').replace('.pgm', '.ppm')) for f in obs_frames]
            no_frames = len(obs_frames)
            no_rows = no_frames // dd_no_cols + int(no_frames % dd_no_cols != 0)
            n_components = 4 if dd_res else 3
            dd_fits_ppm = tmp_path / 'dd_fits.ppm'
            dd_fits_jpg = dd_figfile
            script_lines = []
            
            #Stacks columns
            column_files = []
            for c in range(dd_no_cols):
                idxs = range(c * no_rows, min((c + 1) * no_rows, no_frames))
                flat_files = []
                for i in idxs:
                    flat_files += [obs_frames[i], fit_frames[i]]
                    if dd_res:
                        flat_files.append(res_frames[i])
                    flat_files.append(sky_frames[i])

                column_file = tmp_path / f'column_{c:02}.ppm'
                column_files.append(column_file)
                cmd = utils.ppmstack_cmd_list(flat_files, column_file, no_cols=n_components)
                script_lines.append(" ".join(cmd))

            #Commands for combine columns side by side and convert to jpg
            cmd = utils.ppmstack_cmd_list(column_files, dd_fits_ppm, no_cols=dd_no_cols)
            script_lines.append(" ".join(cmd))
            cmd = utils.ffmpeg_ppm2jpg_list(dd_fits_ppm, dd_fits_jpg)
            script_lines.append(" ".join(cmd))

            #Write all commands in a script and run together
            script_path = tmp_path / 'dd_stack.sh'
            script_path.write_text("\n".join(script_lines) + "\n")
            with open(tmp_path / 'dd_stack.log', 'w') as log:
                subprocess.run(['bash', str(script_path)], stdout=log,
                                stderr=subprocess.STDOUT, check=True, cwd='waction')

        #lc and cw can be plotted with functions
        if 'lightcurve' in set_types:
            lc_fits = sorted(tmp_path.glob("fit_??.dat"))
            #Create lightcurve plot
            qp.quick_lightcurves(lc_fits, show=False, save=lc_figfile)

        if 'doppler' in set_types:
            cw_fits = sorted(tmp_path.glob("fit_??_??.dat"))
            #Create plot
            qp.quick_doppler(cw_fits, show=False, save=cw_figfile)



#=== Functions for parsing args beneath this point ===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Runs shape write action and saves results as a collection of jpgs.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')

    input_group = parser.add_argument_group('Compulsory input files')
    input_group.add_argument('wparfile', type=str, help='write action file')  
    input_group.add_argument('modfile',  type=str, help='modfile')
    input_group.add_argument('obsfile',  type=str, nargs='?', help='obsfile (if mpar requires)')
    
    filedir_group = parser.add_argument_group('Specify output files')
    filedir_group.add_argument('--wpar_logfile',type=Path,default='./write.log',
                               help='File name and path for SHAPE output [./write.log]')
    filedir_group.add_argument('--dd-figfile',type=Path,default='./dd_fits.jpg',
                               help='File name and path of output jpg for delay-Doppler [./dd_fits.jpg]')
    filedir_group.add_argument('--cw-figfile',type=Path,default='./cw_fits.jpg',
                               help='File name and path of output jpg for CWs [./cw_fits.jpg]')
    filedir_group.add_argument('--lc-figfile',type=Path,default='./lc_fits.jpg',
                               help='File name and path of output jpg for lightcurves [./lc_fits.jpg]')
    
    dd_group = parser.add_argument_group('Delay-Doppler figure formatting options')
    dd_group.add_argument('--dd-no-cols', type=int, default=3,
                          help='Number of columns for delay-Doppler figure formatting [3]')
    dd_group.add_argument('--dd_res', type=bool, action='store_true',
                          help='Boolean toggle to display dd residuals [False]')
    
    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #Check files exist
    args.mparfile = utils.check_file(args.mparfile)
    args.modfile = utils.check_file(args.modfile)
    args.obsfile = utils.check_file(args.obsfile)

    return args

def main():
    args = parse_args()
    args = validate_args(args)    
    
    run_and_compile_write(args.wparfile, args.modfile, args.obsfile,
                          args.logfile, args.figfile)

if __name__ == '__main__':
    main()


