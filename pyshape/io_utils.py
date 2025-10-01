#Last modified 12/09/2025

import logging
from pathlib import Path
import sys
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

#===Helper functions for checking input arguments
def check_type(par,par_name,req_type):
    try:
        return req_type(par)
    except:
        error_exit(f"{par_name} must be of type {req_type.__name__} (got '{par}')")

def check_dir(path, must_exist=True):
    """Convert to Path and check it's a directory (if required)."""
    path = Path(path)
    if must_exist:
        if not path.exists():
            error_exit(f"Directory does not exist: {path}")
        if not path.is_dir():
            error_exit(f"Not a directory: {path}")
    return path


#===Clean exit functions===
def error_exit(message):
    logger.error(message)
    sys.exit(1)
    
def safe_exit(message=None):
    if message:
        logger.info(message)
    sys.exit(1)


#===Consistent logger and console===
custom_theme = Theme({
    "logging.level.info": "cyan",
    "logging.level.warning": "yellow",
    "logging.level.error": "bold red",
})
console = Console(theme=custom_theme)

logging.basicConfig(
    level="INFO",#DON'T CHANGE THIS, CHANGE BELOW
    format="| %(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console,
                          show_time=False,show_path=False,
                          markup=True,rich_tracebacks=True)]
)

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

#Matplotlib spam
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
logging.getLogger('matplotlib.backends.backend_pdf').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.INFO)

#Annoying things on import
logging.getLogger("pooch").setLevel(logging.WARNING)
logging.getLogger("numcodecs").setLevel(logging.WARNING)
logging.getLogger("zarr").setLevel(logging.WARNING)
logging.getLogger("dask").setLevel(logging.WARNING)
logger = logging.getLogger('pyshape')
logger.setLevel(logging.INFO)

