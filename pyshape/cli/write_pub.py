#Last modified by @recannon 20261110

#20261110 - Include delay-Doppler functionality. 
#           Changed model plotting to calculate colours first rather than whilst plotting
#20260815 - Added .obj reading (for lightcurves)
#20260601

#Used for pretty much everything
import argparse
from dataclasses import dataclass
import logging
from pathlib import Path
import subprocess
from ..io.obs_io import obsFile
from ..utils import check_file, check_dir, empty_dir, run_shape
from .config import logger, error_exit
import tempfile
import numpy as np

#Only used for certain data types, don't load unless required
lazy from ..plotting import lightcurves, doppler, delay_doppler, model
lazy import trimesh #lc and model (as can take obj as file input type)
lazy from ..io.mod_io import modFile #lc and model (if given as shape mod format)
lazy from ..simulation.pub_lightcurve_generator import pub_lightcurve_generator #lc
lazy from ..jinja_env import render_and_compile_pdf #lc and cw


def write_pub(modfile,outdir,
              model_args,cw_args,lc_args,dd_args):
    
    #Setting up paths
    current_path = Path.cwd()
    waction_path = current_path / 'waction'
    pub_path     = waction_path / 'pub'
    #Makes sure waction/temp and waction/pub exist (and by extension waction)
    pub_path.mkdir(parents=True, exist_ok=True)
    modfile = Path(modfile).resolve()

    #Identifier for output pdfs
    if cw_args:
        obsfile = Path(cw_args.obsfile).resolve()
        wparfile = Path(cw_args.wparfile).resolve()
    elif dd_args:
        obsfile = Path(dd_args.obsfile).resolve()
    
    identifier = f'{modfile.stem}'

    #Only doppler and delay-doppler calls requirea write action
    #This is becuase I can't be bothered to simulate the doppler spectrum myself
    if cw_args or dd_args:
        
        with tempfile.TemporaryDirectory() as tmp:
            
            tmp_path = Path(tmp)
            logger.debug('Running write')
            run_shape([wparfile, modfile, obsfile], run_dir=tmp_path, out_log=waction_path / 'write_pub.wpar.log')
            
            obs_file = obsFile.from_file(obsfile)
            obs_sets = obs_file.datasets
            cw_sets = [o for o in obs_sets if o.set_type == 'doppler']
            dd_sets = [o for o in obs_sets if o.set_type == 'delay-doppler']
            
            if not cw_sets and cw_args: #If there aren't any
                logger.warning('Skipping CWs, none found in obsfile')
            elif cw_args:
                cw_list = []
                for cw in cw_sets:
                    setno = cw.set_no
                    dop_info = cw.dop_info

                    for frameno, frame in enumerate(cw.frames):
                        #Files (hopefully) created by write
                        fit = tmp_path / f'fit_{setno:02d}_{frameno:02d}.dat'
                        ppm = tmp_path / f'sky_{setno:02d}_{frameno:02d}.ppm'
                        if not fit.exists():
                            raise FileNotFoundError(f'Missing {fit}')
                        if not ppm.exists():
                            raise FileNotFoundError(f'Missing {ppm}')

                        fig_title = fr'{len(cw_list)+1:d} $\bullet$ {frame.date.isot.split("T")[0]} $\bullet$ {frame.date.jd:.3f}'

                        logger.info(f'Plotting {fit.name}')
                        fit_pdf = pub_path / f'CW_fit_{setno:02d}_{frameno:02d}.pdf'
                        pos_pdf = pub_path / f'CW_pos_{setno:02d}_{frameno:02d}.pdf'
                        doppler.pub_doppler(fit, dop_info, fig_title, save=fit_pdf)
                        subprocess.run(['convert', ppm, pos_pdf], check=True)

                        cw_list.append({
                            'setno': setno,
                            'frameno': frameno,
                            'cw_pdf': fit_pdf,
                            'pos_pdf': pos_pdf,
                        })

                out_stem = f'PubCW_{identifier}'
                render_and_compile_pdf('pub_cw_plots.tex.j2', {'cw_list': cw_list},
                                    out_stem, pub_path, outdir)
                        
            if not dd_sets and dd_args:
                logger.warning('Skipping DDs, none found in obsfile')
            elif dd_args:
                obs_frames = sorted(tmp_path.glob('obs_*.pgm'))
                fit_frames = sorted(tmp_path.glob('fit_*.pgm'))
                res_frames = sorted(tmp_path.glob('res_*.pgm')) if dd_args.res else []
                sky_frames = [f.with_name(f.name.replace('obs_', 'sky_')).with_suffix('.ppm') for f in obs_frames]
                
                max_images_per_page = 3*dd_args.max_rows
                for i in range( (len(obs_frames) // max_images_per_page) + 1):
                    
                    dd_figfile = f'{outdir}/Pub_DD_{i+1:0>2}.jpg'
                    
                    start = i*max_images_per_page
                    end = start+max_images_per_page
                    delay_doppler.format_delay_doppler_images(obs_frames[start:end],fit_frames[start:end],sky_frames[start:end],
                                                                dd_args.no_cols,dd_figfile,res_frames=res_frames[start:end])
                    
                    
                
        
    #Both model and lc_toggle require reading of the modfile, do this together
    if lc_args or model_args:
        
        if str(modfile).endswith('.mod'):
            mod_info = modFile.from_file(modfile)
            mod_vx = mod_info.components[0]
            V,F,FN,FNa = mod_vx.vertices, mod_vx.facets, mod_vx.FN, mod_vx.FNa
        if str(modfile).endswith('.obj'):
            mesh = trimesh.load(modfile)
            V  = mesh.vertices
            F  = mesh.faces
            FN = mesh.face_normals
                    
        if lc_args:
            #Assume there is only one optical scattering law
            #Though test for if it exists (More likely to have 0 than 2+)
            try:
                mod_ol = mod_info.phot_functions.optical[0]
            except (KeyError, IndexError):
                raise RuntimeError('No optical scattering law found in mod file')
            scattering_law = mod_ol.type
            scattering_params = mod_ol.values_to_dict()
            mod_ss = mod_info.spinstate
            t0,P = mod_ss.t0.jd, mod_ss.P
            lam,bet,phi = mod_ss.lam, mod_ss.bet, mod_ss.phi+90

            #Create plots and output results dictionary (not done)
            pub_lightcurve_generator(pub_path, lc_args.lc_file,
                                                            t0, lam, bet, phi, P,
                                                            FN, FNa, V=V, F=F,
                                                            scattering_law=scattering_law,
                                                            scattering_params=scattering_params,
                                                            shadowing=True,
                                                            plot=True, show_plot=False)

            #Combine the figures
            out_stem = f'PubLC_{identifier}'
            lightcurves.concat_lc_plots(pub_path,outdir,out_stem)        
    
        if model_args:
        
            red_facets = set()
            yellow_facets = set()

            if model_args.redfile:
                with open(model_args.redfile) as f:
                    red_facets = {int(l.split()[1]) for l in f}
            else:
                red_facets = []

            if model_args.yellowfile:
                with open(model_args.yellowfile) as f:
                    yellow_facets = {int(l.split()[1]) for l in f}
            else:
                yellow_facets = []
                    
            ticks= model_args.ticks
            lims = model_args.lims
            
            # Get colour
            facet_colours = []
            shading_flags = []
            for i in range(len(F)):
                if i in red_facets:
                    facet_colours.append([1.0, 0.0, 0.0])
                    shading_flags.append(2)
                elif i in yellow_facets:
                    facet_colours.append([1.0, 1.0, 0.0])
                    shading_flags.append(2)
                else:
                    facet_colours.append([0.8,0.8,0.8])
                    shading_flags.append(1)
            facet_colours = np.array(facet_colours)
                
            out_stem = f'{outdir}/PubModel_{identifier}'
            model.pub_model(V,F,FN,
                        facet_colours=facet_colours, shading_flags=shading_flags,
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
@dataclass
class DDArgs:
    obsfile: Path
    no_cols: int
    res: bool
    max_rows: int


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Creates publication pdfs for each toggled plot type",
                                     epilog='Saves pdfs as {outdir}/Pub{pubtype}_{identifier}.pdf')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    io_group = parser.add_argument_group('IO inputs')    
    io_group.add_argument("modfile", type=str, help="model file (compulsory) [.mod; .obs]")
    io_group.add_argument("-o",'--outdir', type=str, default='./PubPlots',
                          help="Directory of pdfs saved. Default ./PubPlots")
    io_group.add_argument("--obsfile", type=str, help="obsfile (compulsory for cw and dd)")


    cw_group = parser.add_argument_group('CW plots (-cw)')
    cw_group.add_argument("-cw", action="store_true", help="Plot CW data. modfile must be in SHAPE format.")
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
    
    dd_group = parser.add_argument_group('Delay-Dopler collages (-dd)')
    dd_group.add_argument("-dd", action="store_true", help="Create delay-Doppler collages")
    dd_group.add_argument("--no-cols", type=int, default=3, 
                          help="Number of columns for collage, Default 3")
    dd_group.add_argument("--res", action="store_true", help='Includes residuals in collage')
    dd_group.add_argument("--max-rows", type=int, default=12,
                          help="Max number of rows before page break. Default 12")

    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    if not args.lc and not args.cw and not args.mp and not args.dd:
        error_exit('Must specify which plots to be created')
    else:
        args.modfile = check_file(args.modfile)

    args.lc_args,args.cw_args,args.model_args,args.dd_args = None,None,None,None
        
    #CW checks
    if args.cw or args.dd:
        if not args.obsfile:
            error_exit('Must provide obsfile when using -cw or -dd')
        if str(args.modfile).endswith('.obj'):
            error_exit('Must use a SHAPE .mod file for cw and dd options')
        args.wparfile = check_file(args.wparfile)
        if args.cw:
            args.obsfile = check_file(args.obsfile)
            args.cw_args = CWArgs(obsfile=args.obsfile, wparfile=args.wparfile)
        if args.dd:
            args.obsfile_ = check_file(args.obsfile)
            args.dd_args = DDArgs(obsfile=args.obsfile, no_cols=args.no_cols, 
                                  res=args.res, max_rows=args.max_rows)

    #LC checks
    if args.lc:
        if not args.lcfile:
            error_exit('Must provide lcfile when using -lc')
        args.lcfile = check_file(args.lcfile)
        args.lc_args = LCArgs(lc_file=args.lcfile)

    #Model checks
    if args.mp:
        if args.redfile:
            args.redfile = check_file(args.redfile)
        if args.yellowfile:
            args.yellowfile = check_file(args.yellowfile)
        args.model_args = ModelArgs(redfile=args.redfile, yellowfile=args.yellowfile,
                                    ticks=args.ticks, lims=args.lims)
    
    #Create output directory if doesn't exist.
    args.outdir = check_dir(args.outdir,create=True)
    
    return args

def main():
    args = parse_args()
    args = validate_args(args)    
    
    logger.info(f"Processing: {args.modfile}")
    write_pub(args.modfile, args.outdir,
              args.model_args,args.cw_args,args.lc_args,args.dd_args)

if __name__ == "__main__":
    main()



