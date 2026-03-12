#Last modified by @recannon 07/01/2026

from astropy.stats import sigma_clip
import matplotlib.pyplot as plt
import numpy as np
import cmasher as cmr

def quick_lightcurves(fit_files,no_cols=3,show=True,save=False):
    
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

def quick_doppler(fit_files,no_cols=2,sigma_threshold=5,show=True,save=False):

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
        
        signal_thresh = sigma_threshold * sigma_clip(obs_data, sigma=4, maxiters=1).std()
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

#Create figure and plot
def quick_gridscan(p1_arr, p2_arr, chi_arr,
                   p1_grid, p2_grid, chi_grid,
                   minchi, maxlevel, cmp, lines=None,
                   p1_label='p1', p2_label='p2',
                   p1_ticks=None, p2_ticks=None,
                   save=False, show=False):

    fig, ax = plt.subplots(figsize=(12, 6))
    col_contours = np.arange(minchi, (minchi*maxlevel),
                             ((minchi*maxlevel) - minchi) / 20)
    
    ax.plot(p1_arr, p2_arr, 'g.', alpha=1, markersize=1)
    cf = ax.contourf(p1_grid, p2_grid, chi_grid, cmap=cmp, levels=col_contours)
    
    if lines:
        lin_contours = np.min(chi_arr) * (1 + (np.array(lines) / 100))
        ax.contour(p1_grid, p2_grid, chi_grid, levels=lin_contours,
                   colors='deepskyblue', linestyles=['-', '--', ':'])

    cbar = fig.colorbar(cf, ax=ax)
    cbar.set_label("Objective Function", fontsize=14)

    if p1_ticks is not None:
        ax.set_xticks(p1_ticks)
    if p2_ticks is not None:
        ax.set_yticks(p2_ticks)

    ax.set_xlabel(p1_label, fontsize=20)
    ax.set_ylabel(p2_label, fontsize=20)
    ax.set_xlim(np.min(p1_arr), np.max(p1_arr))
    ax.set_ylim(np.min(p2_arr), np.max(p2_arr))
    ax.set_title(f'({p1_arr[np.nanargmin(chi_arr)]}, {p2_arr[np.nanargmin(chi_arr)]}) : {minchi}', fontsize=30)

    if save:
        fig.savefig(save)
    if show:
        fig.show()