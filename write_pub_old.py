#Last modified by @recannon on 10/01/2026

import argparse
import logging
from pathlib import Path
import subprocess
from pyshape.obs import obs_io_old
from pyshape.cli_config import logger, error_exit
import pyshape.plotting.pub_routines as pp
from pyshape.utils import time_shape2astropy, check_file
from pyshape.jinja_env import template_env
from pyshape.mod.mod_io import modFile
from pyshape import artificial_lightcurves

def write_pub(modfile,obsfile,wparfile='par/wpar',outpdf=None):

    current_path = Path.cwd()
    waction_path = current_path / 'waction'
    temp_path    = waction_path / 'temp'
    pub_path     = waction_path / 'pub'
    
    #Identifier for shape logs
    identifier = f'{modfile.stem}__{obsfile.stem}' if modfile.stem != obsfile.stem else modfile.stem
    
    #Changes filepaths to absolute paths. Needed as shape functions are run from ./waction, not ./
    modfile,obsfile = Path(modfile).resolve(),Path(obsfile).resolve()
    wparfile = Path(wparfile).resolve()

    #Makes sure waction/temp and waction/pub exist (and by extension waction)
    temp_path.mkdir(parents=True, exist_ok=True)
    pub_path.mkdir(parents=True, exist_ok=True)

    #Empty waction and pub folders without trying to remove directories
    subprocess.run('find waction/temp -maxdepth 1 -type f -exec rm {} +', shell=True, check=True)
    subprocess.run('find waction/pub -maxdepth 1 -type f -exec rm {} +', shell=True)

    #Run write with shape (doesn't require moments)
    logger.info('Running write')
    logger.debug(f"shape {wparfile} {modfile} {obsfile}")
    with open(waction_path / f'{identifier}.wpar.log', 'w') as log:
        try:
            subprocess.run(["shape", str(wparfile), str(modfile), str(obsfile)], cwd=temp_path, stdout=log, check=True)
        except subprocess.CalledProcessError:
            error_exit(f'Problem running write action. Check {log.name}')

    #Collage mpar figures
    logger.info('Creating pdfs')
    
    #Read obsfile to check for which data types are present
    obs_sets  = obs_io_old.read(obsfile)
    set_types = set(obs_set.type for obs_set in obs_sets) 
    
    if 'doppler' in set_types:
        
        cw_sets = [o for o in obs_sets if o.type=='doppler']
        cw_fits = sorted(temp_path.glob("fit_??_??.dat"))
        pos_ppms = sorted(temp_path.glob('sky_??_??.ppm'))
        
        cw_list = []
        
        #Create individual pdfs for each CW
        for i, (cw,ppm) in enumerate(zip(cw_fits,pos_ppms)):
            
            entry_line = cw_sets[i].lines[-3]
            logger.debug(f'{entry_line = }')
            date = " ".join(entry_line.split()[1:7])
            cw_start = time_shape2astropy(date)
            
            start_jd   = cw_start.jd
            start_date = cw_start.isot.split('T')[0]
            
            fig_title = f'{i+1} $\\bullet$ {start_date} $\\bullet {start_jd:.3f}$ '
            
            #Create fit plot
            logger.info(f'Plotting {cw}')
            fit_pdf = pub_path/f'CW_fit_{i+1}.pdf'
            pp.pub_doppler(cw,fig_title,save=fit_pdf)

            #Create pos pdf
            pos_pdf = pub_path/f'CW_pos_{i+1}.pdf'
            subprocess.run(["convert", ppm, pos_pdf], check=True)

            cw_list.append({
                "cw_pdf":  fit_pdf,
                "pos_pdf": pos_pdf,
            })

        if not outpdf:
            out_stem = f'PubCW_{identifier}'
        elif outpdf:
            out_stem = outpdf.replace('.pdf','')

        template = template_env.get_template("pub_cw_plots.tex.j2")
        tex_output = template.render(cw_list=cw_list)

        tex_file = pub_path / f'{out_stem}.tex'
        tex_file.write_text(tex_output)        
        
        subprocess.run(["pdflatex", tex_file.name],
                cwd=pub_path, check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) #Keeps errors

        #Move final pdf
        out_pdf = pub_path / f'{out_stem}.pdf'
        destination = current_path / out_pdf.name
        out_pdf.replace(destination)
        logger.info(f'Moved final pdf to {out_pdf}')
        
    if 'lightcurve' in set_types:
                
        lc_filename  = Path(f"/cephfs/rcannon/2000rs11/lightcurves/2000rs11.lc.txt")
                
        #Read modfile for spin state, scattering laws, and shape
        mod_info = modFile.from_file(modfile)
        mod_vx = mod_info.components[0]
        V,F,FN,FNa = mod_vx.vertices, mod_vx.facets, mod_vx.FN, mod_vx.FNa
        mod_ss = mod_info.spinstate
        t0,P = mod_ss.t0.jd, mod_ss.P
        lam,bet,phi = mod_ss.lam, mod_ss.bet, mod_ss.phi+90

        #Assume there is only one optical scattering law
        #Though test for if it exists (More likely to have 0 than 2+)
        try:
            mod_ol = mod_info.phot_functions[1][0]
        except (KeyError, IndexError):
            raise RuntimeError("No optical scattering law found in mod file")
        scattering_law = mod_ol.type
        scattering_params = mod_ol.values_to_dict()

        #Create plots and output results dictionary (not done)
        results = artificial_lightcurves.pub_lightcurve_generator(pub_path,lc_filename,t0,lam,bet,phi,P,FN,FNa,V=V,F=F,shadowing=True,plot=True,show_plot=False)

        if not outpdf:
            out_stem = f'PubLC_{identifier}'
        elif outpdf:
            out_stem = outpdf.replace('.pdf','')

        #Combine the figures
        artificial_lightcurves.concat_lc_plots(pub_path,current_path,out_stem)
        
        
        
    # #Stack jpg files into a pdf
    # jpg_files = sorted(temp_path.glob("*.jpg"))
    # output_name = outdir / f"{identifier}.pdf"
    # script_dir = Path(__file__).resolve().parent
    # subprocess.run(["bash", script_dir / "bash_scripts/create_pdf.sh", output_name, *map(str, jpg_files)], check=True)
    
    # #Empty waction folder without trying to remove directories
    # subprocess.run('find waction/temp -maxdepth 1 -type f -exec rm {} +', shell=True, check=True)

    return True

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Calls shape moment/write action and saves results as PDFs.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    input_group = parser.add_argument_group('Compulsory input files')    
    input_group.add_argument("modfile", type=str, nargs='?', help="modfile to write.")
    input_group.add_argument("obsfile", type=str, nargs='?', help="obsfile to write.")
    
    data_group = parser.add_argument_group('Specify which data types to create pdfs for. Default: all')
    data_group.add_argument("-lc", action="store_true", help="LC data")
    data_group.add_argument("-cw", action="store_true", help="CW data")
    
    optional_group = parser.add_argument_group('Optional input parameters')
    optional_group.add_argument("-w", "--wparfile", type=Path, default='./par/wpar',
                        help="wpar file to use. Default cwd/par/wpar")
    optional_group.add_argument("-o",'--outpdf', type=str, default=None,
                        help="Name of pdf saved. Default Pub{dtype}_{identifier}.pdf")

    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #Check optional inputs
    if not args.wparfile.is_file():
        error_exit(f'Cannot find given wparfile: {args.wparfile}')

    if not args.modfile or not args.obsfile:
        error_exit('Must provide both obsfile and modfile')
    else:
        args.modfile = check_file(args.modfile)
        args.obsfile = check_file(args.obsfile)
    
    return args

def main():
    args = parse_args()
    args = validate_args(args)    
    
    logger.info(f"Processing: {args.modfile} and {args.obsfile}")
    write_pub(args.modfile, args.obsfile,
                args.wparfile, args.outpdf)

if __name__ == "__main__":
    main()



