#Last modified by @recannon 06/01/2026

import subprocess
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import argparse
import logging
from ..io_utils import logger, error_exit, check_dir

def concat_lc_plots(figdir:Path, outdir:Path, pdf_name:str = 'Art_LC_Plots'):

    #Setup jinja
    script_dir = Path(__file__).resolve().parent
    templates_dir = script_dir.parent / "templates" / "latex"
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=False   # IMPORTANT for LaTeX
    )
    template = env.get_template("concat_lc_plots.tex.j2")
    logger.debug('Loaded template')

    #Number of lightcurves and their numbers (range)
    lightcurve_pdfs = sorted(figdir.glob("*.pdf"))
    logger.debug(f'pdf files: \n {lightcurve_pdfs}')
    n_lightcurves = len(lightcurve_pdfs)
    lightcurve_nos = list(range(1, n_lightcurves + 1))

    #Create tex file
    latex = template.render(lightcurve_nos=lightcurve_nos)
    out_tex = figdir / f'{pdf_name}.tex'
    out_tex.write_text(latex)
    logger.info(f'Creating pdf from {out_tex}')
    subprocess.run(["pdflatex", out_tex.name],
                cwd=figdir, check=True, )
                #stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) #Keeps errors

    #Move final pdf
    out_pdf = figdir / f'{pdf_name}.pdf'
    destination = outdir / out_pdf.name
    out_pdf.replace(destination)
    logger.info(f'Moved final pdf to {out_pdf}')
    
    return True


#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Combine LC plots generated with pub_lightcurve_generator")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")
    
    #Combine args
    arg_group = parser.add_argument_group('Arguments for creating combined figure')
    arg_group.add_argument('--figdir',type=str,default=None,
                            help='Directory containing individual LC PDFs')
    arg_group.add_argument('--outdir',type=str,default=None,
                            help='Output directory for combined PDF')
    arg_group.add_argument("--name", type=str, default="Artificial_LC_Plots",
                            help="Base name of output PDF (no extension)")
    
    return parser.parse_args()


def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #Check directories exist
    if not args.figdir:
        error_exit('Must provide --figdir')
    else:
        args.figdir = check_dir(args.figdir)
    
    if not args.outdir:
        error_exit('Must provide --outdir')
    else:
        args.outdir = check_dir(args.outdir)

    return args


#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    concat_lc_plots(args.figdir, args.outdir, args.name)

    return True

if __name__ == "__main__":
    main()
    