#Last modified 14/05/2025

import matplotlib.pyplot as plt
import numpy as np
from . import polescan
from astropy.stats import sigma_clip
from .outfmt import logger

def pq_polescan(bet,lam,chi, maxlevel=1.5,betstep=1,lamstep=1,lines=[],cmp='magma',save=False,show=True):

    #Create 1x1 meshgrid of poles
    betall,lamall,chiall = polescan.interpolate_chi(bet,lam,chi,betstep,lamstep)

    minchi = np.nanmin(chiall)
    logger.debug(f'Minimum chisqr is {minchi}')

    fig, ax = plt.subplots(figsize=(12, 6))
    col_contours = np.arange(minchi, minchi * maxlevel,
                            (minchi * maxlevel - minchi) / 15)

    #Poles scanned
    ax.plot(lam, bet, 'k.', alpha=0.5, markersize=1)
    #Interpolated colour map
    cf = ax.contourf(lamall, betall, chiall, levels=col_contours, cmap=cmp)
    #Optional line contours
    if lines:
        lin_contours = np.min(chi) * (1 + (np.array(lines) / 100))
        ax.contour(lamall, betall, chiall, colors='deepskyblue', 
                   linestyles=['solid', 'dashed', 'dotted'],
                   levels=lin_contours, linewidths=1)
    #Minimum chisqr
    ax.plot(lam[np.nanargmin(chi)], bet[np.nanargmin(chi)], 'cd')

    ax.tick_params(axis='both', which='major', labelsize=18)
    ax.set_xticks(np.arange(0, 361, 60))
    ax.set_yticks(np.arange(-90, 91, 30))
    ax.set_xlabel("Longitude", fontsize=20)
    ax.set_ylabel("Latitude", fontsize=20)
    ax.set_xlim(np.min(lam), np.max(lam))
    ax.set_ylim(np.min(bet), np.max(bet))
    ax.set_title(f'({bet[np.nanargmin(chi)]}, {lam[np.nanargmin(chi)]}) : {minchi}', fontsize=30)

    cbar = fig.colorbar(cf, ax=ax)
    cbar.ax.tick_params(labelsize=16, labelleft=True,
                        labelright=False, left=True, right=False)
    cbar.set_label('Reduced chi-squared', rotation=270, fontsize=18, labelpad=20)
    if show:
        logger.debug(f'Displaying polescan')
        plt.show()
    if save:
        logger.debug(f'Saving polescan to {save}')
        plt.savefig(save)
    plt.close()

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

