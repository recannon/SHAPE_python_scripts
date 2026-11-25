#Last modified by @recannon 20261125

#20261125 - Cleared up error messages
#20260827 - More (limited) documentation

#Reads in many logfiles at once for plot functions/rank to use

import dataclasses
import numpy as np
from pathlib import Path
from . import log_io
from ..cli.config import logger,error_exit

def scan_results(scan_dir):
    namecores_path = Path(scan_dir) / 'namecores.txt'
    if not namecores_path.exists():
        error_exit(f'Could not find namecores.txt in {scan_dir}')

    p1, p2, chi = [], [], []
    with open(namecores_path) as f:
        lines = f.readlines()

    #This is a boolean toggle to detect if its reading a grid scan or a pole scan
    polescan = lines[0].split()[0].startswith('lat')

    for line in lines:
        namecore, p1_val, p2_val = line.strip().split()
        log_path = Path(scan_dir) / 'logfiles' / f'{namecore}.log'
        if not log_path.exists():
            logger.warning(f'Log file not found: {log_path}')
            continue
        try:
            log_info = log_io.read(log_path)
            chi.append(log_info['ALLDATA'])
            p1.append(float(p1_val))
            p2.append(float(p2_val))
        except:
            logger.warning(f'Cannot find chisqr in {log_path}')

    return np.array(p1), np.array(p2), np.array(chi), polescan

#===Helper functions for line and grid_scan inputs
@dataclasses.dataclass
class ParamInfo:
    location: str
    name: str
    min: float
    max: float
    step: float

def check_scan_param_vals(param_info, req_type=float) -> ParamInfo:
    try:
        location = param_info[0]
        name = param_info[1]
        min_val, max_val, step_val = map(req_type, param_info[2:])
        if min_val >= max_val:
            error_exit(f'{name} max must be greater than min')
        if step_val <= 0:
            error_exit(f'{name} step must be greater than 0')
        return ParamInfo(location, name, min_val, max_val, step_val)
    except ValueError:
        logger.warning(param_info)
        error_exit(f'Must provide {req_type.__name__} values for {param_info[1]} min/max/step')

def check_no_files(no_files):
    #Check no_files created
    if no_files == 0:
        error_exit("No files would be generated — check grid min/max/step settings.")
    logger.info(f'This will create and run {no_files} slurm jobs')
    check = input("Is that ok? [y/N] ")
    if check.lower() != 'y':
        logger.info("Aborting.")
        exit(0)