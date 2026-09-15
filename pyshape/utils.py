#Last modified by @recannon 15/09/2026

#15/09/2026 - mpar and ppm handling functions
#27/08/2026 - More Documentation

#Helper functions for use throughout the scripts
import tempfile
from astropy.time import Time
from .cli_config import error_exit
from pathlib import Path
from .cli_config import logger
import subprocess

#===Helper functions for checking input arguments
def check_type(par,par_name,req_type):
    '''Check if an input is a correct type. If able, will change it to that type'''
    try:
        return req_type(par)
    except:
        error_exit(f"{par_name} must be of type {req_type.__name__} (got '{par}')")

def check_dir(path, must_exist=True, create=False):
    '''Convert to Path and check it's a directory. Create if required'''
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
    '''Convert to Path and check it is a file (if required).'''
    path = Path(path)
    if must_exist:
        if not path.exists():
            error_exit(f"File does not exist: {path}")
        if not path.is_file():
            error_exit(f"Not a file: {path}")
    return path

#===Emptying directory===
def empty_dir(path, remove_dirs=False, ignore_errors=False):
    '''Remove all contents of a directory. remove_dirs=True to remove directories'''
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

#===Running SHAPE and other related functions===
def run_shape(args: list[str|Path], run_dir: str|Path, out_log: str|Path):
    '''Runs SHAPE with args=[par, mod, obs], where obs is optional'''
    
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

def compile_moments_output(pa_view_files, out_jpg, log_file):
    pa_view_files = sorted(check_file(f) for f in pa_view_files)
    pos_files = [f for f in pa_view_files if 'pos' in str(f)]
    neg_files = [f for f in pa_view_files if 'neg' in str(f)]
    out_jpg = Path(out_jpg).resolve()
    log_file = Path(log_file).resolve()
    #3 columns so for 3 principal axis views
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        temp_ppm = tmp_path / 'pa_views.ppm'

        # ppmstack_cmd = (['ppmstack', '3', '1', '1']
        #                  + [str(f) for f in pos_files + neg_files]
        #                  + [str(temp_ppm)])
        # ffmpeg_cmd = ['ffmpeg', '-loglevel', 'error', '-hide_banner',
        #               '-i', str(temp_ppm), str(out_jpg)]
        ppmstack_cmd = ppmstack_cmd_list([str(f) for f in pos_files + neg_files], str(temp_ppm), 3)
        ffmpeg_cmd = ffmpeg_ppm2jpg_list(str(temp_ppm), str(out_jpg))

        with open(log_file, 'w') as log:
            for cmd in (ppmstack_cmd, ffmpeg_cmd):
                logger.debug(f'Running: {" ".join(cmd)}')
                subprocess.run(cmd, cwd=tmp_path, stdout=log,
                                stderr=subprocess.STDOUT, check=True)
    return
    
def ppmstack_cmd_list(files:list[str|Path], out_file:str|Path, no_cols=3):
    '''Runs SHAPE ppmstack command'''
    return ['ppmstack', str(no_cols), '1', '1', *(str(f) for f in files), str(out_file)]

def ffmpeg_ppm2jpg_list(ppm_file:str|Path,jpg_file:str|Path):
    return ['ffmpeg', '-loglevel', 'error', '-hide_banner', '-i', str(ppm_file), str(jpg_file)]

#===Shape time formatting for mod/obs files
def time_shape2astropy(t: str) -> Time:
    '''Converts a SHAPE time string to astropy.time object'''
    parts = t.split()
    year, month, day, hour, minute, second = map(int, parts)
    iso_str = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
    return Time(iso_str, format='iso', scale='utc')

def time_astropy2shape(t: Time) -> str:
    '''Converts astropy.time object to SHAPE time string'''
    dt = t.to_datetime()
    return f"{dt.year: >4} {dt.month: >2} {dt.day: >2} {dt.hour: >2} {dt.minute: >2} {dt.second: >2}"
