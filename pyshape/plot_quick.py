#Last modified 14/05/2025

import matplotlib.pyplot as plt
import numpy as np
from . import polescan
from astropy.stats import sigma_clip
from .outfmt import logger
import matplotlib.tri as tri


def pq_polescan(bet:np.array, lam:np.array, chi:np.array,
                maxlevel:float=1.5, nside:int=32, lines:list=[],
                cmp:str='magma', save:str=None, show:bool=True):
    
    pole_mask = np.logical_or(bet==90, bet==-90)

    lon_plot,lat_plot,chi_plot = polescan.interpolate_chi(bet,lam,chi,nside)
    coords_plot = tri.Triangulation(lon_plot, lat_plot)

    minchi = chi_plot.min()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    col_contours = np.arange(minchi, minchi * maxlevel,
                            (minchi * maxlevel - minchi) / 15)
    ax.plot(lam,bet,'g.',alpha=1,markersize=1)
    cf = ax.tricontourf(coords_plot, chi_plot, cmap="cmr.sunburst", levels=col_contours)
    if lines:
        lin_contours = np.min(chi) * (1 + (np.array(lines) / 100))
        cl = ax.tricontour(coords_plot, chi_plot, levels=lin_contours,
                    colors='deepskyblue', linestyles=['-','--',':'])

    # add colorbar linked to the contour plot
    cbar = fig.colorbar(cf, ax=ax)
    cbar.set_label("Chi value", fontsize=14)   # optional label
        
    ax.set_xticks(np.arange(0, 361, 60))
    ax.set_yticks(np.arange(-90, 91, 30))
    ax.set_xlabel("Longitude", fontsize=20)
    ax.set_ylabel("Latitude", fontsize=20)
    ax.set_xlim(np.min(lam[~pole_mask]), np.max(lam[~pole_mask]))
    ax.set_ylim(np.min(bet), np.max(bet))
    ax.set_title(f'({bet[np.nanargmin(chi)]}, {lam[np.nanargmin(chi)]}) : {minchi}', fontsize=30)

    if save:
        fig.savefig(save)

    fig.show()

    return 1

def pq_lightcurves(fit_files,no_cols=3,show=True,save=False):
    
    # A4 size in inches: 11.7 x 8.3 (landscape)
    A4_WIDTH = 11.7
    SUBPLOT_HEIGHT = 2.5  # You can adjust this per-row height

    n_plots = len(fit_files)
    n_rows = n_plots // no_cols + int(n_plots % no_cols != 0)
    fig_height = n_rows * SUBPLOT_HEIGHT

    fig, axs = plt.subplots(n_rows, no_cols, figsize=(A4_WIDTH, fig_height))
    axs = axs.flatten()

    for i in range(n_plots):
        d_jd, d_mag,p_mag,_,_ = np.loadtxt(fit_files[i],unpack=True)

        axs[i].plot(d_jd, d_mag, 'ro')
        axs[i].plot(d_jd, p_mag, 'k-')
        axs[i].set_title(f'{str(fit_files[i]).split("_")[-1]}')
        axs[i].invert_yaxis()

    #Hide unused plots
    for j in range(n_plots, len(axs)):
        fig.delaxes(axs[j])

    plt.tight_layout()

    if show:
        plt.show()
    if save:
        plt.savefig(save)

    plt.close(fig)

    return 1

def pq_doppler(fit_files,no_cols=2,sigma_threshold=5,show=True,save=False):

    # A4 size in inches: 11.7 x 8.3 (landscape)
    A4_WIDTH = 11.7
    SUBPLOT_HEIGHT = 2.5  # You can adjust this per-row height

    n_plots = len(fit_files)
    n_rows = n_plots // no_cols + int(n_plots % no_cols != 0)
    fig_height = n_rows * SUBPLOT_HEIGHT

    fig, axs = plt.subplots(n_rows, no_cols, figsize=(A4_WIDTH, fig_height))
    axs = axs.flatten()

    for i in range(n_plots):
        bins, obs_data, fit_data, res = np.loadtxt(fit_files[i],unpack=True)

        axs[i].plot(bins, obs_data, 'ro')
        axs[i].plot(bins, fit_data, 'k-')
        axs[i].set_title(f'{" ".join(str(fit_files[i]).split("_")[-2:])}')
        
        signal_thresh = sigma_threshold * sigma_clip(obs_data, sigma=3, maxiters=5).std()
        signal_mask = obs_data > signal_thresh

        if np.any(signal_mask):
            signal_bins = bins[signal_mask]
            min_bin = signal_bins.min()
            max_bin = signal_bins.max()
            
            margin = 10
            axs[i].set_xlim(min_bin - margin, max_bin + margin)
        else:
            axs[i].set_xlim(bins[0], bins[-1])  #plots everything if no signal
        

    #Hide unused plots
    for j in range(n_plots, len(axs)):
        fig.delaxes(axs[j])

    plt.tight_layout()

    if show:
        plt.show()
    if save:
        plt.savefig(save)

    plt.close(fig)

    return 1

