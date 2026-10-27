#Last modified by @recannon 27/08/2026

#27/08/2026 - More Documentation

#Used to change the weights of obsfiles. Can be done by component, and in directories.
#python -m change_weights obsfiles cw 1e4 -c 5 6 7 #Sets cw weights for files in obsfiles, only affecting sets 5, 6 and 7
#python -m change_weights obsfiles dd 0.5 #Sets delay-Doppler weights for files in obsfiles
#python -m change_weights test.obs lc 100 #Sets lightcurve weights in test.obs

from .obs_io import obsFile
import argparse
from pathlib import Path
import glob
from ..cli.cli_config import logger

def change_weights(fname,obs_type,new_weights,sets_affected=None):

    #Load obs file
    obs_file = obsFile.from_file(fname)

    change_type = {'dd' : 'delay-doppler',
                   'lc' : 'lightcurve',
                   'cw' : 'doppler'}
    obs_type = change_type[obs_type]
   
    datasets = obs_file.datasets
    
    if not sets_affected:
        sets_affected = list(range(len(datasets)))

    #change weights
    for obs_set in datasets:
        #Check type and sets to affect
        if obs_set.set_type == obs_type and obs_set.set_no in sets_affected:            
            obs_set.set_weights(new_weights)
        else:
            continue


    #Save file
    obs_file.write(fname)
    return 1


def main():
    parser = argparse.ArgumentParser(description="Freeze or unfreeze all variable factors of listed components in a modfile.")

    #Beta and lambda ranges and steps
    parser.add_argument("fname",    type=str, help="Name of file to affect. If directory, will affect all .obs files in directory")
    parser.add_argument("obs_type", type=str, help="Type of dataset expected")
    parser.add_argument("new_weights", type=float, help="New weights for the selected sets. Scientific notation accepted")

    parser.add_argument("-c", "--components", nargs='+', type=int, default=[],
                        help="Optional list of set numbers to affect (rather than all of one type)")

    args = parser.parse_args()

    if Path(args.fname).is_file():
        logger.info(f'Changing {args.fname}')
        change_weights(*vars(args).values())
    elif Path(args.fname).is_dir():
        logger.info(f'Changing directory of files: {args.fname}')
        obsfiles = glob.glob(f'{args.fname}/*.obs')
        for obs in obsfiles:
            logger.debug(f'Changing {obs}')
            change_weights(obs,args.obs_type,args.new_weights,args.components)
    else:
        raise FileNotFoundError('Cannot find file or directory with name [fname]')

if __name__ == "__main__":
    main()

