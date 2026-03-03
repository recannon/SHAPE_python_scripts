#Last modified by @recannon 11/01/2026

from astropy.time import Time
from .cli_config import error_exit
from pathlib import Path
from .cli_config import logger
import subprocess

#===Helper functions for checking input arguments
def check_type(par,par_name,req_type):
    try:
        return req_type(par)
    except:
        error_exit(f"{par_name} must be of type {req_type.__name__} (got '{par}')")

def check_dir(path, must_exist=True, create=False):
    """Convert to Path and check it's a directory (if required)."""
    path = Path(path)
    if path.exists():
        if not path.is_dir():
            error_exit(f"Not a directory: {path}")
    else:
        if create:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f'Created directory {path}')
        elif must_exist:
            error_exit(f"Directory does not exist: {path}")
    return path

def check_file(path, must_exist=True):
    """Convert to Path and check it is a file (if required)."""
    path = Path(path)
    if must_exist:
        if not path.exists():
            error_exit(f"File does not exist: {path}")
        if not path.is_file():
            error_exit(f"Not a file: {path}")
    return path

#===Emptying directory===
def empty_dir(path, remove_dirs=False, ignore_errors=False):
    """Remove all contents of a directory"""
    path = Path(path)
    if not path.exists():
        error_exit(f'Cannot empty {path}: Does not exist')
    if not path.is_dir():
        error_exit(f'Cannot empty {path}: Not a directory')

    for item in path.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif remove_dirs:
                if item.is_dir():
                    #Recursively empty dirs
                    empty_dir(item, remove_dirs=remove_dirs, ignore_errors=ignore_errors)
                    item.rmdir()
        except Exception as e:
            if not ignore_errors:
                raise
            else:
                logger.warning(f'Cannot remove {item}: {e}')

#===Running SHAPE===
def run_shape(args, run_dir, out_log):
    """Runs SHAPE with args=[par, mod, obs], where obs is optional"""
    
    #Check files exist and change to absolute paths
    out_log = Path(out_log).resolve()
    args = [check_file(arg).resolve() for arg in args]
    run_dir = check_dir(run_dir).resolve()

    logger.info(f'Running {args[0].name}')
    logger.debug(f'shape {" ".join(map(str, args))}')

    with out_log.open('w') as log:
        try:
            subprocess.run(['shape', *map(str, args)], cwd=run_dir, 
                           stdout=log, stderr=subprocess.STDOUT,  check=True)
        except subprocess.CalledProcessError:
            error_exit(f'Problem running {args[0].name} action. Check {out_log}')

#===Shape time formatting for mod/obs files
def time_shape2astropy(t: str) -> Time:
    parts = t.split()
    year, month, day, hour, minute, second = map(int, parts)
    iso_str = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
    return Time(iso_str, format='iso', scale='utc')

def time_astropy2shape(t: Time) -> str:
    dt = t.to_datetime()
    return f"{dt.year: >4} {dt.month: >2} {dt.day: >2} {dt.hour: >2} {dt.minute: >2} {dt.second: >2}"
