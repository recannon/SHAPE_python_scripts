#Last modified by @recannon on 11/01/2026

import argparse
import logging
from pathlib import Path
import subprocess
from pyshape.obs.obs_io import obsFile
from pyshape.cli_config import logger, error_exit
import pyshape.plotting.pub_routines as pp
from pyshape.utils import check_file, check_dir, empty_dir, run_shape
from pyshape.jinja_env import render_and_compile_pdf
from pyshape.mod.mod_io import modFile
from pyshape.plotting import artificial_lightcurves
from dataclasses import dataclass

def write_pub(modfile,outdir,
              model_args,cw_args,lc_args):
    
    #Setting up paths
    current_path = Path.cwd()
    waction_path = current_path / 'waction'
    temp_path    = waction_path / 'temp'
    pub_path     = waction_path / 'pub'
    #Makes sure waction/temp and waction/pub exist (and by extension waction)
    temp_path.mkdir(parents=True, exist_ok=True)
    pub_path.mkdir(parents=True, exist_ok=True)
    modfile = Path(modfile).resolve()

    #Identifier for output pdfs
    if cw_args:
        obsfile = Path(cw_args.obsfile).resolve()
        wparfile = Path(cw_args.wparfile).resolve()
        identifier = f'{modfile.stem}__{obsfile.stem}' if modfile.stem != obsfile.stem else modfile.stem
    else:
        identifier = f'{modfile.stem}'

    #Only doppler call requires a write action
    if cw_args:
        
        obs_file = obsFile.from_file(obsfile)
        obs_sets = obs_file.datasets
        cw_sets = [o for o in obs_sets if o.set_type == 'doppler']
        if not cw_sets: #If there aren't any
            logger.warning('Skipping CWs, none found in obsfile')
        else:
            #Empty waction and pub folders (not recursively)
            empty_dir(temp_path)
            empty_dir(pub_path)
            #Run write action for data files
            run_shape([wparfile, modfile, obsfile],
                    run_dir=temp_path, out_log=waction_path / f'{identifier}.wpar.log')
            
            cw_list = []
            for cw in cw_sets:
                setno = cw.set_no
                dop_info = cw.dop_info

                for frameno, frame in enumerate(cw.frames):
                    #Files (hopefully) created by write
                    fit = temp_path / f"fit_{setno:02d}_{frameno:02d}.dat"
                    ppm = temp_path / f"sky_{setno:02d}_{frameno:02d}.ppm"
                    if not fit.exists():
                        raise FileNotFoundError(f"Missing {fit}")
                    if not ppm.exists():
                        raise FileNotFoundError(f"Missing {ppm}")

                    fig_title = fr"{len(cw_list)+1:d} $\bullet$ {frame.date.isot.split('T')[0]} $\bullet$ {frame.date.jd:.3f}"

                    logger.info(f"Plotting {fit.name}")
                    fit_pdf = pub_path / f"CW_fit_{setno:02d}_{frameno:02d}.pdf"
                    pos_pdf = pub_path / f"CW_pos_{setno:02d}_{frameno:02d}.pdf"
                    pp.pub_doppler(fit, dop_info, fig_title, save=fit_pdf)
                    subprocess.run(["convert", ppm, pos_pdf], check=True)

                    cw_list.append({
                        "setno": setno,
                        "frameno": frameno,
                        "cw_pdf": fit_pdf,
                        "pos_pdf": pos_pdf,
                    })

            out_stem = f'PubCW_{identifier}'
            render_and_compile_pdf("pub_cw_plots.tex.j2", {"cw_list": cw_list},
                                out_stem, pub_path, outdir)
        
    #Both model and lc_toggle require reading of the modfile, do this together
    if lc_args or model_args:
        
        mod_info = modFile.from_file(modfile)
        mod_vx = mod_info.components[0]
        V,F,FN,FNa = mod_vx.vertices, mod_vx.facets, mod_vx.FN, mod_vx.FNa
        
        if lc_args:
            #Assume there is only one optical scattering law
            #Though test for if it exists (More likely to have 0 than 2+)
            try:
                mod_ol = mod_info.phot_functions.optical[0]
            except (KeyError, IndexError):
                raise RuntimeError("No optical scattering law found in mod file")
            scattering_law = mod_ol.type
            scattering_params = mod_ol.values_to_dict()
            mod_ss = mod_info.spinstate
            t0,P = mod_ss.t0.jd, mod_ss.P
            lam,bet,phi = mod_ss.lam, mod_ss.bet, mod_ss.phi+90

            #Create plots and output results dictionary (not done)
            artificial_lightcurves.pub_lightcurve_generator(pub_path, lc_args.lc_file,
                                                            t0, lam, bet, phi, P,
                                                            FN, FNa, V=V, F=F,
                                                            scattering_law=scattering_law,
                                                            scattering_params=scattering_params,
                                                            shadowing=True,
                                                            plot=True, show_plot=False)

            #Combine the figures
            out_stem = f'PubLC_{identifier}'
            artificial_lightcurves.concat_lc_plots(pub_path,outdir,out_stem)        
    
        if model_args:
        
            red_facets = set()
            yellow_facets = set()

            if model_args.redfile:
                with open(model_args.redfile) as f:
                    red_facets = {int(d) for d in f}

            if model_args.yellowfile:
                with open(model_args.yellowfile) as f:
                    yellow_facets = {int(d) for d in f}
                    
            ticks= model_args.ticks
            lims = model_args.lims
            
            out_stem = f'{outdir}/PubModel_{identifier}'
            pp.pub_model(V,F,FN,
                        red_list=red_facets,yellow_list=yellow_facets,
                        lims=lims,ticks=ticks,out_stem=out_stem)

    return True

#===Functions for parsing below this point===

@dataclass
class CWArgs:
    obsfile: Path
    wparfile: Path
@dataclass  
class LCArgs:
    lc_file: Path
@dataclass
class ModelArgs:
    redfile: Path
    yellowfile: Path
    ticks: float
    lims: float


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Creates publication pdfs for each toggled plot type",
                                     epilog='Saves pdfs as {outdir}/Pub{pubtype}_{identifier}.pdf')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    io_group = parser.add_argument_group('IO inputs')    
    io_group.add_argument("modfile", type=str, help="modfile (compulsory)")
    io_group.add_argument("-o",'--outdir', type=str, default='./PubPlots',
                          help="Directory of pdfs saved. Default ./PubPlots")

    cw_group = parser.add_argument_group('CW plots (-cw)')
    cw_group.add_argument("-cw", action="store_true", help="Plot CW data")
    cw_group.add_argument("--obsfile", type=str, help="obsfile (compulsory)")
    cw_group.add_argument("--wparfile", type=Path, default='./par/wpar',
                          help="wpar file to use. Default cwd/par/wpar")

    lc_group = parser.add_argument_group('Lightcurve plots (-lc)')
    lc_group.add_argument("-lc", action="store_true", help="Plot lightcurve data")
    lc_group.add_argument("--lcfile", type=Path, default=None,
                          help="Lightcurve data file (compulsory)")

    mp_group = parser.add_argument_group('Model projection plots (-mp)')
    mp_group.add_argument("-mp", action="store_true", help="Plot model projections")
    mp_group.add_argument("--redfile", type=Path, default=None,
                          help="File listing facets to be coloured red")
    mp_group.add_argument("--yellowfile", type=Path, default=None,
                          help="File listing facets to be coloured yellow")
    mp_group.add_argument("--ticks", type=float, default=0.3,
                          help="Symmetric location of axis ticks and grid lines")
    mp_group.add_argument("--lims", type=float, default=0.45,
                          help="Symmetric location of axis limits")

    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    if not args.lc and not args.cw and not args.mp:
        error_exit('Must specify which plots to be created')
    else:
        args.modfile = check_file(args.modfile)
    
    #CW checks
    if args.cw:
        if not args.obsfile:
            error_exit('Must provide obsfile when using -cw')
        args.obsfile = check_file(args.obsfile)
        args.wparfile = check_file(args.wparfile)
        args.cw_args = CWArgs(obsfile=args.obsfile, wparfile=args.wparfile)
    else:
        args.cw_args = None

    #LC checks
    if args.lc:
        if not args.lcfile:
            error_exit('Must provide lcfile when using -lc')
        args.lcfile = check_file(args.lcfile)
        args.lc_args = LCArgs(lc_file=args.lcfile)
    else:
        args.lc_args = None

    #Model checks
    if args.mp:
        if args.redfile:
            args.redfile = check_file(args.redfile)
        if args.yellowfile:
            args.yellowfile = check_file(args.yellowfile)
        args.model_args = ModelArgs(redfile=args.redfile, yellowfile=args.yellowfile,
                                    ticks=args.ticks, lims=args.lims)
    else:
        args.model_args = None
    
    #Create output directory if doesn't exist.
    args.outdir = check_dir(args.outdir,create=True)
    
    return args

def main():
    args = parse_args()
    args = validate_args(args)    
    
    logger.info(f"Processing: {args.modfile}")
    write_pub(args.modfile, args.outdir,
              args.model_args,args.cw_args,args.lc_args)

if __name__ == "__main__":
    main()



