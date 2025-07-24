from ..outfmt import logger
import numpy as np
import matplotlib.pyplot as plt
from astropy.time import Time

def plot_lc_fit(art_lc_data,lc_data,x,phase_angle,aspect_angle,i,no_rotations,out_path,show_plot=True):
    '''
    Produces figure of artificial lightcurve and selected scattering functions

    Inputs:
        - artificial_lc : [List] [2-D array] The artificial lightcurve information in 8 columns.
                            - t-T0        : Time since T0 (in days)
                            - plotphase   : Rotation phase as a fraction of full rotation (accounting for YORP)
                            - SL_illum    : Magnitude calculated using Lambertian scattering, centred around 0
                            - SLS_illum   : Magnitude calculated using Lommel-Seelinger scattering, centred around 0
                            - SLLS_illum  : Magnitude calculated using a combination of L and LS, centred around 0
                            - Hapke_illum : Magnitude calculated using Hapke scattering, centred around 0
                            - phases *    : Rotation phase as a fraction of full rotation (not accounting for YORP) -> Something wrong with these.
                            - lc_no       : Number of the lightcurve
        - lc_data       : [List] [2-D array] Observed lightcurve data with 11 columns
                            - JD       : jd time of observation
                            - Flux     : Intensity of flux
                            - Sx,Sy,Sz : Sun vectors for the asteroid (3 columns)
                            - Ex,Ey,Ez : Earth vectors for the asteroid (3 columns)
                            - Mag Unc  : Uncertainty in the magnitudes. Assumed as 0.01mag if not provided
                            - Mag      : Magnitude values, calculated from the flux column
                            - Phase    : Rotation phase as a fraction of full rotation (accounting for YORP)
        - x             : [List] of flags used to indicate which scattering model(s) to plot.
                          The first value of the list will be the model to which the observed data is scaled to.
                          The first value of the list will be plotted in a black solid line.
                          If not the primary, they shall be plotted as such:
                            - 2 : Lambertian (Dotted blue line)
                            - 3 : Lommel-Seelinger (Dashed green line)
                            - 4 for a combination of Lommel-Seelinger + omega * Lambertian (continuous red line)
                            - 5 for Hapke (dashed grey line)
          - phase_angle : [List] [Float] The mean phase angle in degrees for the lightcurve
                               (angle between positions of Earth and Sun as seen from the asteroid)
          - aspect_angle: [List] [Float] The mean aspect angle in degrees for the lightcurve 
                               (angle between pole orientation and direction to Earth)
          - i           : The number lightcurve that is being plotted
        - out_path  : file path of the directory for which individual lightcurve figures shall be saved
        - show_plot : Bool - If True outputs the figure as well       
        
    Outputs:
        - Figure: Saved to out_path
    '''

    logger.info(f'Plotting lightcurve {i}')

    # plt.rcParams["font.family"] = "sans-serif"  # Use a sans-serif font
    # plt.rcParams["font.sans-serif"] = ["ClearSans-Regular"]  # Default Matplotlib sans-serif font

    lc_start = Time(lc_data[0,0],format='jd')
    lc_start_jd   = lc_start.jd
    lc_start_date = lc_start.isot.split('T')[0]

    ymaxModel = np.array([np.max(art_lc_data[:,k]) for k in [2,3,4,7]])
    yminModel = np.array([np.min(art_lc_data[:,k]) for k in [2,3,4,7]])

    ymax = np.max(ymaxModel[x[0]-2])
    ymin = np.min(yminModel[x[0]-2])

    # Colorblind-friendly colors
    CBblue  = np.array([68, 119, 170]) / 255
    CBred   = np.array([238, 102, 119]) / 255
    CBgreen = np.array([34, 136, 51]) / 255
    CBgrey  = np.array([187, 187, 187]) / 255

    #Data is sorted by jd, if plotphase decreases it has looped (1->0)
    #We plot these separately so that there are no lines spanning the width of the plot
    art_lc_plot_group_ind = [0] + [i for i in range(1,len(art_lc_data[:,0]))
                                if art_lc_data[i,1]<art_lc_data[i-1,1]] + [None]
    
    fig, ax = plt.subplots(dpi=300)
    fig.set_figheight(7)
    fig.set_figwidth(8.3*no_rotations)
    for low_ind,high_ind in zip(art_lc_plot_group_ind[:-1],art_lc_plot_group_ind[1:]):
        plot_data = art_lc_data[low_ind:high_ind]
        for x_i in x:
            if x_i == 2:
                ax.plot(plot_data[:,1], plot_data[:,x_i], ':', color=CBblue, lw=0.8)
            elif x_i == 3:
                ax.plot(plot_data[:,1], plot_data[:,x_i], "--", color=CBgreen, lw=0.8)
            elif x_i == 4:
                ax.plot(plot_data[:,1], plot_data[:,x_i], "-", color=CBred, lw=0.8)
            elif x_i == 5:
                ax.plot(plot_data[:,1], plot_data[:,x_i], "--", color=CBgrey, lw=0.8)
        ax.plot(plot_data[:,1], plot_data[:,x[0]], 'k-', lw=0.8)
    ax.plot(lc_data[:,10], lc_data[:,9], 'o', color=CBred)

    #Text
    text_size = 19
    title_size = 25
    label_size = 25
    ax.text(0.03,0.90,f"Phase Angle = {np.degrees(np.mean(phase_angle)):.2f}$^o$",fontsize=text_size)
    ax.text(no_rotations*0.5+0.03,0.90,f"Aspect Angle = {np.mean(aspect_angle):.1f}$^o$",fontsize=text_size)
    ax.text(0.03,-0.85,f"Model Peak-to-peak = {ymax-ymin:.2f}$^{{m}}$",fontsize=text_size)
    ax.set_title(f'{i+1} $\\bullet$ {lc_start_date} $\\bullet {lc_start_jd:.3f}$ ',fontsize=title_size,pad=10)
    ax.set_xlabel('Rotational Phase',fontsize=label_size)

    #Format axes
    xticks = np.linspace(0,no_rotations,6)
    yticks = [-1, -0.5, 0, 0.5, 1]
    ax.set_xticks(xticks)  # Format with one decimal   
    ax.set_yticks(yticks)
    ax.set_xticklabels([f'{t:.1f}' for t in xticks])
    ax.set_yticklabels([f'{t:.1f}' for t in yticks])
    ax.set_xlim(0, no_rotations)
    ax.set_ylim(1, -1)
    ax.tick_params(direction='in', top=True, right=True, left=True, bottom=True, 
                width=0.75, length=6, labelsize=label_size, pad=10)
    for spine in ax.spines.values():
        spine.set_linewidth(0.75)

    #Save fig
    fig_name =f'{out_path}/ASF_{i+1:0>2}_fix_cncv.pdf'
    
    plt.tight_layout()
    plt.savefig(fig_name)
    logger.info(f'Saved figure to {fig_name}')

    if show_plot:
        plt.show()
    plt.close()

    logger.debug('Done')
    return 1
