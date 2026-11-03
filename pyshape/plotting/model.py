#Last modified by @recannon 20261028

#20261028 - General tidy up

from astropy.stats import sigma_clip
from astropy.time import Time
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from mpl_toolkits.mplot3d.art3d import PolyCollection
import numpy as np
from rich.progress import track

from ..cli.config import logger
from ..mod.mod_io import modFile

#x_label, y_label, invert_x, invert_y
VIEW_AXES = {
    "+Z": ("X", "Y", False, False),
    "-Z": ("X", "Y", False, True),
    "+Y": ("X", "Z", True,  False),
    "-Y": ("X", "Z", False, False),
    "+X": ("Y", "Z", False, False),
    "-X": ("Y", "Z", True,  False),
}

def pub_model(vertices,facets,normals,
              out_stem,
              red_list=None,yellow_list=None,
              lims = 0.6, ticks=0.5, titlesize=35, labelsize=30):
    
    views = ['+Z', '+Y', '+X', '-Z', '-Y', '-X']

    # plt.rcParams.update({'font.size': 30})
    with plt.rc_context({"font.size": 30}):
        fig, axes = plt.subplots(2, 3, figsize=(30, 16))
        
        for ax, view in zip(axes.flatten(), views):
            
            #Create and plot model projection
            ax = plot_model_projection(vertices,facets,normals,
                                    ax,view,
                                    red_list=red_list,yellow_list=yellow_list)
        
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
            
            #Format axes
            xl, yl, inv_x, inv_y = VIEW_AXES[view]
            ax.set_xlabel(f"{xl} [km]", fontsize=labelsize)
            ax.set_ylabel(f"{yl} [km]", fontsize=labelsize)
            if inv_x: ax.invert_xaxis()
            if inv_y: ax.invert_yaxis()
                    
        fig.tight_layout()
        fig.savefig(f'{out_stem}.pdf', bbox_inches='tight', dpi=300)
        plt.close(fig)
        
        
#For default directions. Can take custom
DIR_LOOKUP = {
    '+Z': np.array([0, 0,  1], dtype=float),
    '-Z': np.array([0, 0, -1], dtype=float),
    '+Y': np.array([0,  1, 0], dtype=float),
    '-Y': np.array([0, -1, 0], dtype=float),
    '+X': np.array([ 1, 0, 0], dtype=float),
    '-X': np.array([-1, 0, 0], dtype=float),
}

def plot_model_projection(vertices,facets,normals,
                           ax,view,
                           red_list=None,yellow_list=None):

    #Identical values, for if I decide to add ability to do custom geometries
    light_dir = DIR_LOOKUP[view]
    view_dir = DIR_LOOKUP[view]

    #Vertices arranged in 3s for each facet
    x = vertices[facets, 0].T
    y = vertices[facets, 1].T
    z = vertices[facets, 2].T

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
        face_colour,edge_colour = facet_lighting(light_dir, view_dir, normals[n], n,
                                red_facets=red_list,
                                yellow_facets=yellow_list)

        #Each pc is only one vertex. Otherwise this can screw with concavities
        pc = PolyCollection([verts], zorder=zorder)
        pc.set_facecolor(face_colour)
        pc.set_edgecolor(edge_colour)
        ax.add_collection(pc)
        
    return ax
    
def facet_lighting(light_dir, view_dir, normals, facet_id,
                   red_facets=None, yellow_facets=None,
                   ambient=0.2,
                   diffuse_strength=0.7,
                   specular_strength=0.6,
                   shininess=80):
    
    #Check normalised
    light_dir = light_dir / np.linalg.norm(light_dir)

    #Diffuse shading
    diffuse = max(np.dot(normals, light_dir), 0)
    #Specular (glossiness)
    reflect_dir = 2*np.dot(normals, light_dir)*normals - light_dir
    spec = max(np.dot(view_dir, reflect_dir), 0) ** shininess
    #Combine effects
    intensity = ambient + diffuse_strength*diffuse + specular_strength*spec
    intensity = np.clip(intensity, 0, 1)

    #Red and yellow tend colour->white rather than black->colour
    white = np.array([1.0, 1.0, 1.0])
    if red_facets is not None and facet_id in red_facets:
        bright = np.array([1.0, 0.0, 0.0])  # pure red
        face_colour = bright + (white - bright) * spec  # white highlight
        face_colour = np.clip(face_colour, 0, 1)
    elif yellow_facets is not None and facet_id in yellow_facets:
        bright = np.array([1.0, 1.0, 0.0])  # pure yellow
        face_colour = bright + (white - bright) * spec
        face_colour = np.clip(face_colour, 0, 1)
    else:
        base_colour = np.array([0.8, 0.8, 0.8])
        face_colour = base_colour * intensity
    
    # edge_colour = np.array([0.8, 0.8, 0.8]) * intensity
    edge_colour = face_colour
    
    return face_colour, edge_colour