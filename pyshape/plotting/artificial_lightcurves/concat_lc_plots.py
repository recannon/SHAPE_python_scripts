#Last modified by @recannon 07/01/2026

import subprocess
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import argparse
import logging
from ...cli_config import logger, error_exit
from ...utils import check_dir
from ...jinja_env import render_and_compile_pdf

def concat_lc_plots(figdir:Path, outdir:Path, pdf_name:str = 'Art_LC_Plots'):

    #Number of lightcurves and their numbers (range)
    lightcurve_pdfs = sorted(figdir.glob("ArtLC*.pdf"))
    logger.debug(f'pdf files: \n {lightcurve_pdfs}')
    n_lightcurves = len(lightcurve_pdfs)
    lightcurve_nos = list(range(1, n_lightcurves + 1))
    
    #Render as pdf
    render_and_compile_pdf("concat_lc_plots.tex.j2", {"lightcurve_nos": lightcurve_nos},
                           pdf_name, figdir, outdir)
    
    return True
