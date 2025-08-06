#Last modified 16/05/2025
#python /path/to/write_fit.py modfile obsfile
#python /path/to/write_fit.py lat lon (if pole scan, give values as strings, e.g +40 060. Files expected in mod/obsfiles) 
#python /path/to/write_fit.py --all (runs fit for all files in namecores, looking in modfiles/obsfiles) 

from pyshape.outfmt import logger, error_exit
from pyshape.utils import check_type
import subprocess
from pyshape import obs_file, plot_quick
import argparse
from pathlib import Path
import logging

def write_fit(modfile,obsfile,mparfile='par/mpar',wparfile='par/wpar',outdir='.',no_cols=3,res=False):
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

    current_path   = Path.cwd()
    waction_path   = current_path / 'waction'
    temp_path      = current_path / 'waction/temp'
    
    #Identifier to call pdf
    identifier = f'{modfile.stem}__{obsfile.stem}' if modfile.stem != obsfile.stem else modfile.stem
    
    #Changes filepaths to absolute paths. Needed as shape functions are run from ./waction, not ./
    modfile,obsfile = Path(modfile).resolve(),Path(obsfile).resolve()
    mparfile,wparfile = Path(mparfile).resolve(),Path(wparfile).resolve()

    #Makes sure both waction and waction/temp exist. Creates if not
    temp_path.mkdir(parents=True, exist_ok=True)

    #Empty waction folder without trying to remove directories
    subprocess.run('find waction/temp -maxdepth 1 -type f -exec rm {} +', shell=True, check=True)

    #Run moments with shape
    logger.info('Running moments')
    logger.debug(f'shape {mparfile} {modfile} {obsfile}')
    with open(f'waction/{identifier}.mpar.log', 'w') as log:
        try:
            subprocess.run(["shape", str(mparfile), str(modfile), str(obsfile)], cwd=temp_path, stdout=log, check=True)
        except subprocess.CalledProcessError:
            error_exit(f'Problem running moments action. Check {log.name}')

    #Run write with shape
    logger.info('Running write')
    logger.debug(f"shape {wparfile} {modfile} {obsfile}")
    with open(waction_path / f'{identifier}.wpar.log', 'w') as log:
        try:
            subprocess.run(["shape", str(wparfile), str(modfile), str(obsfile)], cwd=temp_path, stdout=log, check=True)
        except subprocess.CalledProcessError:
            error_exit(f'Problem running write action. Check {log.name}')

    #Collage mpar figures
    logger.info('Creating jpgs')
    pos_files = sorted((temp_path).glob("*pos.ppm"))
    neg_files = sorted((temp_path).glob("*neg.ppm"))
    with open(temp_path / 'mpar_stack.sh','w') as f:
        f.write(f'ppmstack 3 1 1 {" ".join(map(str, pos_files))} {" ".join(map(str, neg_files))} mpar.ppm\n')
        f.write(f'ffmpeg -loglevel error -hide_banner -i {current_path}/waction/temp/mpar.ppm {current_path}/waction/temp/1_mpar.jpg')
    with open(waction_path / 'mpar_stack.log', 'w') as log:
        subprocess.run(["bash", temp_path / "mpar_stack.sh"], cwd=temp_path, stdout=log, check=True)

    #Read obsfile to check for which data types are present
    obs_sets  = obs_file.read(obsfile)
    set_types = set(obs_set.type for obs_set in obs_sets) 
       
    #delay-Doppler requires stacking of pgm images
    if 'delay-doppler' in set_types:
        
        obs_frames = sorted((temp_path).glob("obs_*.pgm"))
        fit_frames = sorted((temp_path).glob("fit_*.pgm"))
        res_frames = sorted((temp_path).glob("res_*.pgm"))
        sky_frames = [str(name).replace('obs_', 'sky_').replace('.pgm', '.ppm') for name in obs_frames]        
        temp_frames = [str(name).replace('sky_','temp_') for name in sky_frames]
        no_frames  = len(temp_frames)
        no_rows    = no_frames//no_cols + int(no_frames % no_cols != 0)

        with open(temp_path / 'dd_stack.sh','w') as f:
            
            for i in range(len(temp_frames)):
                parts = [obs_frames[i], fit_frames[i]]
                if res:
                    parts.append(res_frames[i])
                parts.append(sky_frames[i])
                parts.append(temp_frames[i])
                f.write(f'ppmstack {len(parts)-1} 1 1 {" ".join(map(str, parts[:-1]))} {str(parts[-1])}\n')
                
            #Stack columns
            column_files = [Path(temp_frames[0]).parent / f'temp_{i:02}.ppm' for i in range(no_cols)]            
            for i in range(no_cols):
                f.write(f'ppmstack 1 1 1 {" ".join(map(str, temp_frames[i*no_rows:(i+1)*no_rows]))} {column_files[i]}\n')

            #Group columns together
            f.write(f'ppmstack {no_cols} 1 1 {" ".join(map(str, column_files))} {current_path}/waction/temp/dd_fits.ppm\n')
            f.write(f'ffmpeg -loglevel error -hide_banner -i {current_path}/waction/temp/dd_fits.ppm {current_path}/waction/temp/2_dd_fits.jpg\n')

        subprocess.run(f'bash {current_path}/waction/temp/dd_stack.sh > dd_stack.log',shell=True,check=True,cwd='waction')

    #lc and cw can be plotted with functions
    if 'lightcurve' in set_types:
        lc_fits = sorted(temp_path.glob("fit_??.dat"))
        #Create lightcurve plot
        plot_quick.pq_lightcurves(lc_fits, show=False, save=temp_path / '3_lc_fits.jpg')

    if 'doppler' in set_types:
        cw_fits = sorted(temp_path.glob("fit_??_??.dat"))
        #Create plot
        plot_quick.pq_doppler(cw_fits, show=False, save=temp_path / '4_cw_fits.jpg')

    #Stack jpg files into a pdf
    jpg_files = sorted(temp_path.glob("*.jpg"))
    output_name = outdir / f"{identifier}.pdf"
    script_dir = Path(__file__).resolve().parent
    subprocess.run(["bash", script_dir / "bash_scripts/create_pdf.sh", output_name, *map(str, jpg_files)], check=True)
    
    #Empty waction folder without trying to remove directories
    subprocess.run('find waction/temp -maxdepth 1 -type f -exec rm {} +', shell=True, check=True)

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
    optional_group.add_argument("-m", "--mparfile", type=Path, default='./par/mpar',
                        help="mpar file to use. Default cwd/par/mpar")
    optional_group.add_argument("-w", "--wparfile", type=Path, default='./par/wpar',
                        help="wpar file to use. Default cwd/par/wpar")
    optional_group.add_argument("-o",'--outdir', type=Path, default='.',
                        help="Directory to save fits. Default cwd")
    optional_group.add_argument("-r", "--residuals", action="store_true",
                        help="Include residuals in dd fit")
    optional_group.add_argument("-n", "--no-cols", default=3,
                        help="Number of columns for dd fit. Default is 3")
    
    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #Check optional inputs
    args.no_cols = check_type(args.no_cols,'--no-cols',int)
    if not args.mparfile.is_file():
        error_exit(f'Cannot find given mparfile: {args.mparfile}')
    if not args.wparfile.is_file():
        error_exit(f'Cannot find given wparfile: {args.wparfile}')
    if not args.outdir.is_dir():
        error_exit(f'Cannot find given output directory: {args.outdir}')

    #If all, don't check modfile/obsfile
    if args.all:
        if not Path('./namecores.txt').is_file():
            error_exit('Used --all but cannot find ./namecores.txt')
        if args.modfile or args.obsfile:
            logger.warning('Found modefile or obsfile provided with --all. Ignoring provided files')

    elif not args.modfile and not args.obsfile:
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
            write_fit(modfile, obsfile,
                      args.mparfile, args.wparfile, args.outdir,
                      args.no_cols, args.residuals)

    elif args.modfile and args.obsfile:
        
        logger.info(f"Processing: {args.modfile} and {args.obsfile}")
        write_fit(args.modfile, args.obsfile,
                  args.mparfile, args.wparfile, args.outdir,
                  args.no_cols, args.residuals)

    else:
        error_exit("This message shouldn't appear so it is time to cry")

if __name__ == "__main__":
    main()



