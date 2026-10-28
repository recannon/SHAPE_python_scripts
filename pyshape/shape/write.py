#Last modified by @recannon on 26/10/2026

#Runs write action and compiles output into a single pdf

import argparse
import logging
from pathlib import Path
from ..cli.config import logger
from .. import utils
from ..obs.obs_io import obsFile
from .. import log_file
import tempfile
from ..plotting import delay_doppler, doppler, lightcurves

def run_and_compile_write(wparfile:str|Path, modfile:str|Path, obsfile:str|Path,
                          wpar_logfile:str|Path,
                          dd_no_cols:int, dd_res:bool, 
                          dd_figfile:str|Path, cw_figfile:str|Path, lc_figfile:str|Path):

    write_inputs =[Path(f).resolve() for f in [wparfile,modfile,obsfile]]

    with tempfile.TemporaryDirectory() as tmp:
        
        tmp_path = Path(tmp)
        logger.info('Running write')
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
            sky_frames = [f.with_name(f.name.replace('obs_', 'sky_')).with_suffix('.ppm') for f in obs_frames]
                                    
            delay_doppler.format_delay_doppler_images(obs_frames,fit_frames,sky_frames,
                                                      dd_no_cols,dd_figfile,res_frames=res_frames)
            
        #lc and cw can be plotted with functions
        if 'lightcurve' in set_types:
            lc_fits = sorted(tmp_path.glob("fit_??.dat"))
            #Create lightcurve plot
            lightcurves.quick_lightcurves(lc_fits, show=False, save=lc_figfile)

        if 'doppler' in set_types:
            cw_fits = sorted(tmp_path.glob("fit_??_??.dat"))
            #Create plot
            doppler.quick_doppler(cw_fits, show=False, save=cw_figfile)

    return chisqr

#=== Functions for parsing args beneath this point ===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Runs shape write action and saves results as a collection of jpgs.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')

    input_group = parser.add_argument_group('Compulsory input files')
    input_group.add_argument('wparfile', type=str, help='write action file')  
    input_group.add_argument('modfile',  type=str, help='modfile')
    input_group.add_argument('obsfile',  type=str, help='obsfile')
    
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
    dd_group.add_argument('--dd_res', action='store_true',
                          help='Boolean toggle to display dd residuals [False]')
    
    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #Check files exist
    args.wparfile = utils.check_file(args.wparfile)
    args.modfile = utils.check_file(args.modfile)
    args.obsfile = utils.check_file(args.obsfile)

    return args

def main():
    args = parse_args()
    args = validate_args(args)    
    
    run_and_compile_write(args.wparfile, args.modfile, args.obsfile,
                          args.wpar_logfile,
                          args.dd_no_cols, args.dd_res,
                          args.dd_figfile, args.cw_figfile, args.lc_figfile)

if __name__ == '__main__':
    main()


