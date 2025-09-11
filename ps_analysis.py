from pyshape.outfmt import logger,error_exit
from pyshape.utils import check_type, check_dir
from pyshape import polescan, plot_quick
import argparse
import logging
from pathlib import Path
import numpy as np
import cmasher as cmr

#Code for combining and/or plotting polescan results into a jpg file. E.g.
#python -m ps_analysis --combine --subscan
#python -m ps_analysis --plot [--fig-name FIGNAME] [--max-level MAXLVL] [--lines L1 L2 L3]
#python -m ps_analysis --combine --dirs DIR1 DIR2 [DIR3...] --out-dir OUTDIR

def plot_polescan(dirname,fig_name,maxlevel,lines):
    logger.debug(f'Scanning files in {dirname}')
    bet,lam,chi,_,_ = polescan.results(dirname)

    bet,lam = bet[~np.isnan(chi)],lam[~np.isnan(chi)]
    chi = chi[~np.isnan(chi)]
    
    #Plot
    plot_quick.pq_polescan(bet,lam,chi,
                        maxlevel=maxlevel, lines=lines,
                        cmp='cmr.sunburst',show=False,save=fig_name)
    return True


def combine_polescan(ps_dirs,out_dir,plot=False,plot_args=None):
    
    logger.debug(f'Combining polescans from {ps_dirs}')

    bet,lam,chi,loc = polescan.combine(ps_dirs,out_dir)

    if plot:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.hist(loc)
        plt.savefig('test.png')
        
    return True
    
    
#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Plot or combine polescans (or both)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Plot args
    plot_group = parser.add_argument_group('Arguments for creating a polescan plot')
    plot_group.add_argument('-p','--plot', action='store_true',
                            help='Will look for other plotting arguemnts')
    plot_group.add_argument('--dirname', type=str,
                            help='Directory of logfiles of the polescan. Defaults to cwd')
    plot_group.add_argument('--fig-name', type=str,
                            help="Specify name of output jpg file. Defaults to polescan.jpg")
    plot_group.add_argument('--max-level', type=str,
                            help='Multiple of minimum chisqr that appears coloured on plot. Default 1.1')
    plot_group.add_argument('--lines', nargs='*', type=float, default=None,
                            help='Additional contours to plot as percentages above minimum chi-sqr. e.g., --lines 1 2.5 5')
    
    #Combine args
    combine_group = parser.add_argument_group('Arguments for combining multiple polescans. To plot combined scan, call --plot as well')
    combine_group.add_argument('-c','--combine',action='store_true',
                               help = 'Will look for other combine arguments')
    combine_group.add_argument('--subscan',action='store_true',
                               help='If toggled will combine all polescans in ./subscans into ./')
    combine_group.add_argument('--dirs',nargs='+',default=None,
                               help='List of paths to polescans to be combined. Not required if using --subscans')
    combine_group.add_argument('--out-dir',type=str,
                               help='Out directory to save combined results. Not required if using --subscans or also calling --plot')
    
    return parser.parse_args()


def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #Check combine mode
    if args.combine:
        needs_output = not args.plot and not (args.out_dir or args.subscan)
        if needs_output:
            error_exit('Provide either plot (and plotting args) or out_dir/subscan when combining polescans')

        if args.subscan:
            if args.dirs:
                error_exit('Cannot combine subscans with other polescans. Do this separately')            
            args.dirs    = sorted(list(Path.cwd().joinpath("subscans").glob("*")))
            if not args.out_dir:
                args.out_dir = Path.cwd()
            else:
                args.out_dir = check_dir(args.out_dir)
        
        elif args.dirs:
            args.dirs = [check_dir(dir) for dir in args.dirs]
            if not args.out_dir:
                error_exit('Must provide --out-dir if not using --subscan')    
            args.out_dir = check_dir(args.out_dir)
            
        else:
            error_exit('Must provide either --subscan or a list of --dirs')     

    #Check if we are in plot mode
    if args.plot:
        
        #Check directory exists and has files in
        if not args.dirname:
            args.dirname = '.'
        args.dirname = check_dir(args.dirname)
        no_files = len([f for f in args.dirname.iterdir() if f.is_file()])
        if no_files == 0:
            error_exit(f'Directory {args.dirname} has no files in')

        if not args.fig_name:
            args.fig_name = './polescan.jpg'

        #Maxlevel
        if not args.max_level:
            args.max_level = 1.1
        args.max_level = check_type(args.max_level,'--max-level',float) 
        #Lines
        if args.lines == []:
            args.lines = [1.0, 2.5, 5.0]

    return args


#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    if args.plot:
        plot_polescan(args.dirname,args.fig_name,args.max_level,args.lines)

    if args.combine:
        combine_polescan(args.dirs,args.out_dir,args.plot,[args.fig_name,args.max_level,args.lines])


if __name__ == "__main__":
    main()

