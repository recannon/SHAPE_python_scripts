#Last modified by @recannon on 07/10/2026

#07/10/2026 - Moved all moments processing out of this script into moments.py
#15/09/2026 - Subfunctions from utils for moments and dd routines
#01/06/2026

import argparse
import logging
from pathlib import Path
import subprocess
from ..obs.obs_io import obsFile
from .cli_config import logger, error_exit
from .. import utils
from ..plotting import quick_routines as qp
from .. import log_file
from ..shape.moments import run_and_compile_moments 

def write_quick(modfile,obsfile,mparfile='par/mpar',wparfile='par/wpar',outdir='.',no_cols=3,res=False):
    """
    Run shape model fitting and post-processing.

    This function performs a shape moments and write action on provided files,
    generates figures for the fit, and collates them into a PDF summary report.

    Parameters:
        modfile (Path): Path to .mod file
        obsfile (Path): Path to .obs file
        mparfile (Path): Path to mpar parameter file
        wparfile (Path): Path to wpar parameter file
        no_cols  (int): Number of columns for delay-doppler stacking
        res (bool): Include residuals in output stacking
    """
    
    #Identifier to call pdf/log files
    identifier = f'{modfile.stem}__{obsfile.stem}' if modfile.stem != obsfile.stem else modfile.stem

    #Paths
    current_path = Path.cwd()
    waction_path = current_path / 'waction'
    temp_path    = waction_path / 'temp'
    maction_log  = waction_path / f'{identifier}.mpar.log'
    waction_log  = waction_path / f'{identifier}.wpar.log'
    
    #Changes filepaths to absolute paths. Needed as shape functions are run from ./waction, not ./
    modfile,obsfile = Path(modfile).resolve(),Path(obsfile).resolve()
    mparfile,wparfile = Path(mparfile).resolve(),Path(wparfile).resolve()

    #Makes sure both waction and waction/temp exist. Creates if not
    temp_path.mkdir(parents=True, exist_ok=True)

    #Empty waction folder without trying to remove directories
    #Ignore errors as there should not be anything of importance in temp
    utils.empty_dir(temp_path, remove_dirs=False, ignore_errors=True)

    #Runs moments and compiles result into a jpg
    #Going to assume that obsfile is not required to speed it up! (Only needed if you have show_unseen in mpar)
    run_and_compile_moments(mparfile, modfile, None, mpar_logfile=maction_log, figfile=temp_path / '1_mpar.jpg')

    #Run write action
    logger.info('Running write')
    utils.run_shape([wparfile, modfile, obsfile],
              run_dir=temp_path, out_log=waction_log)

    #Print chisqr. Can treat the wpar file as a log file for this purpose
    chisqr = log_file.read(waction_log)['ALLDATA']
    logger.info(f'Chisqr: {chisqr}')

    logger.info('Creating jpgs')

    #Read obsfile to check for which data types are present
    obs_sets  = obsFile.from_file(obsfile).datasets
    set_types = set(o.set_type for o in obs_sets) 
       
    #delay-Doppler requires stacking of pgm images
    if 'delay-doppler' in set_types:
        
        obs_frames = sorted(temp_path.glob('obs_*.pgm'))
        fit_frames = sorted(temp_path.glob('fit_*.pgm'))
        res_frames = sorted(temp_path.glob('res_*.pgm')) if res else []
        sky_frames = [Path(str(f).replace('obs_', 'sky_').replace('.pgm', '.ppm')) for f in obs_frames]
        no_frames = len(obs_frames)
        no_rows = no_frames // no_cols + int(no_frames % no_cols != 0)
        n_components = 4 if res else 3
        dd_fits_ppm = current_path / 'waction' / 'temp' / 'dd_fits.ppm'
        dd_fits_jpg = current_path / 'waction' / 'temp' / '2_dd_fits.jpg'
        script_lines = []
        
        #Stacks columns
        column_files = []
        for c in range(no_cols):
            idxs = range(c * no_rows, min((c + 1) * no_rows, no_frames))
            flat_files = []
            for i in idxs:
                flat_files += [obs_frames[i], fit_frames[i]]
                if res:
                    flat_files.append(res_frames[i])
                flat_files.append(sky_frames[i])

            column_file = temp_path / f'column_{c:02}.ppm'
            column_files.append(column_file)
            cmd = utils.ppmstack_cmd_list(flat_files, column_file, no_cols=n_components)
            script_lines.append(" ".join(cmd))

        #Commands for combine columns side by side and convert to jpg
        cmd = utils.ppmstack_cmd_list(column_files, dd_fits_ppm, no_cols=no_cols)
        script_lines.append(" ".join(cmd))
        cmd = utils.ffmpeg_ppm2jpg_list(dd_fits_ppm, dd_fits_jpg)
        script_lines.append(" ".join(cmd))

        #Write all commands in a script and run together
        script_path = temp_path / 'dd_stack.sh'
        script_path.write_text("\n".join(script_lines) + "\n")
        with open(temp_path / 'dd_stack.log', 'w') as log:
            subprocess.run(['bash', str(script_path)], stdout=log,
                            stderr=subprocess.STDOUT, check=True, cwd='waction')

    #lc and cw can be plotted with functions
    if 'lightcurve' in set_types:
        lc_fits = sorted(temp_path.glob("fit_??.dat"))
        #Create lightcurve plot
        qp.quick_lightcurves(lc_fits, show=False, save=temp_path / '3_lc_fits.jpg')

    if 'doppler' in set_types:
        cw_fits = sorted(temp_path.glob("fit_??_??.dat"))
        #Create plot
        qp.quick_doppler(cw_fits, show=False, save=temp_path / '4_cw_fits.jpg')

    #Resize jpgs
    resized = []
    for jpg in sorted(temp_path.glob('*.jpg')):
        out = temp_path / f'resized_{jpg.name}'
        subprocess.run(['convert', str(jpg), '-resize', '842', str(out)], check=True)
        resized.append(str(out))
    #Stack jpg files into a pdf
    output_name = outdir / f'{identifier}.pdf'
    subprocess.run(['convert', *map(str, resized), '-append', str(temp_path/'resized.jpg')], check=True)
    subprocess.run(['convert', str(temp_path/'resized.jpg'), str(output_name)], check=True)
    logger.info(f'Created PDF: {output_name}')
    
    return True

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Calls shape moment/write action and saves results as PDFs.',
                                     epilog='If writing polescan results with *files/lat{+02d}lon{03d}.* : Can use write_quick [lat] [lon]')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')

    input_group = parser.add_argument_group('Compulsory input files')    
    input_group.add_argument('modfile', type=str, nargs='?', help='modfile to write.')
    input_group.add_argument('obsfile', type=str, nargs='?', help='obsfile to write.')
    input_group.add_argument('--all', action='store_true',
                        help='Run write_fit for all files in namecores.txt')
    
    filedir_group = parser.add_argument_group('Specify default paths')
    filedir_group.add_argument('-m', '--mparfile', type=Path, default='./par/mpar',
                        help='mpar file to use. Default cwd/par/mpar')
    filedir_group.add_argument('-w', '--wparfile', type=Path, default='./par/wpar',
                        help='wpar file to use. Default cwd/par/wpar')
    filedir_group.add_argument('-o','--outdir', type=Path, default='.',
                        help='Directory to save fits. Default cwd')
    
    dd_group = parser.add_argument_group('Specify DD collage inputs')
    dd_group.add_argument('-r', '--residuals', action='store_true',
                        help='Include residuals in dd fit')
    dd_group.add_argument('-n', '--no-cols', default=3,
                        help='Number of columns for dd fit. Default is 3')
    
    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #Check optional inputs
    args.no_cols = utils.check_type(args.no_cols,'--no-cols',int)        
    args.mparfile = utils.check_file(args.mparfile)
    args.wparfile = utils.check_file(args.wparfile)
    args.outdir = utils.check_dir(args.outdir, create=True)

    #If all, don't check modfile/obsfile
    if args.all:
        if not Path('./namecores.txt').is_file():
            error_exit('Used --all but cannot find ./namecores.txt')
        if args.modfile or args.obsfile:
            logger.warning('Found modefile or obsfile provided with --all. Ignoring provided files')

    elif not args.modfile or not args.obsfile:
        error_exit('Must provide both obsfile and modfile (or use --all)')
    
    else:
        try: #Try turn into integers. If your file names are only integers it is a bit silly
            lat,lon = int(args.modfile), int(args.obsfile)

            logger.info('Super secret polescan mode activated')
            args.modfile = Path('modfiles') / f'lat{lat:+03d}lon{lon:03d}.mod'
            args.obsfile = Path('obsfiles') / f'lat{lat:+03d}lon{lon:03d}.obs'
        
        except: #Normal running mode
            args.modfile = Path(args.modfile)
            args.obsfile = Path(args.obsfile)
            
        #Check files exist
        args.modfile = utils.check_file(args.modfile)
        args.obsfile = utils.check_file(args.obsfile)

    return args

def main():
    args = parse_args()
    args = validate_args(args)    
    
    if args.all:
        logger.info('Running in --all mode. Processing all files from namecores.txt')
        with open('./namecores.txt') as f:
            namecores = [line.strip().split()[0] for line in f if line.strip()]

        for namecore in namecores:
            modfile = Path('modfiles') / f'{namecore}.mod'
            obsfile = Path('obsfiles') / f'{namecore}.obs'
            
            if not modfile.is_file():
                logger.warning(f'Cannot find {modfile}. Skipping')
                continue
            if not obsfile.is_file():
                logger.warning(f'Cannot find {obsfile}. Skipping')
            
            logger.info(f'Processing: {modfile} and {obsfile}')
            write_quick(modfile, obsfile,
                      args.mparfile, args.wparfile, args.outdir,
                      args.no_cols, args.residuals)

    elif args.modfile and args.obsfile:
        
        logger.info(f'Processing: {args.modfile} and {args.obsfile}')
        write_quick(args.modfile, args.obsfile,
                  args.mparfile, args.wparfile, args.outdir,
                  args.no_cols, args.residuals)

    else:
        error_exit("This message shouldn't appear so it is time to cry")

if __name__ == '__main__':
    main()



