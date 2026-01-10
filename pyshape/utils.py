from astropy.time import Time
from .cli_config import error_exit
from pathlib import Path

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

def check_file(file, must_exist=True):
    """Convert to Path and check it is a file (if required)."""
    file = Path(file)
    if must_exist:
        if not file.exists():
            error_exit(f"File does not exist: {file}")
        if not file.is_file():
            error_exit(f"Not a file: {file}")
    return file

#===Shape time formatting for mod/obs files
def time_shape2astropy(t: str) -> Time:
    parts = t.split()
    year, month, day, hour, minute, second = map(int, parts)
    iso_str = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
    return Time(iso_str, format='iso', scale='utc')

def time_astropy2shape(t: Time) -> str:
    dt = t.to_datetime()
    return f"{dt.year: >4} {dt.month: >2} {dt.day: >2} {dt.hour: >2} {dt.minute: >2} {dt.second: >2}"
