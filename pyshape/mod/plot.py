#Last modified by @recannon 27/08/2026

#27/08/2026 - More documentation
#21/08/2026 - Creation

#Niche script to plot several different models next to eachother for ease of comparison.
#Requires heavy customisation, so won't really document until I've tidied it up

import argparse
import logging
from pathlib import Path
from pyshape.cli.cli_config import logger
from pyshape.utils import check_file
from pyshape.mod.mod_io import modFile
from dataclasses import dataclass
import trimesh
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from pyshape.plotting.model.plot_model_projection import plot_model_projection
import numpy as np
import pandas as pd
import re

titlesize = 30
labelsize = 25
no_rows = 1
no_cols = 3

def generate_lims_and_ticks(vertices):
    '''Round down to a axis tick that is a multiple of 1,2,3,5'''
    extent = np.abs(vertices).max()
    lims = 1.1 * extent   
    exponent = np.floor(np.log10(lims))
    base = 10 ** exponent
    for m in (5, 3, 2, 1):
        if m * base <= lims:
            return lims, m * base
    return lims, base

def plot_models(modfiles,outstem,titles):
    
    plt.rcParams.update({'font.size': 30})
    fig, axes = plt.subplots(no_rows, no_cols, figsize=(30, 30))
    
    #Loops through each axes and file to plot
    for ax, modfile, title in zip(axes.flatten(),modfiles,titles):
        print(title)
        
        #Read in file
        if str(modfile).endswith('.mod'):
            mod_info = modFile.from_file(modfile)
            mod_vx = mod_info.components[0]
            V,F,FN,_ = mod_vx.vertices, mod_vx.facets, mod_vx.FN, mod_vx.FNa
        if str(modfile).endswith('.obj'):
            mesh = trimesh.load(modfile)
            if 'itokawa' in str(modfile).lower():
                angle = np.radians(90)
                axis = [1, 0, 0]  # X axis
                rot_matrix = trimesh.transformations.rotation_matrix(angle, axis)
                mesh.apply_transform(rot_matrix)
            V  = mesh.vertices
            F  = mesh.faces
            FN = mesh.face_normals  
        
        #Create and plot model projection
        ax = plot_model_projection(V,F,FN,ax,'+Z')
    
        lims,ticks = generate_lims_and_ticks(V)   
    
        #Then tick formatting!
        ax.tick_params(direction='in')
        ax.set_xlim(-lims,lims)
        ax.set_ylim(-lims,lims)
        ax.set_aspect('equal')
        ax.spines[['right', 'top']].set_visible(False)
        ax.set_title(rf'{title}', fontsize=titlesize)
        ax.xaxis.set_major_formatter(FormatStrFormatter('%g'))
        ax.yaxis.set_major_formatter(FormatStrFormatter('%g'))
        ax.set_xticks([-ticks, 0.0, ticks])
        ax.set_yticks([-ticks, 0.0, ticks])
        ax.grid(True, which='major', linewidth=0.8, alpha=0.6)
        ax.spines['left'].set_linewidth(2.5)
        ax.spines['bottom'].set_linewidth(2.5)
        ax.set_xlabel('X [km]', fontsize=labelsize)
        ax.set_ylabel('Y [km]', fontsize=labelsize)
                
    plt.tight_layout()
    plt.savefig(f'{outstem}.pdf', bbox_inches='tight', dpi=300)
    plt.close()
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
    parser = argparse.ArgumentParser(description="Plots the model for a single viewing geometry",
                                     epilog='Saves pdfs as {outdir}/Pub{pubtype}_{identifier}.pdf')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    io_group = parser.add_argument_group('IO inputs')    
    io_group.add_argument("modfiles", type=str, nargs='+', help="model files (compulsory) [.mod; .obs]")
    io_group.add_argument("-o",'--outstem', type=str, default='model_plots',
                          help="Stem of saved pdf default ./model_plots[.pdf]")

    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')
    
    new_filelist = []
    for f in args.modfiles:
        new_filelist.append(check_file(f))
    args.modfiles = new_filelist
    
    return args

def sort_key(name):
    if not isinstance(name, str):
        name = str(name)
    match = re.match(r'^\((\d+)\)', name)
    if match:
        return (0, int(match.group(1)), name)
    if '/' in name:
        return (2, 0, name)
    return (1, 0, name)


def main():
    args = parse_args()
    args = validate_args(args)

    metadatas = '/home/rcannon/Code/CBtab/metadatas.csv'
    df_objs = pd.read_csv(metadatas)

    titles = []
    for modfile in args.modfiles:
        obj_name = modfile.stem
        if obj_name in df_objs['ObjName'].values:
            title = df_objs.loc[df_objs['ObjName'] == obj_name, 'Name'].iloc[0]
        else:
            title = obj_name
        titles.append(title)

    order = sorted(range(len(titles)), key=lambda i: sort_key(titles[i]))
    args.modfiles = [args.modfiles[i] for i in order]
    titles = [titles[i] for i in order]

    plot_models(args.modfiles, args.outstem, titles)
    
if __name__ == "__main__":
    main()



