#Last modified 14/05/2025

import matplotlib.pyplot as plt
import numpy as np
from . import polescan
import glob

def pq_polescan(bet,lam,chi, maxlevel=1.5,betstep=1,lamstep=1,lines=[],cmp='magma'):

    #Create 1x1 meshgrid of poles
    betall,lamall,chiall = polescan.interpolate_chi(bet,lam,chi,betstep,lamstep)

    minchi = np.nanmin(chiall)
    print(minchi)

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
    ax.set_xlim(0, 360)
    ax.set_ylim(-90, 90)
    ax.set_title(f'({bet[np.nanargmin(chi)]}, {lam[np.nanargmin(chi)]}) : {minchi}', fontsize=30)

    cbar = fig.colorbar(cf, ax=ax)
    cbar.ax.tick_params(labelsize=16, labelleft=True,
                        labelright=False, left=True, right=False)
    cbar.set_label('Reduced chi-squared', rotation=270, fontsize=18, labelpad=20)

    plt.show()
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
        axs[i].set_title(f'{fit_files[i].split("_")[-1]}')
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

def pq_doppler(fit_files,no_cols=2,show=True,save=False):

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
        axs[i].set_title(f'{" ".join(fit_files[i].split("_")[-2:])}')
        if len(bins)>100:
            mid_bin = len(bins)//2 + int(len(bins)%2 != 0)
            axs[i].set_xlim(left=mid_bin-50,right=mid_bin+50)

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

