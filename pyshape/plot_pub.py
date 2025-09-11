#Last modified 14/05/2025

import matplotlib.pyplot as plt
import numpy as np
from . import polescan
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from .outfmt import logger
import matplotlib.tri as tri


def pp_polescan(bet:np.array, lam:np.array, chi:np.array, 
                cmp_array:list, cmp:str='magma', save:bool=False):

    lon_plot,lat_plot,chi_plot = polescan.interpolate_chi(bet,lam,chi)
    coords_plot = tri.Triangulation(lon_plot, lat_plot)

    proj = ['N','S']
    ortho_N = ccrs.Orthographic(central_longitude=180,central_latitude=+90)
    ortho_S = ccrs.Orthographic(central_longitude=0,central_latitude=-90)
    moll    = ccrs.Mollweide(central_longitude=180)
    sine    = ccrs.Sinusoidal()
    pltcrr  = ccrs.PlateCarree()

    # col_contours = np.linspace(np.min(coords_chi), perc_levels[0], 11)
    col_contours = cmp_array

    fig = plt.figure(figsize=[3.37689*2,3.7689*9/8*2])
    ax1 = plt.subplot2grid(shape=(2, 2), loc=(0, 0), colspan=1, projection=ortho_N)
    ax2 = plt.subplot2grid(shape=(2, 2), loc=(0, 1), colspan=1, projection=ortho_S)
    ax3 = plt.subplot2grid(shape=(2, 2), loc=(1, 0), colspan=2, projection=moll)   

    for i,ax in enumerate([ax1,ax2,ax3]):
        ax.set_global()
        
        ax.tricontourf(coords_plot, chi_plot, cmap=cmp, levels=col_contours,transform=pltcrr)
        # ax.tricontour(coords_plot, chi_plot, levels=perc_levels,
                #    colors=['r','g','b'], linestyles=['-','--',':'],transform=pltcrr)

        gl = ax.gridlines(draw_labels=True, linestyle='-')
        
        gl.xlocator = mticker.FixedLocator([-120,-60,0,60,120,179.999])
        gl.ylocator = mticker.FixedLocator([-90,-60,-30,0,30,60,90])

        gl.xformatter = mticker.FuncFormatter(lambda x, pos: f"{x % 360:.0f}°")
        gl.yformatter = mticker.FuncFormatter(lambda x, pos: f"{x:.0f}°")

        #N/S labels
        if i!=2:
            ax.text(0.1, 0.9, proj[i], transform=ax.transAxes, fontsize=20, fontweight='bold', ha='center', va='center')
            
    fig.show()
    return 1

    