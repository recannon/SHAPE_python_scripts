#Last modified by @recannon on 26/10/2026

#Runs moments action and compiles output into a single jpg

import argparse
import logging
from pathlib import Path
from pyshape.cli.cli_config import logger
from pyshape import utils
import tempfile
import subprocess

def compile_moments_output(pa_view_files, tmp_path, out_jpg, log_file):
    pa_view_files = sorted(utils.check_file(f) for f in pa_view_files)
    pos_files = [f for f in pa_view_files if 'pos' in f.name]
    neg_files = [f for f in pa_view_files if 'neg' in f.name]
    out_jpg = Path(out_jpg).resolve()
    log_file = Path(log_file).resolve()
    temp_ppm = tmp_path / 'pa_views.ppm'

    ppmstack_cmd = utils.ppmstack_cmd_list(pos_files + neg_files, temp_ppm, 3)
    ffmpeg_cmd = utils.ffmpeg_ppm2jpg_list(temp_ppm, out_jpg)
    
    #Writes to same log file as moments action, with a separator
    with open(log_file, 'a') as log:
        for cmd in (ppmstack_cmd, ffmpeg_cmd):
            logger.debug(f'Running: {" ".join(map(str, cmd))}')
            log.write(f'\n--- {" ".join(map(str, cmd))} ---\n')
            log.flush()
            subprocess.run(cmd, cwd=tmp_path, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
    return

def run_and_compile_moments(mparfile, modfile, obsfile,
                            mpar_logfile, figfile):
    
    #absolute paths required as SHAPE runs from tmp_dir    
    mparfile, modfile = Path(mparfile).resolve(), Path(modfile).resolve()
    moments_inputs = [mparfile, modfile]
    if obsfile:
        moments_inputs.append(Path(obsfile).resolve())

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        logger.info('Running moments')
        utils.run_shape(moments_inputs, run_dir=tmp_path, out_log=mpar_logfile)
        
        #Collage mpar figures
        logger.info('Creating moments jpg')
        pa_files = sorted(tmp_path.glob('pa*'))
        compile_moments_output(pa_files, tmp_path, figfile, mpar_logfile)
    
    return True


#=== Functions for parsing args beneath this point ===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Runs shape moment action and saves results as a jpg.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')

    input_group = parser.add_argument_group('Compulsory input files')
    input_group.add_argument('mparfile', type=str, help='moments action file')  
    input_group.add_argument('modfile',  type=str, help='modfile')
    input_group.add_argument('obsfile',  type=str, nargs='?', help='obsfile (if mpar requires)')
    
    filedir_group = parser.add_argument_group('Specify default paths')
    filedir_group.add_argument('--mpar_logfile',type=Path,default='./moments.log',
                               help='File name and path for SHAPE output')
    filedir_group.add_argument('--figfile',type=Path,default='./moments.jpg',
                               help='File name and path of output jpg')
    
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
    args.obsfile = utils.check_file(args.obsfile) if args.obsfile else None

    return args

def main():
    args = parse_args()
    args = validate_args(args)    
    
    run_and_compile_moments(args.mparfile, args.modfile, args.obsfile,
                            args.mpar_logfile, args.figfile)

if __name__ == '__main__':
    main()


