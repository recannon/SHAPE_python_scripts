#Last modified 12/09/2025

from ..io_utils import logger, error_exit, safe_exit, check_type
from .. import log_file
from pathlib import Path
import argparse
import logging

#python -m rank_fits
#python -m rank_fits --dirname not_logfiles --top 10 --chi-type Doppler
#chi-type must be one of ['ALLDATA','Doppler','delay','lghtcrv']

def rank(dirname:Path, top:int = 5, chi_type:str = 'ALLDATA', percent:bool = False, delete:bool = False):
    
    log_files = sorted(dirname.glob('*'))

    results = []
    for log in log_files:
        try:
            chi_val = log_file.read(log)[chi_type]
            results.append((chi_val, log))
        except KeyError:
            logger.warning(f"Chi type '{chi_type}' not found in {log}")
        except Exception as e:
            logger.warning(f"Error reading {log}: {e}")
    results.sort()

    if not percent:
        top_lines = [f"| {chi:.3f} : {log.name}" for chi, log in results[:top]]
        logger.info(f"Top {top} files by chisqr ({chi_type}):\n" + "\n".join(top_lines))
    elif percent:
        chi_cut = results[0][0] * (1 + top/100)
        top_lines = [f"| {chi:.3f} : {log.name}" for chi, log in results if chi < chi_cut]
        logger.info(f"Files within {top}% of minimum ({chi_type}):\n" + "\n".join(top_lines))

    else:
        error_exit("This error shouldn't appear so it is time to cry")
    
    if delete:
        
        namecores_path = Path("./namecores.txt")
        try:
            with namecores_path.open("w") as f:
                for line in top_lines:
                    log = Path(line.split()[-1])
                    f.write(log.stem + "\n")
            logger.info(f"Rewrote {namecores_path} with {len(top_lines)} entries")
        except Exception as e:
            logger.warning(f"Could not rewrite {namecores_path}: {e}")
        
        #Deleting files
        if not percent:
            not_selected = results[top:]
        elif percent:
            not_selected = [(chi, log) for chi, log in results if chi >= chi_cut]
        
        for _,log in not_selected:
            shape_files = [
                log, 
                Path(str(log).replace("log", "obs")),
                Path(str(log).replace("log", "mod")),
            ]
            for f in shape_files:
                try:
                    f.unlink()
                    logger.debug(f"Deleted {f}")
                except Exception as e:
                    logger.warning(f"Could not delete {f}: {e}")

    return True
    
#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Rank a directory of logfiles based on specified chisqr value")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Beta and lambda ranges and steps
    parser.add_argument("--dirname", type=str, help="Name of directory of logfiles. Default ./logfiles")
    parser.add_argument("--top",     type=str, help="How many log files to show from first place. Default: 5")
    parser.add_argument("--chi-type",type=str, help="Type of chisqr to rank by. Default: ALLDATA")
    parser.add_argument("--delete", action="store_true",
                        help="Will delete any files not with the selection specified")
    parser.add_argument("--percent", action="store_true",
                        help="If toggled, will select the files within {--top} percent of the best fit")

    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #Check directory exists and number of files
    if not args.dirname:
        args.dirname = './logfiles'
    args.dirname = Path(args.dirname)
    if not args.dirname.is_dir():
        error_exit(f'Directory {args.dirname} does not exist')
    no_files = len([f for f in args.dirname.iterdir() if f.is_file()])
    if no_files == 0:
        error_exit(f'Directory {args.dirname} has no files in')

    #Type of chisquared to rank it
    ALLOWED_CHI_TYPES = ['ALLDATA','Doppler','delay','lghtcrv']
    if not args.chi_type:
        args.chi_type = 'ALLDATA'
    elif args.chi_type not in ALLOWED_CHI_TYPES:
        error_exit(f'Chi-type must be one of: {" ".join(ALLOWED_CHI_TYPES)}')

    #Number of top files to show
    if not args.top:        
        args.top = 5
    elif args.top == 0:
        error_exit('Cannot show the top 0 files')
    elif args.top == -1:
        args.top = no_files
    elif not args.percent:
        args.top = check_type(args.top,'--top',int)
    elif args.percent:
        args.top = check_type(args.top,'--top',float)
        logger.info(f'Selecting log files within {args.top}% of the best fit.')

    if args.top > no_files:
        logger.info(f'Only {no_files} files in {args.dirname}. Showing all files')    

    #Check for delete
    if args.delete:
        del_check = input('Are you sure you want to delete files? (y/N)')
        if del_check.lower() != 'y':
            safe_exit()

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    rank(args.dirname,args.top,args.chi_type,args.percent,args.delete)


if __name__ == "__main__":
    main()

