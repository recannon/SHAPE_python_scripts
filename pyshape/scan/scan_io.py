#Last modified 12/09/2025

import dataclasses
import glob
import numpy as np
from .. import log_file
from ..io_utils import logger,error_exit

#===Read polescans===
def polescan_results(scan_dir):

    # #First check jobs finished
    # faction_path = f'{scan_dir}/faction/job_output*'
    # faction_files = sorted(glob.glob(faction_path))
    # # print(f'Found {len(faction_path)} faction files')
    # for fac in faction_files:
    #     f = open(fac,'r')
    #     lines = [l.strip().split() for l in f.readlines()]
    #     f.close()
    #     if lines[-1][0] != 'Done':
    #         logger.warning(f'Warning: {fac} not completed. {lines[-2][3]}')


    log_file_path = f'{scan_dir}/logfiles/lat*.log'
    log_files = sorted(glob.glob(log_file_path))
    if len(log_files) == 0:
        logger.warning(f'Could not find any polescan log files ({log_file_path})')
        return [],[],[]
    else:
        logger.debug(f'Found {len(log_files)} log files')

    chi,bet,lam,unreduced,dof = [],[],[],[],[]
    for f in log_files:
        try:
            log_info = log_file.read(f)
            chi.append(log_info['ALLDATA'])
            # unreduced.append(log_info['unreduced'])
            # dof.append(log_info['dof'])
            bet.append(int(f[-13:-10]))
            lam.append(int(f[-7:-4]))
        except:
            # chi.append(np.nan)
            logger.warning(f'Found NaN chisqr in {f}')

    chi,bet,lam = np.array(chi),np.array(bet),np.array(lam)
    unreduced,dof = np.array(unreduced),np.array(dof)

    return bet,lam,chi,unreduced,dof

#===Helper functions for line and grid_scan inputs
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