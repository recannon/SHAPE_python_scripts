#Last modified by @recannon 07/01/2026

from astropy.stats import sigma_clip
import matplotlib.pyplot as plt
import numpy as np
import cmasher as cmr

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