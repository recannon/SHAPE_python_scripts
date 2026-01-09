#Last modified by @recannon on 09/01/2026

import argparse
import logging
from pathlib import Path
import subprocess
from pyshape.obs import obs_io
from pyshape.io_utils import logger, error_exit, check_type
import pyshape.plotting.pub_routines as pp
from pyshape.utils import time_shape2astropy

def write_pub(modfile,obsfile,wparfile='par/wpar',outdir='test.pdf'):

    current_path = Path.cwd()
    waction_path = current_path / 'waction'
    temp_path    = waction_path / 'temp'
    pub_path     = waction_path / 'pub'
    
    #Identifier for shape logs
    identifier = f'{modfile.stem}__{obsfile.stem}' if modfile.stem != obsfile.stem else modfile.stem
    
    #Changes filepaths to absolute paths. Needed as shape functions are run from ./waction, not ./
    modfile,obsfile = Path(modfile).resolve(),Path(obsfile).resolve()
    wparfile = Path(wparfile).resolve()

    #Makes sure waction/temp and waction/pub exist (and by extension waction)
    temp_path.mkdir(parents=True, exist_ok=True)
    pub_path.mkdir(parents=True, exist_ok=True)

    #Empty waction and pub folders without trying to remove directories
    subprocess.run('find waction/temp -maxdepth 1 -type f -exec rm {} +', shell=True, check=True)
    subprocess.run('find waction/pub -maxdepth 1 -type f -exec rm {} +', shell=True, check=True)

    #Run write with shape (doesn't require moments)
    logger.info('Running write')
    logger.debug(f"shape {wparfile} {modfile} {obsfile}")
    with open(waction_path / f'{identifier}.wpar.log', 'w') as log:
        try:
            subprocess.run(["shape", str(wparfile), str(modfile), str(obsfile)], cwd=temp_path, stdout=log, check=True)
        except subprocess.CalledProcessError:
            error_exit(f'Problem running write action. Check {log.name}')

    #Collage mpar figures
    logger.info('Creating pdfs')
    
    #Read obsfile to check for which data types are present
    obs_sets  = obs_io.read(obsfile)
    set_types = set(obs_set.type for obs_set in obs_sets) 
    
    if 'doppler' in set_types:
        
        cw_sets = [o for o in obs_sets if o.type=='doppler']
        cw_fits = sorted(temp_path.glob("fit_??_??.dat"))
        
        for i, cw in enumerate(cw_fits):
            
            entry_line = cw_sets[i].lines[-3]
            print(entry_line)
            date = " ".join(entry_line.split()[1:7])
            cw_start = time_shape2astropy(date)
            
            start_jd   = cw_start.jd
            start_date = cw_start.isot.split('T')[0]
            
            fig_title = f'{i+1} $\\bullet$ {start_date} $\\bullet {start_jd:.3f}$ '
            
            #Create plot
            pp.pub_doppler(cw,fig_title,save=pub_path/f'CW_{i+1}.pdf')

    # #Stack jpg files into a pdf
    # jpg_files = sorted(temp_path.glob("*.jpg"))
    # output_name = outdir / f"{identifier}.pdf"
    # script_dir = Path(__file__).resolve().parent
    # subprocess.run(["bash", script_dir / "bash_scripts/create_pdf.sh", output_name, *map(str, jpg_files)], check=True)
    
    # #Empty waction folder without trying to remove directories
    # subprocess.run('find waction/temp -maxdepth 1 -type f -exec rm {} +', shell=True, check=True)

    return True

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Calls shape moment/write action and saves results as PDFs.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    input_group = parser.add_argument_group('Compulsory input files')    
    input_group.add_argument("modfile", type=str, nargs='?', help="modfile to write.")
    input_group.add_argument("obsfile", type=str, nargs='?', help="obsfile to write.")
    input_group.add_argument("--all", action="store_true",
                        help="Run write_fit for all files in namecores.txt")
    
    optional_group = parser.add_argument_group('Optional input parameters')
    optional_group.add_argument("-w", "--wparfile", type=Path, default='./par/wpar',
                        help="wpar file to use. Default cwd/par/wpar")
    optional_group.add_argument("-o",'--outdir', type=Path, default='.',
                        help="Directory to save fits. Default cwd")

    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #Check optional inputs
    if not args.wparfile.is_file():
        error_exit(f'Cannot find given wparfile: {args.wparfile}')
    if not args.outdir.is_dir():
        args.outdir.mkdir()
        logger.debug(f'Created output directory {args.outdir}')
        # error_exit(f'Cannot find given output directory: {args.outdir}')

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
        if not args.modfile.is_file():
            error_exit(f'Cannot find given modfile: {args.modfile}')
        if not args.obsfile.is_file():
            error_exit(f'Cannot find given obsfile: {args.obsfile}')
    
    return args

def main():
    args = parse_args()
    args = validate_args(args)    
    
    if args.all:
        logger.info("Running in --all mode. Processing all files from namecores.txt")
        with open('./namecores.txt') as f:
            namecores = [line.strip() for line in f if line.strip()]

        for namecore in namecores:
            modfile = Path("modfiles") / f"{namecore}.mod"
            obsfile = Path("obsfiles") / f"{namecore}.obs"
            
            if not modfile.is_file():
                logger.warning(f'Cannot find {modfile}. Skipping')
                continue
            if not obsfile.is_file():
                logger.warning(f'Cannot find {obsfile}. Skipping')
            
            logger.info(f"Processing: {modfile} and {obsfile}")
            write_pub(modfile, obsfile,
                      args.wparfile, args.outdir,)

    elif args.modfile and args.obsfile:
        
        logger.info(f"Processing: {args.modfile} and {args.obsfile}")
        write_pub(args.modfile, args.obsfile,
                  args.wparfile, args.outdir)

    else:
        error_exit("This message shouldn't appear so it is time to cry")

if __name__ == "__main__":
    main()



