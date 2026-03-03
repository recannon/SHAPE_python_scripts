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
        colour = facet_lighting(light_dir, view_dir, normals[n], n,
                                red_facets=red_list,
                                yellow_facets=yellow_list)

        #Each pc is only one vertex. Otherwise this can screw with concavities
        pc = PolyCollection([verts], zorder=zorder)
        pc.set_facecolor(colour)
        pc.set_edgecolor(colour)
        ax.add_collection(pc)
        
    return ax
    