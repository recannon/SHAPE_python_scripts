
import glob
import subprocess
from string import Template

target     = '2000rs11'
no         = '1'
fig_path   = f'/home/rcannon/Code/Radar/SHAPE/figures/{target}'
model_dir  = f'{fig_path}/M{no}'
noLCs = 8
no_col = 4

#Define template for latex file
template_start = Template('''
\\documentclass{article}
\\usepackage[varg]{txfonts}
\\usepackage{graphicx}
\\usepackage{geometry}
\\geometry{left=0.2in, right=0.2in, top=0in, bottom=0in}
\\newcommand{\includelc}[1]{
\\includegraphics[trim=0cm 0cm 0cm 0cm, clip=true]{ $model } }
\\begin{document}
\\begin{figure*}[tbp]
''')

template_end = f'''}}
\\end{{figure*}}
\\end{{document}}'''

print(model_dir)
model_name = model_dir.split('/')[-1]
lightcurve_pdfs = sorted(glob.glob(f'{model_dir}/*fix.pdf'))
out_core = f'{model_name}_Artificial_LC_Plots'

# latex_start = template_start.safe_substitute(model=f'{target}_M{j+1}py_ASF_#1.pdf')
latex_start = template_start.safe_substitute(model=f'test_ASF_#1_fix.pdf')

latex_end   = template_end

latex_cmd = f'\\resizebox{{\\hsize}}{{!}}{{'
for i,lightcurve_pdf in enumerate(lightcurve_pdfs):
    latex_cmd += f"   \\includelc{{{i+1:0>2}}}"
    if i == (no_col*6)-1:
        latex_cmd += f'''}}
\\end{{figure*}}
\\newpage
\\begin{{figure*}}[tbp]
\\resizebox{{\\hsize}}{{!}}{{'''
    elif i%no_col == no_col-1 and i != noLCs-1:
        latex_cmd += f'}}\n\\resizebox{{\\hsize}}{{!}}{{'
latex_fin = latex_start + latex_cmd + latex_end


latex_file = f'{model_dir}/{out_core}.tex'
f_latex = open(latex_file,'w')
print(f'Saved {latex_file} from {model_name} plots')
f_latex.write(latex_fin)
f_latex.close()

print("")

subprocess.check_output([f'pdflatex -output-directory={model_dir} {model_dir}/{out_core}.tex'], shell=True)

master_pdfs = glob.glob(f'{fig_path}/M{no}/{target}_M{no}.pdf')

subprocess.check_output(f'mv -f {" ".join(master_pdfs)} {fig_path}', shell=True)