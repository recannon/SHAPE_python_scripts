import sys
from astropy.time import Time
from .outfmt import logger,error_exit
import dataclasses

#===Shape time formatting for mod/obs files
def time_shape2astropy(t: str) -> Time:
    parts = t.split()
    year, month, day, hour, minute, second = map(int, parts)
    iso_str = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
    return Time(iso_str, format='iso', scale='utc')

def time_astropy2shape(t: Time) -> str:
    dt = t.to_datetime()
    return f"{dt.year} {dt.month} {dt.day} {dt.hour} {dt.minute} {dt.second}"

#===Helper functions for line and grid_scan
@dataclasses.dataclass
class ParamInfo:
    name: str
    min: float
    max: float
    step: float

def check_scan_param_vals(param_info, req_type=float) -> ParamInfo:
    try:
        name = param_info[0]
        min_val, max_val, step_val = map(req_type, param_info[1:])
        if min_val >= max_val:
            error_exit(f'{name} max must be greater than min')
        if step_val <= 0:
            error_exit(f'{name} step must be greater than 0')
        return ParamInfo(name, min_val, max_val, step_val)
    except ValueError:
        error_exit(f'Must provide {req_type.__name__} values for {param_info[0]} min/max/step')

def check_no_files(no_files):
    #Check no_files created
    if no_files == 0:
        error_exit("No files would be generated — check grid min/max/step settings.")
    logger.info(f'This will create and run {no_files} slurm jobs')
    check = input("Is that ok? [y/N] ")
    if check.lower() != 'y':
        logger.info("Aborting.")
        exit(0)


