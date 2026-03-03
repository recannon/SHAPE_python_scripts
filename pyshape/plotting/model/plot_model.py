#Last modified by @recannon 03/03/2026
#Originally derived in part from Sam Jacksons scripts

import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from mpl_toolkits.mplot3d.art3d import PolyCollection
import numpy as np
import cmasher as cmr
from pyshape.mod.mod_io import modFile
from rich.progress import track
from .facet_lighting import facet_lighting

DIR_LOOKUP = {
    '+Z': np.array([0, 0,  1], dtype=float),
    '-Z': np.array([0, 0, -1], dtype=float),
    '+Y': np.array([0,  1, 0], dtype=float),
    '-Y': np.array([0, -1, 0], dtype=float),
    '+X': np.array([ 1, 0, 0], dtype=float),
    '-X': np.array([-1, 0, 0], dtype=float),
}

def format_model_projection_subplot(ax,view,
                          ticks=0.5,lims=0.6,
                          titlesize=35,labelsize=30):

    #Then tick formatting!
    ax.tick_params(direction='in')
    ax.set_xlim(-lims,lims)
    ax.set_ylim(-lims,lims)
    ax.set_aspect('equal')
    ax.spines[['right', 'top']].set_visible(False)
    ax.set_title(rf'$\bf {view} $', fontsize=titlesize)
    ax.xaxis.set_major_formatter(FormatStrFormatter('%g'))
    ax.yaxis.set_major_formatter(FormatStrFormatter('%g'))
    ax.set_xticks([-ticks, 0.0, ticks])
    ax.set_yticks([-ticks, 0.0, ticks])
    ax.grid(True, which='major', linewidth=0.8, alpha=0.6)
    ax.spines['left'].set_linewidth(2.5)
    ax.spines['bottom'].set_linewidth(2.5)
    
    match view:
        case '+Y':
            ax.set_xlabel('X [km]', fontsize=labelsize)
            ax.set_ylabel('Z [km]', fontsize=labelsize)
            ax.invert_xaxis()
        case '-Y':
            ax.set_xlabel('X [km]', fontsize=labelsize)
            ax.set_ylabel('Z [km]', fontsize=labelsize)
        case '+X':
            ax.set_xlabel('Y [km]', fontsize=labelsize)
            ax.set_ylabel('Z [km]', fontsize=labelsize)
        case '-X':
            ax.set_xlabel('Y [km]', fontsize=labelsize)
            ax.set_ylabel('Z [km]', fontsize=labelsize)
            ax.invert_xaxis()
        case '+Z':
            ax.set_xlabel('X [km]', fontsize=labelsize)
            ax.set_ylabel('Y [km]', fontsize=labelsize)
        case '-Z':
            ax.set_xlabel('X [km]', fontsize=labelsize)
            ax.set_ylabel('Y [km]', fontsize=labelsize)
            ax.invert_yaxis()
            
    return ax

def plot_model_projections(model_name,
         red_list,yellow_list):
    
    mod_info = modFile.from_file(model_name)
    vx_mod = mod_info.components[0]
    vertices = vx_mod.vertices
    facets = vx_mod.facets
    normals = vx_mod.FN
    x = vertices[facets, 0].T
    y = vertices[facets, 1].T
    z = vertices[facets, 2].T
    
    views = ['+Z', '+Y', '+X', '-Z', '-Y', '-X']

    plt.rcParams.update({'font.size': 30})
    fig, axes = plt.subplots(2, 3, figsize=(30, 16))
    
    for ax, view in zip(axes.flatten(), views):

        # light_dir defaults per-view, but can be overridden globally
        light_dir = DIR_LOOKUP[view]
        view_dir = DIR_LOOKUP[view]

        for n in track(range(len(facets)), description=view):

            #This facets vertices
            xn, yn, zn = x[:, n], y[:, n], z[:, n]
            #Drops the 'depth' of each facet (Creates the projection)
            match view:
                case '+Y': verts = list(zip(xn, zn)); zorder =  int(np.max(yn) * 1000)
                case '-Y': verts = list(zip(xn, zn)); zorder = -int(np.min(yn) * 1000)
                case '+X': verts = list(zip(yn, zn)); zorder =  int(np.max(xn) * 1000)
                case '-X': verts = list(zip(yn, zn)); zorder = -int(np.min(xn) * 1000)
                case '+Z': verts = list(zip(xn, yn)); zorder =  int(np.max(zn) * 1000)
                case '-Z': verts = list(zip(xn, yn)); zorder = -int(np.min(zn) * 1000)
                case _: raise ValueError(f'Invalid view: {view!r}')

            #Get colour
            colour = facet_lighting(light_dir, view_dir, normals[n], n,
                                    red_facets=red_list,
                                    yellow_facets=yellow_list)

            #Each pc is only one vertex. Otherwise this can screw with concavities
            pc = PolyCollection([verts], zorder=zorder)
            pc.set_facecolor(colour)
            pc.set_edgecolor(colour)
            ax.add_collection(pc)
            
        format_model_projection_subplot(ax, view)
        
    plt.tight_layout()
    plt.savefig(f'test_views.png', bbox_inches='tight', dpi=200)
    plt.close()
    
if __name__ == '__main__':
    
    model_name = '/home/rcannon/Code/Radar/SHAPE/2000rs11/PS2/FF/modfiles/FF.mod'

    with open('/home/rcannon/Code/Radar/SHAPE/2000rs11/PS2/FF/unseen90.dat') as f:
        red_list = {int(d) for d in f}

    with open('/home/rcannon/Code/Radar/SHAPE/2000rs11/PS2/FF/unseen60.dat') as f:
        yellow_list = {int(d) for d in f}
    
    plot_model_projections(model_name,red_list,yellow_list)
    