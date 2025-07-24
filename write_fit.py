#Last modified 16/05/2025
#python /path/to/write_fit.py modfile obsfile
#python /path/to/write_fit.py lat lon (if pole scan, give values as strings, e.g +40 060. Files expected in mod/obsfiles) 
#python /path/to/write_fit.py --all (runs fit for all files in namecores, looking in modfiles/obsfiles) 

from pyshape.outfmt import logger, error_exit
import subprocess
from pyshape import obs_file, plot_quick
import numpy as np
import glob
import argparse
from pathlib import Path

def write_fit(modfile,obsfile,mparfile='par/mpar',wparfile='par/wpar',outdir='./',no_cols=3,res=False):
    """
    Run shape model fitting and post-processing.

    This function performs a shape moments and write action on provided files,
    generates figures for the fit, and collates them into a PDF summary report.

    Parameters:
        modfile (str | Path): Path to .mod file
        obsfile (str | Path): Path to .obs file
        mparfile (str | Path): Path to mpar parameter file
        wparfile (str | Path): Path to wpar parameter file
        no_cols (int): Number of columns for delay-doppler stacking
        res (bool): Include residuals in output stacking
    """

    current_path = Path.cwd()
    mod_identifier = Path(modfile).stem
    obs_identifier = Path(obsfile).stem
    identifier = mod_identifier if mod_identifier == obs_identifier else f"{mod_identifier}.{obs_identifier}"

    #Changes filepaths to absolute paths. Needed as shape functions are run from ./waction, not ./
    modfile,obsfile = Path(modfile).resolve(),Path(obsfile).resolve()
    mparfile,wparfile = Path(mparfile).resolve(),Path(wparfile).resolve()

    if not Path('waction/logs').is_dir():
        error_exit('Cannot find ./waction/logs directory')

    #Empty waction and logs folder without trying to remove directories
    subprocess.run('find waction/ -maxdepth 1 -type f -exec rm {} +', shell=True, check=True)

    #Run moments with shape
    logger.info('Running moments')
    logger.debug(f'shape {mparfile} {modfile} {obsfile}')
    with open(f'waction/logs/{identifier}.mpar.log', 'w') as log:
        subprocess.run(["shape", str(mparfile), str(modfile), str(obsfile)], cwd="waction", stdout=log, check=True)

    #Run write with shape
    logger.info('Running write')
    logger.debug(f"shape {wparfile} {modfile} {obsfile}")
    with open(f'waction/logs/{identifier}.wpar.log', 'w') as log:
        subprocess.run(["shape", str(wparfile), str(modfile), str(obsfile)], cwd="waction", stdout=log, check=True)
    
    #Collage mpar figures
    logger.info('Creating jpgs')
    pos_files = sorted(glob.glob(f'{current_path}/waction/*pos.ppm'))
    neg_files = sorted(glob.glob(f'{current_path}/waction/*neg.ppm'))
    with open(f'{current_path}/waction/mpar_stack.sh','w') as f:
        f.write(f'ppmstack 3 1 1 {" ".join(pos_files)} {" ".join(neg_files)} mpar.ppm\n')
        f.write(f'ffmpeg -loglevel error -hide_banner -i {current_path}/waction/mpar.ppm {current_path}/waction/1_mpar.jpg')
    with open('waction/logs/mpar_stack.log', 'w') as log:
        subprocess.run(["bash", f"{current_path}/waction/mpar_stack.sh"], cwd="waction", stdout=log, check=True)

    #Read obsfile to check for which data types are present
    obs_sets  = obs_file.read(obsfile)
    set_types = np.unique([set.type for set in obs_sets])
    
    #Delay-doppler requires stacking of ppm images
    if 'delay-doppler' in set_types:            
        
        obs_frames = sorted(glob.glob(f'{current_path}/waction/obs*.pgm'))
        fit_frames = sorted(glob.glob(f'{current_path}/waction/fit*.pgm'))
        res_frames = sorted(glob.glob(f'{current_path}/waction/res*.pgm'))
        sky_frames = [name.replace('obs_','sky_').replace('.pgm','.ppm') for name in obs_frames]
        temp_frames = [name.replace('sky_','temp_') for name in sky_frames]
        no_frames  = len(temp_frames)
        no_rows    = no_frames//no_cols + int(no_frames % no_cols != 0)

        with open(f'{current_path}/waction/dd_stack.sh','w') as f:
            for i in range(len(temp_frames)):
                parts = [obs_frames[i], fit_frames[i]]
                if res:
                    parts.append(res_frames[i])
                parts.append(sky_frames[i])
                parts.append(temp_frames[i])
                f.write(f'ppmstack {len(parts)-1} 1 1 {" ".join(parts[:-1])} {parts[-1]}\n')

            #Stack columns
            column_files = [f'{temp_frames[0].rsplit("/",1)[0]}/temp_{i:0>2}.ppm' for i in range(no_cols)]
            for i in range(no_cols):
                f.write(f'ppmstack 1 1 1 {" ".join(temp_frames[i*no_rows:(i+1)*no_rows])} {column_files[i]}\n')

            #Group columns together
            f.write(f'ppmstack {no_cols} 1 1 {" ".join(column_files)} {current_path}/waction/dd_fits.ppm\n')        
            f.write(f'ffmpeg -loglevel error -hide_banner -i {current_path}/waction/dd_fits.ppm {current_path}/waction/2_dd_fits.jpg\n')

        subprocess.run(f'bash {current_path}/waction/dd_stack.sh > logs/dd_stack.log',shell=True,check=True,cwd='waction')

    #lc and cw can be plotted with functions
    if 'lightcurve' in set_types:
        lc_fits = sorted(glob.glob('./waction/fit_??.dat'))
        #Create lightcurve plot
        plot_quick.pq_lightcurves(lc_fits,show=False,save='./waction/3_lc_fits.jpg')

    if 'doppler' in set_types:
        cw_fits = sorted(glob.glob('./waction/fit_??_??.dat'))
        #Create plot
        plot_quick.pq_doppler(cw_fits,show=False,save='./waction/4_cw_fits.jpg')

    #Stack jpg files into a pdf
    jpg_files = sorted(glob.glob('./waction/*jpg'))
    output_name = f'{outdir}/{identifier}.pdf'
    script_dir = Path(__file__).resolve().parent
    subprocess.run(["bash", script_dir / "bash_scripts/create_pdf.sh", output_name, *map(str, jpg_files)], check=True)
    return True

def process_file(modfile, obsfile, args):
    """Run write_fit if files exist, otherwise raise an error."""
    modfile = Path(modfile)
    obsfile = Path(obsfile)

    if modfile.is_file() and obsfile.is_file():
        logger.info(f"Processing: {modfile} and {obsfile}")
        write_fit(str(modfile), str(obsfile),
                  args.mparfile, args.wparfile, args.outdir,
                  args.no_cols, args.residuals)
    else:
        error_exit(f"Missing file(s): {modfile if not modfile.is_file() else ''} {obsfile if not obsfile.is_file() else ''}")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Calls shape moment/write action and saves results as PDFs."
    )
    parser.add_argument("modfile", type=str, nargs="?", help="modfile to write.")
    parser.add_argument("obsfile", type=str, nargs="?", help="obsfile to write.")
    parser.add_argument("-m", "--mparfile", type=str, default='./par/mpar',
                        help="mpar file to use.")
    parser.add_argument("-w", "--wparfile", type=str, default='./par/wpar',
                        help="wpar file to use.")
    parser.add_argument("-n", "--no-cols", type=int, default=3,
                        help="Number of columns for dd fit. Default is 3.")
    parser.add_argument("-r", "--residuals", action="store_true",
                            help="Include residuals in dd fit")
    parser.add_argument("--all", action="store_true",
                        help="Run write_fit for all files in namecores.txt")
    parser.add_argument("-o",'--outdir', type=str, default='./',
                        help="Directory to save fits. Default cwd")
    return parser.parse_args()


def main():
    args = parse_args()
    
    if args.all:
        logger.info("Running in --all mode. Processing all mod/obs pairs.")
        try:
            with open('namecores.txt') as f:
                namecores = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error("namecores.txt not found.")
            return

        for namecore in namecores:
            modfile = Path("modfiles") / f"{namecore}.mod"
            obsfile = Path("obsfiles") / f"{namecore}.obs"
            try:
                process_file(modfile, obsfile, args)
            except FileNotFoundError as e:
                logger.warning(e)

    elif args.modfile and args.obsfile:


        try: #Try turn into integers. If your files are integer names it is a bit silly
            lat,lon = int(args.modfile), int(args.obsfile)
            modfile = f"./modfiles/lat{lat}lon{lon}.mod"
            obsfile = f"./obsfiles/lat{lat}lon{lon}.obs"
            logger.info('Super secret polescan mode activated')
        except:
            modfile = args.modfile
            obsfile = args.obsfile
        process_file(modfile, obsfile, args)

    else:
        logger.error("modfile and obsfile are required unless --all is specified.")
        exit(1)

if __name__ == "__main__":
    main()



