#Last modified @recannon 20261028

from astropy.stats import sigma_clip
import matplotlib.pyplot as plt
import numpy as np
import cmasher as cmr

# Colorblind-friendly colors
CBblue  = np.array([68, 119, 170]) / 255
CBred   = np.array([238, 102, 119]) / 255
CBgreen = np.array([34, 136, 51]) / 255
CBgrey  = np.array([187, 187, 187]) / 255

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


def pub_doppler(fit_file,dop_info,fig_title,sigma_threshold=5,show=True,save=False):

    # Plot sizes (for fitting 4 to a row, that keeps nice font sizes)
    FIG_HEIGHT = 7
    FIG_WIDHT  = 8.3

    text_size = 30
    title_size = 30
    label_size = 30

    #x axis ticks
    com_idx = int(dop_info[2]) - 1
    bins = np.arange(dop_info[0])
    freq = (bins - com_idx) * dop_info[1]

    fig, ax = plt.subplots(dpi=300)
    fig.set_figheight(FIG_HEIGHT)
    fig.set_figwidth(FIG_WIDHT)
    
    _, obs_data, fit_data, res = np.loadtxt(fit_file,unpack=True)

    ax.plot(freq, obs_data, 'o', color=CBred)
    ax.plot(freq, fit_data, '-', color='black', lw=0.8)
    ax.set_title(fig_title, fontsize=title_size)
    
    signal_thresh = sigma_threshold * sigma_clip(obs_data, sigma=4, maxiters=1).std()
    signal_mask = obs_data > signal_thresh

    if np.any(signal_mask):
        signal_freq = freq[signal_mask]
        min_freq = signal_freq.min()
        max_freq = signal_freq.max()
        margin = 10 * dop_info[1] #10 bins
        ax.set_xlim(min_freq - margin, max_freq + margin)
    else:
        ax.set_xlim(freq[0], freq[-1])  #plots everything if no signal

    ax.tick_params(direction='in', top=True, right=True, left=True, bottom=True, 
                    width=0.75, length=6, labelsize=label_size, pad=10)
    ax.set_xlabel('Doppler freq. [Hz]',fontsize=label_size, labelpad=0)
    ax.set_ylabel("Echo Power [St'd devs]", fontsize=label_size, labelpad=0)

    for spine in ax.spines.values():
        spine.set_linewidth(0.75)

    fig.tight_layout()

    if save:
        fig.savefig(save)
    if show:
        plt.show()

    plt.close(fig)

    return 1
