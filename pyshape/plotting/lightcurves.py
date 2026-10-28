#Last modified @recannon 20261028

from astropy.stats import sigma_clip
import matplotlib.pyplot as plt
import numpy as np
import cmasher as cmr
from ..cli.config import logger
from matplotlib.ticker import FormatStrFormatter
from astropy.time import Time
from pathlib import Path

# Colorblind-friendly colors
CBblue  = np.array([68, 119, 170]) / 255
CBred   = np.array([238, 102, 119]) / 255
CBgreen = np.array([34, 136, 51]) / 255
CBgrey  = np.array([187, 187, 187]) / 255

# Plot sizes (for fitting 4 to a row, that keeps nice font sizes)
FIG_HEIGHT = 7
FIG_WIDHT  = 8.3

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

    fig.tight_layout()

    if save:
        fig.savefig(save)
    if show:
        plt.show()

    plt.close(fig)

    return 1


def pub_lightcurves(art_lc_data,lc_data,solar_phase_angle,aspect_angle,i,out_path,show_plot=True):
    '''
    Produces a plot of an artificial lightcurve and the observed data for a single lightcurve
    ./artificial_lightcurves/pub_lightcurve_generator.py for details on how input arrays are constructed
    '''
    
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
    ax.text(0.45+0.03,0.90,f"Aspect = {np.degrees(np.mean(aspect_angle)):.1f}$^o$",fontsize=text_size)
    ax.text(0.03,-0.80,rf"$\Delta m$ = {ymax-ymin:.2f}",fontsize=text_size)
    ax.set_title(f'{i} $\\bullet$ {lc_start_date} $\\bullet {lc_start_jd:.3f}$ ',fontsize=title_size,pad=10)
    ax.set_xlabel('Rot. Phase',fontsize=label_size, labelpad=0)
    ax.set_ylabel('Rel. Mag', fontsize=label_size, labelpad=-10)

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
    
    fig.tight_layout()
    fig.savefig(fig_name)
    logger.info(f'Saved figure to {fig_name}')

    if show_plot:
        plt.show()
    plt.close(fig)

    logger.debug('Done')
    return 1