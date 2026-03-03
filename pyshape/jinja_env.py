# Last modified by @recannon 10/01/2026

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .utils import time_astropy2shape
import subprocess
from .cli_config import logger

#Paths
script_dir = Path(__file__).resolve().parent
templates_dir = script_dir / "templates"
mod_templates   = templates_dir / "mod"
tex_templates = templates_dir / "latex"

template_env = Environment(
    loader=FileSystemLoader([
        mod_templates,
        tex_templates,
    ]),
    trim_blocks=True,
    lstrip_blocks=True,
)

template_env.filters["fmt"] = format
template_env.globals.update(
    zip=zip,
    enumerate=enumerate,
    cnvrt_time=time_astropy2shape,
)

#===Making pdf with tex===
def render_and_compile_pdf(template_name: str, render_kwargs: dict,
                             out_stem: str, work_dir: Path, dest_dir: Path) -> Path:
    """Render a Jinja template, compile with pdflatex, and move the result."""
    template = template_env.get_template(template_name)
    tex_file = work_dir / f'{out_stem}.tex'
    tex_file.write_text(template.render(**render_kwargs))

    subprocess.run(["pdflatex", tex_file.name],
                   cwd=work_dir, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    out_pdf = work_dir / f'{out_stem}.pdf'
    destination = dest_dir / out_pdf.name
    out_pdf.replace(destination)
    logger.info(f'Moved final pdf to {destination}')  # also fixes the logging bug
    return destination