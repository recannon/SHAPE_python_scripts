#Last modified by @recannon 20261124

#Used for pretty much everything
import argparse
from dataclasses import dataclass
import logging
from pathlib import Path
from ..utils import check_dir
from .config import logger
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

from ..simulation.gravitational_environment import gravitational_potential

from ..plotting import model

#Only used for certain data types, don't load unless required
lazy import trimesh #lc and model (as can take obj as file input type)
lazy from ..io.mod_io import modFile #lc and model (if given as shape mod format)


def write_gravenv(modfile,density,outdir,ticks,lims):
    
    #Setting up paths
    current_path = Path.cwd()
    waction_path = current_path / 'waction'
    pub_path     = waction_path / 'pub'
    #Makes sure waction/temp and waction/pub exist (and by extension waction)
    pub_path.mkdir(parents=True, exist_ok=True)
    modfile = Path(modfile).resolve()
    
    identifier = f'{modfile.stem}'

    #Read model information
    if str(modfile).endswith('.mod'):
        mod_info = modFile.from_file(modfile)
        mod_vx = mod_info.components[0]
        V,F,FN,FNa = mod_vx.vertices, mod_vx.facets, mod_vx.FN, mod_vx.FNa
    if str(modfile).endswith('.obj'):
        mesh = trimesh.load(modfile)
        V  = mesh.vertices
        F  = mesh.faces
        FN = mesh.face_normals
        
    #Calculate U_plot (for Grav potential)
    mesh.apply_scale(1000)
    U, U_cent = gravitational_potential(mesh, density)
    mesh.apply_scale(0.001)
    U_plot = (-U-U_cent) * 100
    pmin,pmax,pstep = U_plot.min(),U_plot.max(),0.01

    out_stem = f'{outdir}/PubGravPot_{identifier}'
    
    #Color map
    orex = [[0.3843,0.2941,0.6588], [0.3137,0.3725,0.6902], [0.1961,0.4510,0.7216], [0.1451,0.5255,0.7294], [0.0471,0.6000,0.7333], [0.1451,0.6667,0.6980], [0.1922,0.7451,0.6549], [0.3333,0.7843,0.6431], [0.4431,0.8235,0.6353], [0.5490,0.8588,0.6235], [0.6471,0.8902,0.6078], [0.7373,0.9176,0.5882], [0.8196,0.9490,0.5647], [0.8745,0.9647,0.5882], [0.9294,0.9843,0.6118], [0.9647,0.9961,0.6588], [1.0000,1.0000,0.7098], [1.0000,0.9647,0.6510], [1.0000,0.9294,0.5765], [1.0000,0.8784,0.5098], [1.0000,0.8275,0.4471], [1.0000,0.7647,0.3882], [1.0000,0.6941,0.3294], [1.0000,0.6157,0.2902], [1.0000,0.5294,0.2549], [1.0000,0.4510,0.2353], [1.0000,0.3647,0.2118], [0.9765,0.2941,0.2431], [0.9412,0.2235,0.2706], [0.8824,0.1412,0.2745], [0.8235,0.0667,0.2784], [0.7490,0.0353,0.2667]]
    norm = colors.Normalize(vmin=pmin, vmax=pmax)
    cmap_orex = colors.ListedColormap(orex)
    # sm = plt.cm.ScalarMappable(cmap=cmap_orex, norm=norm)
    cmap = plt.get_cmap(cmap_orex)

    facet_colours = cmap(norm(U_plot))[:, :3]            # (Nf, 3) RGB

    out_stem = f'{outdir}/PubGravPot_{identifier}'
    shading_flags = np.zeros(len(F), dtype=int)
    model.pub_model(V,F,FN,facet_colours,shading_flags,out_stem,
                    lims=lims,ticks=ticks,
                    norm=norm, cmap=cmap, cbar_label='Gravitational Potential [0.01 J/kg]',
                    cbar_params=[pmin,pmax,pstep])

    return True

#===Functions for parsing below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Creates publication pdfs for gravitational environment and slopes.",
                                     epilog='Saves pdfs as {outdir}/Pub{pubtype}_{identifier}.pdf')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    io_group = parser.add_argument_group('Inputs')    
    io_group.add_argument("modfile", type=str, help="model file")
    io_group.add_argument("density", type=float, help="Density of the object, in SI units")
    io_group.add_argument("-o",'--outdir', type=str, default='./PubPlots',
                          help="Directory of pdfs saved. Default ./PubPlots")

    plot_group = parser.add_argument_group('Plotting customisations')
    plot_group.add_argument("--ticks", type=float, default=0.3,
                          help="Symmetric location of axis ticks and grid lines")
    plot_group.add_argument("--lims", type=float, default=0.45,
                          help="Symmetric location of axis limits")

    
    return parser.parse_args()

def validate_args(args):
    """Validate arguments"""
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')
    
    #Create output directory if doesn't exist.
    args.outdir = check_dir(args.outdir,create=True)
    
    return args

def main():
    args = parse_args()
    args = validate_args(args)    
    
    logger.info(f"Processing: {args.modfile}")
    write_gravenv(args.modfile, args.density, args.outdir, args.ticks, args.lims)

if __name__ == "__main__":
    main()



