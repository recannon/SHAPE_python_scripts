#Last modified by @recannon 09/01/2026

import numpy as np
import matplotlib.pyplot as plt
from astropy.time import Time
from ..io_utils import logger
from astropy.stats import sigma_clip

# Colorblind-friendly colors
CBblue  = np.array([68, 119, 170]) / 255
CBred   = np.array([238, 102, 119]) / 255
CBgreen = np.array([34, 136, 51]) / 255
CBgrey  = np.array([187, 187, 187]) / 255

# Plot sizes (for fitting 4 to a row, that keeps nice font sizes)
FIG_HEIGHT = 7
FIG_WIDHT  = 8.3

def pub_lightcurves(art_lc_data,lc_data,solar_phase_angle,aspect_angle,i,out_path,show_plot=True):
    
    logger.info(f'Plotting lightcurve {i}')

    lc_start = Time(lc_data[0,0],format='jd')
    lc_start_jd   = lc_start.jd
    lc_start_date = lc_start.isot.split('T')[0]

    ymax = np.max(art_lc_data[:,3])
    ymin = np.min(art_lc_data[:,3])

    art_plot_data = art_lc_data[art_lc_data[:, 1].argsort()]
    mag_shift = (np.max(art_plot_data[:,3]) + np.min(art_plot_data[:,3])) / 2

    fig, ax = plt.subplots(dpi=300)
    fig.set_figheight(FIG_HEIGHT)
    fig.set_figwidth(FIG_WIDHT)

    #Artificial lightcurve
    ax.plot(art_plot_data[:, 1], art_plot_data[:, 3]-mag_shift, '-', color='black', lw=0.8)

    #Observed data
    ax.plot(lc_data[:,10], lc_data[:,9]-mag_shift, 'o', color=CBred)
    
    #Text
    text_size = 30
    title_size = 30
    label_size = 30
    ax.text(0.03,0.90,rf"$\alpha$ = {np.degrees(np.mean(solar_phase_angle)):.2f}$^o$",fontsize=text_size)
    ax.text(0.5+0.03,0.90,f"Aspect = {np.degrees(np.mean(aspect_angle)):.1f}$^o$",fontsize=text_size)
    ax.text(0.03,-0.80,rf"$\Delta m$ = {ymax-ymin:.2f}",fontsize=text_size)
    ax.set_title(f'{i} $\\bullet$ {lc_start_date} $\\bullet {lc_start_jd:.3f}$ ',fontsize=title_size,pad=10)
    ax.set_xlabel('Rotational Phase',fontsize=label_size)

    #Format axes
    xticks = np.linspace(0,1,6)
    yticks = [-1, -0.5, 0, 0.5, 1]
    ax.set_xticks(xticks)  # Format with one decimal   
    ax.set_yticks(yticks)
    ax.set_xticklabels([f'{t:g}' for t in xticks])
    ax.set_yticklabels([f'{t:g}' for t in yticks])
    ax.set_xlim(0, 1)
    ax.set_ylim(1, -1)
    ax.tick_params(direction='in', top=True, right=True, left=True, bottom=True, 
                width=0.75, length=6, labelsize=label_size, pad=10)
    for spine in ax.spines.values():
        spine.set_linewidth(0.75)

    #Save fig
    fig_name =f'{out_path}/ArtLC_{i:0>2}_fix.pdf'
    
    plt.tight_layout()
    plt.savefig(fig_name)
    logger.info(f'Saved figure to {fig_name}')

    if show_plot:
        plt.show()
    plt.close()

    logger.debug('Done')
    return 1

def pub_doppler(fit_file,fig_title,sigma_threshold=5,show=True,save=False):

    text_size = 30
    title_size = 30
    label_size = 30

    fig, ax = plt.subplots(dpi=300)
    fig.set_figheight(FIG_HEIGHT)
    fig.set_figwidth(FIG_WIDHT)
    
    bins, obs_data, fit_data, res = np.loadtxt(fit_file,unpack=True)

    ax.plot(bins, obs_data, 'o', color=CBred)
    ax.plot(bins, fit_data, '-', color='black', lw=0.8)
    ax.set_title(fig_title, fontsize=title_size)
    
    signal_thresh = sigma_threshold * sigma_clip(obs_data, sigma=4, maxiters=1).std()
    signal_mask = obs_data > signal_thresh

    if np.any(signal_mask):
        signal_bins = bins[signal_mask]
        min_bin = signal_bins.min()
        max_bin = signal_bins.max()
        margin = 10
        ax.set_xlim(min_bin - margin, max_bin + margin)
    else:
        ax.set_xlim(bins[0], bins[-1])  #plots everything if no signal

    ax.tick_params(direction='in', top=True, right=True, left=True, bottom=True, 
                    width=0.75, length=6, labelsize=label_size, pad=10)
    for spine in ax.spines.values():
        spine.set_linewidth(0.75)

    plt.tight_layout()

    if show:
        plt.show()
    if save:
        plt.savefig(save)

    plt.close(fig)

    return 1
