# Last modified by @recannon 10/01/2026

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .utils import time_astropy2shape

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