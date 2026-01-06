#Last modified by @recannon 06/01/2026

import numpy as np
import matplotlib.pyplot as plt
from astropy.time import Time
from ..io_utils import logger

# Colorblind-friendly colors
CBblue  = np.array([68, 119, 170]) / 255
CBred   = np.array([238, 102, 119]) / 255
CBgreen = np.array([34, 136, 51]) / 255
CBgrey  = np.array([187, 187, 187]) / 255

def plot_lc_fit(art_lc_data,lc_data,solar_phase_angle,aspect_angle,i,out_path,show_plot=True):
    
    logger.info(f'Plotting lightcurve {i}')

    lc_start = Time(lc_data[0,0],format='jd')
    lc_start_jd   = lc_start.jd
    lc_start_date = lc_start.isot.split('T')[0]

    ymax = np.max(art_lc_data[:,3])
    ymin = np.min(art_lc_data[:,3])

    art_plot_data = art_lc_data[art_lc_data[:, 1].argsort()]
    mag_shift = (np.max(art_plot_data[:,3]) + np.min(art_plot_data[:,3])) / 2

    fig, ax = plt.subplots(dpi=300)
    fig.set_figheight(7)
    fig.set_figwidth(8.3)

    #Artificial lightcurve
    ax.plot(art_plot_data[:, 1], art_plot_data[:, 3]-mag_shift, '-', color='black', lw=0.8)

    #Observed data
    ax.plot(lc_data[:,10], lc_data[:,9]-mag_shift, 'o', color=CBred)
    
    #Text
    text_size = 19
    title_size = 25
    label_size = 25
    ax.text(0.03,0.90,f"Phase Angle = {np.degrees(np.mean(solar_phase_angle)):.2f}$^o$",fontsize=text_size)
    ax.text(0.5+0.03,0.90,f"Aspect Angle = {np.degrees(np.mean(aspect_angle)):.1f}$^o$",fontsize=text_size)
    ax.text(0.03,-0.85,f"Model Peak-to-peak = {ymax-ymin:.2f}$^{{m}}$",fontsize=text_size)
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
    fig_name =f'{out_path}/test_ASF_{i:0>2}_fix.pdf'
    
    plt.tight_layout()
    plt.savefig(fig_name)
    logger.info(f'Saved figure to {fig_name}')

    if show_plot:
        plt.show()
    plt.close()

    logger.debug('Done')
    return 1
