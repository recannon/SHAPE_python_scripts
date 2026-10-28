#Last modified by @recannon 20261027

#20261027 - General tidy up

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from astropy.time import Time
from astropy.stats import sigma_clip
from ..cli.config import logger
from .model.plot_model_projection import plot_model_projection

# Colorblind-friendly colors
CBblue  = np.array([68, 119, 170]) / 255
CBred   = np.array([238, 102, 119]) / 255
CBgreen = np.array([34, 136, 51]) / 255
CBgrey  = np.array([187, 187, 187]) / 255

# Plot sizes (for fitting 4 to a row, that keeps nice font sizes)
FIG_HEIGHT = 7
FIG_WIDHT  = 8.3

#x_label, y_label, invert_x, invert_y
VIEW_AXES = {
    "+Z": ("X", "Y", False, False),
    "-Z": ("X", "Y", False, True),
    "+Y": ("X", "Z", True,  False),
    "-Y": ("X", "Z", False, False),
    "+X": ("Y", "Z", False, False),
    "-X": ("Y", "Z", True,  False),
}

def pub_model(vertices,facets,normals,
              out_stem,
              red_list=None,yellow_list=None,
              lims = 0.6, ticks=0.5, titlesize=35, labelsize=30):
    
    views = ['+Z', '+Y', '+X', '-Z', '-Y', '-X']

    # plt.rcParams.update({'font.size': 30})
    with plt.rc_context({"font.size": 30}):
        fig, axes = plt.subplots(2, 3, figsize=(30, 16))
        
        for ax, view in zip(axes.flatten(), views):
            
            #Create and plot model projection
            ax = plot_model_projection(vertices,facets,normals,
                                    ax,view,
                                    red_list=red_list,yellow_list=yellow_list)
        
            #Then tick formatting!
            ax.tick_params(direction='in')
            ax.set_xlim(-lims,lims)
            ax.set_ylim(-lims,lims)
            ax.set_aspect('equal')
            ax.spines[['right', 'top']].set_visible(False)
            ax.set_title(rf'$\bf {view} $', fontsize=titlesize)
            ax.xaxis.set_major_formatter(FormatStrFormatter('%g'))
            ax.yaxis.set_major_formatter(FormatStrFormatter('%g'))
            ax.set_xticks([-ticks, 0.0, ticks])
            ax.set_yticks([-ticks, 0.0, ticks])
            ax.grid(True, which='major', linewidth=0.8, alpha=0.6)
            ax.spines['left'].set_linewidth(2.5)
            ax.spines['bottom'].set_linewidth(2.5)
            
            #Format axes
            xl, yl, inv_x, inv_y = VIEW_AXES[view]
            ax.set_xlabel(f"{xl} [km]", fontsize=labelsize)
            ax.set_ylabel(f"{yl} [km]", fontsize=labelsize)
            if inv_x: ax.invert_xaxis()
            if inv_y: ax.invert_yaxis()
                    
        fig.tight_layout()
        fig.savefig(f'{out_stem}.pdf', bbox_inches='tight', dpi=300)
        plt.close(fig)