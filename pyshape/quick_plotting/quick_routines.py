#Last modified 12/09/2025

from astropy.stats import sigma_clip
import matplotlib.pyplot as plt
import numpy as np

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

