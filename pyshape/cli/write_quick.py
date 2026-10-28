#Last modified by @recannon on 07/10/2026

#07/10/2026 - Moved all moments processing out of this script into moments.py
#15/09/2026 - Subfunctions from utils for moments and dd routines
#01/06/2026

import argparse
import logging
from pathlib import Path
import subprocess
from .config import logger, error_exit
from .. import utils
from .. import shape
# from ..shape.moments import run_and_compile_moments 
# from ..shape.write import run_and_compile_write

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
    shape.run_and_compile_moments(mparfile, modfile, None, mpar_logfile=maction_log, figfile=temp_path/'1_mpar.jpg')

    #Runs write and compiles results into jpgs
    #The numbers of the jpg names determines the order that they are compiled into a pdf
    shape.run_and_compile_write(wparfile, modfile, obsfile, wpar_logfile=waction_log,
                                dd_no_cols=no_cols, dd_res=res,
                                dd_figfile=temp_path/'2_dd_fits.jpg', cw_figfile=temp_path/'4_cw_fits.jpg', lc_figfile=temp_path/'3_lc_fits.jpg')

    # from PIL import Image

    # width = 842
    # resized = []
    # for jpg in sorted(temp_path.glob('*.jpg')):
    #     with Image.open(jpg) as im:
    #         im = im.convert('RGB')
    #         new_height = round(im.height * width / im.width)
    #         resized.append(im.resize((width, new_height), Image.Resampling.LANCZOS))

    # canvas = Image.new('RGB', (width, sum(im.height for im in resized)), 'white')
    # y = 0
    # for im in resized:
    #     canvas.paste(im, (0, y))
    #     y += im.height
    # output_name = outdir / f'{identifier}.pdf'
    # canvas.save(output_name, 'PDF', resolution=72.0)
    # logger.info(f'Created PDF: {output_name}')

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



