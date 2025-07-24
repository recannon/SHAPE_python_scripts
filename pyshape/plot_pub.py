#Last modified 14/05/2025

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from . import polescan

def pp_polescan(bet,lam,chi,target, cmp_array=None,cmp='magma',save=False):
    
    minchi = np.min(chi)
    betall,lamall,chiall = polescan.interpolate_chi(bet,lam,chi,betstep=1,lamstep=1)

    if cmp_array==None:
        cmp_array = np.linspace(minchi, 2*minchi, 10)

    orthproj = {'N' : [  0, 90],
                'S' : [  0,-90]}

    meridians = [225, 270, 315, 360, 0,  45,  90, 135, 180]
    parallels = np.arange(-90, 91, 30)

    fig = plt.figure(figsize=[3.37689*2,3.37689*9/8*2])
    ax1 = plt.subplot2grid(shape=(2, 2), loc=(0, 0), colspan=1)
    ax2 = plt.subplot2grid(shape=(2, 2), loc=(0, 1), colspan=1)
    ax3 = plt.subplot2grid(shape=(2, 2), loc=(1, 0), colspan=2)
    axs = [ax1, ax2, ax3]

    #Mollweide projection
    moll = Basemap(projection='moll', lon_0=0.5, resolution='l', ax=axs[2])
    cf = moll.contourf(lamall, betall, chiall, levels=cmp_array, cmap=cmp, latlon=True)
    moll.drawparallels(parallels, labels=[1, 1, 1, 1], labelstyle="+/-", xoffset=-1800, color='darkgreen',textcolor='darkgreen',fontsize=16)
    moll.drawmeridians(meridians, color='blue')
    for mer in [270, 0, 90]:
        # if mer == 180 or mer == 360:
        #     continue
        axs[2].annotate(str(mer),xy=moll(mer,0),xycoords='data',fontsize=16,color='blue')

    cbar = moll.colorbar(cf,ax=axs[2], aspect=40, location='bottom')
    cbar.ax.tick_params(labelsize=12)
    cbar.set_label('Reduced chi-squared', rotation=0, fontsize=16, labelpad=10)

    #Orthographic projections
    for ax, proj in zip(axs[:-1], orthproj):
        orth = Basemap(projection='ortho', lon_0=orthproj[proj][0], lat_0=orthproj[proj][1], resolution='l', ax=ax)
        orth.contourf(lamall, betall, chiall, levels=cmp_array, cmap=cmp, latlon=True)
        orth.drawparallels(parallels, color='darkgreen')
        orth.drawmeridians(meridians, color='blue')
        ax.text(0.1, 0.9, proj, transform=ax.transAxes, fontsize=20, fontweight='bold', ha='center', va='center')

        for mer in [270, 0, 90, 180]:
            if mer == 360:
                continue
            ax.annotate(str(mer),xy=orth(mer,0),xycoords='data',fontsize=16,color='blue')
            
        for par in [-90,-60,-30,30,60,90]:
            ax.annotate(str(par),xy=orth(120,par),xycoords='data',fontsize=16,color='darkgreen')

    for ax in axs:
        ax.xaxis.set_ticks_position('both')
        ax.xaxis.set_tick_params(direction='in', labelsize=12)
        ax.yaxis.set_ticks_position('both')
        ax.yaxis.set_tick_params(direction='in', labelsize=12)

    fig.tight_layout()
    if save:
        fig.savefig(f'./figures/{target}/Pub_radar_{target}_scan.pdf')
    plt.show()
    plt.close()


import cartopy.crs as ccrs

def pp_polescan(bet,lam,chi,target, cmp_array=None,cmp='magma',save=False):
    
    minchi = np.min(chi)
    betall,lamall,chiall = polescan.interpolate_chi(bet,lam,chi,betstep=1,lamstep=1)

    if cmp_array==None:
        cmp_array = np.linspace(minchi, 2*minchi, 10)

    