from pyshape.outfmt import console,logger
import numpy as np
from pyshape import mod_file, convinv, utils
import pyshape.plotting_utils as plot_utils

target = '2000rs11'
target_h='2000 RS11'
f_mod = f'/home/rcannon/Code/Radar/{target}/v04/v500/modfiles/lat-80lon270.mod'
f_lc  = f'/cephfs/rcannon/{target}/lightcurves/{target}.lc.txt'

# target = '2024on'
# target_h = '2024 ON'
# f_mod = '/home/rcannon/Code/Radar/2024on/init_ps/test.v.mod'
# f_lc  = f'/cephfs/rcannon/{target}/lightcurves/{target}.lc.txt'

concave = True
iden = 'test'
#x is given as a list, 3: LommelSeelinger, 2: Lambert, 4: Combination, 5: Hapke. 
#First value in list is plotted in a black line and has observed data scaled to fit it.
x = [3,4,5]

def test_plot():
    
    mod_info  = mod_file.read(f_mod)

    if len(mod_info.components) != 1 or mod_info.components[0].type != 'vertex':
        raise TypeError('Can only create artificial lightcurves for single component vertex models')

    t0  = mod_info.spin_state.t0.jd
    lam = mod_info.spin_state.lam
    bet = mod_info.spin_state.bet
    P   = mod_info.spin_state.P

    V = mod_info.components[0].vertices
    F = mod_info.components[0].facets
    FN  = mod_info.components[0].FN
    FNa = mod_info.components[0].FNa

    out_path = f'../figures/{target}/M_{iden}' #For figures

    results = plot_utils.lightcurve_generator(V,F,FN,FNa,f_lc,t0,lam,bet,P,x,out_path,0,target_h=target_h,concave=concave,plot=True,show_plot=False)

    # print(mod_info.components[0].FNa)

    # print(mod_info.components[0].FN, mod_info.components[0].FNa)

    return 1

def main():
    test_plot()
    return 1

if __name__ == "__main__":
    main()

