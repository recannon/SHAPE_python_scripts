#Last modified by @recannon 06/01/2026

import subprocess
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

target     = '2000rs11'
no         = '1'
fig_path   = Path(f'/home/rcannon/Code/Radar/SHAPE/figures/{target}')
model_dir  = Path(f'{fig_path}/M{no}')
noLCs = 8
no_col = 4

templates_dir = '/home/rcannon/Code/Radar/SHAPE/python_scripts/pyshape/templates/latex'
env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=False   # IMPORTANT for LaTeX
)
template = env.get_template("concat_lc_plots.tex.j2")

n_lightcurves = 8
lightcurves = list(range(1, n_lightcurves + 1))

latex = template.render(lightcurves=lightcurves)
out_tex = model_dir / "Artificial_LC_Plots.tex"
out_tex.write_text(latex)

out_pdf = model_dir / "Artificial_LC_Plots.pdf"
subprocess.run(["pdflatex", f"-output-directory={model_dir}", out_tex.name],
               cwd=model_dir, check=True)

out_pdf = model_dir / "Artificial_LC_Plots.pdf"
destination = fig_path / out_pdf.name
out_pdf.replace(destination)