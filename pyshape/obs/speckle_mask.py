#Last modified by @recannon 27/08/2026

#27/08/2026 - More Documentation
#13/07/2026 - Creation

#Only works for delay-Doppler
#Edits the mask file of delay-Doppler obsfiles (for selected data sets) to keep the vignetting but scale down below the noise threshold
#Threshold comes from noise limit of 3.66 * np.sqrt(no_looks)

from .obs_io import obsFile
import argparse
from pathlib import Path
import logging
from ..cli.cli_config import logger, error_exit
from ..utils import check_file, check_dir
from astropy.io import fits
import numpy as np

def speckle_mask(fname:Path, sets_affected:list[int], mask_dir:Path):
    
    #Load obs file
    obs_file = obsFile.from_file(fname)
   
    datasets = obs_file.datasets
    
    mask_dir.mkdir(parents=True, exist_ok=True)
    
    if not sets_affected:
        sets_affected = list(range(len(datasets)))

    #change weights
    for obs_set in datasets:

        set_no = obs_set.set_no
        set_type = obs_set.set_type

        #Check set is requested and correct type
        if set_no in sets_affected and set_type == 'delay-doppler':                        
            
            frames = obs_set.frames
            masked = [fr.mask for fr in frames]
            fits_path = check_dir(obs_set.data_dir)
            
            #Loop through frames and their fits files
            for fr_no,frame in enumerate(frames):
                
                fits_name = frame.fname
                no_looks  = frame.looks
                
                #Can only use fits files
                if Path(fits_name).suffix.lower() != '.fits':
                    logger.warning(f'Skipping set {set_no}, frame {fr_no}: {fits_name} is not a .fits file') 
                    continue               
                
                with fits.open(fits_path / fits_name) as hdul:
                    fits_data = hdul[0].data
                fits_shape = np.shape(fits_data)
                # print(fits_data)
                
                mask_file = mask_dir / f'mask_{set_no:0>2}_{fr_no:0>2}.txt'
                logger.info(f'Acting on {mask_file}')
                
                #Create speckle mask
                thresh = 3.66 * np.sqrt(no_looks)
                logger.info(f'Thresh: {thresh}\nMaximum data: {np.abs(fits_data).max()}')
                logger.debug(f'Number of pixels above thresh: {np.sum(fits_data>thresh)}')
                speckle_mask = (thresh / np.maximum(np.abs(fits_data), thresh)) ** 2
                
                if mask_file.is_file():
                    
                    #Read old mask
                    old_mask = np.loadtxt(mask_file)
                    
                    if np.shape(old_mask) != fits_shape:
                        error_exit(f'Mask size discrepency (frame {set_no}:{fr_no})')
                    
                    #Old mask may have been vignetted, which we want to keep
                    vignette_window = old_mask != 0
                    speckle_mask *= vignette_window

                np.savetxt(mask_file,speckle_mask)
                    
                
        elif set_no in sets_affected and obs_set.set_type != 'delay-doppler':
            logger.warning(f'Set number {obs_set.set_no} is not a delay-Doppler set.')
        else:
            continue


    #Save file
    # obs_file.write(fname)
    
    
    return




#===Functions for parsing args below this point===
def parse_args():
    '''Parse command-line arguments.'''
    parser = argparse.ArgumentParser(description='Adjust masking of obsfile data sets to limit signal to speckle noise threshold',
                                     epilog='Recommended that you duplicate your mask directory, as this will work in place')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')

    #Beta and lambda ranges and steps
    parser.add_argument('fname',   type=str, help='Name of file to affect. Cannot be a directory (presumable parallel obsfiles use the same masks)')
    parser.add_argument('maskdir', type=str, help='Directory for Mask files. Masks do not need to previously exist')

    parser.add_argument('-c', '--components', nargs='+', type=int, default=[],
                        help='Optional list of set numbers to affect (rather than all of one type)')

    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')
        
    #Convert to Path and check exists (make dir if not)
    args.fname = check_file(args.fname)
    args.maskdir = check_dir(args.maskdir,must_exist=True,create=True)

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    logger.info(f'Running script on file: {args.fname}')
    speckle_mask(args.fname,args.components,args.maskdir)

if __name__ == '__main__':
    main()