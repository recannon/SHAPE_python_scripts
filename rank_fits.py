from pyshape.outfmt import logger, error_exit
from pyshape.utils import check_type
from pyshape import log_file
from pathlib import Path
import argparse
import logging

#python -m rank_fits
#python -m rank_fits --dirname not_logfiles --top 10 --chi-type Doppler
#chi-type must be one of ['ALLDATA','Doppler','delay','lghtcrv']

def rank_fits(dirname:Path, top:int = 5, chi_type:str = 'ALLDATA'):
    
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

    top_lines = [f"| {chi:.3f} : {log.name}" for chi, log in results[:top]]
    logger.info(f"Top {top} files by chisqr ({chi_type}):\n" + "\n".join(top_lines))
    
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
    else:
        args.top = check_type(args.top,'--top',int)
        if args.top > no_files:
            logger.info(f'Only {no_files} files in {args.dirname}. Showing all files')    

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    rank_fits(args.dirname,args.top,args.chi_type)


if __name__ == "__main__":
    main()

