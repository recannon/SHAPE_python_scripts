#Last modified 03/05/2025

from pyshape import obs_file
import argparse
from pathlib import Path
import glob

def change_weights(fname,obs_type,new_weights,sets_affected=[]):

    #Load obs file
    set_list = obs_file.read(fname)

    change_type = {'dd' : 'delay-doppler',
                   'lc' : 'lightcurve',
                   'cw' : 'doppler'}
    obs_type = change_type[obs_type]
   
    if sets_affected == []:
        sets_affected = list(range(len(set_list)))

    #change weights
    for obs_set in set_list:
        #Check type and sets to affect
        if obs_set.type == obs_type and obs_set.setno in sets_affected:
            obs_set.change_weights(new_weights)
        else:
            continue

    #Save file
    obs_file.write(fname,set_list)
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
        print(f'Changing {args.fname}')
        change_weights(*vars(args).values())
    elif Path(args.fname).is_dir():
        print('Directory of files')
        obsfiles = glob.glob(f'{args.fname}/*.obs')
        for obs in obsfiles:
            print(f'Changing {obs}')
            change_weights(obs,args.obs_type,args.new_weights,args.components)
    else:
        raise FileNotFoundError('Cannot find file or directory with name [fname]')

if __name__ == "__main__":
    main()

