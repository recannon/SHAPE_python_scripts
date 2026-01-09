#Last modified by @recannon 07/01/2026

#Designed slightly counter intuitively to align with Agatas matlab script,
#And to work with convex inversion (don't want the function to take my dataclass objects)

from pyshape import artificial_lightcurves
from pyshape.mod.mod_io import modFile
from pyshape.io_utils import logger
from pyshape import artificial_lightcurves
from pathlib import Path
import logging

logger.setLevel(logging.INFO)

target = '2000rs11'
iden = 'Brauer_SP'

lc_filename  = Path(f"/cephfs/rcannon/{target}/lightcurves/{target}.lc.txt")
mod_filename = Path(f"/home/rcannon/Code/Radar/SHAPE/{target}/Brauer_Fit_Checks/modfiles/SP.mod")

#Requires figures to be in the same directory as python_scripts
base_dir = Path(__file__).resolve().parent
out_path = base_dir / ".." / "figures" / target / f"M_{iden}"
out_path = out_path.resolve()
out_path.mkdir(parents=True, exist_ok=True)

#Read modfile for spin state, scattering laws, and shape
mod_info = modFile.from_file(mod_filename)
mod_vx = mod_info.components[0]
V,F,FN,FNa = mod_vx.vertices, mod_vx.facets, mod_vx.FN, mod_vx.FNa
mod_ss = mod_info.spinstate
t0,P = mod_ss.t0.jd, mod_ss.P
lam,bet,phi = mod_ss.lam, mod_ss.bet, mod_ss.phi+90

#Assume there is only one scattering law
#Though test for if it exists (This is more likely than 2)
try:
    mod_ol = mod_info.phot_functions[1][0]
except (KeyError, IndexError):
    raise RuntimeError("No optical scattering law found in mod file")
scattering_law = mod_ol.type
scattering_params = mod_ol.values_to_dict()

#Create plots and output results dictionary (not done)
results = artificial_lightcurves.pub_lightcurve_generator(out_path,lc_filename,t0,lam,bet,phi,P,FN,FNa,V=V,F=F,shadowing=True,plot=True,show_plot=False)

#Combine the figures
artificial_lightcurves.concat_lc_plots(out_path,out_path.parent,f'{iden}_ArtLCs')