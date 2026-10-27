#Last modified @recannon 20261027

import argparse
import logging
from ..cli.cli_config import logger, error_exit
from .mod_io import modFile
import trimesh
from pathlib import Path

def shape2obj(modfile):

    mod_info = modFile.from_file(modfile)
    c_list = mod_info.components
    if len(c_list) != 1:
        logger.warning('More than one component found, writing out first component only')
    c_vx = c_list[0]
    if c_vx.type != 'vertex':
        raise ValueError(f'{modfile} is type {c_vx.type!r}, not vertex')
    
    V,F = c_vx.vertices, c_vx.facets

    mesh = trimesh.Trimesh(vertices=V, faces=F)
    obj_name = modfile.with_suffix('.obj')
    mesh.export(obj_name)
    
    return obj_name
    

#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Convert shape files to OBJ format",
                                     epilog='Must be a vertex model, and only writes the first component.')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Beta and lambda ranges and steps
    parser.add_argument("fname", type=str, 
                        help=".mod file to affect. If directory, will affect all .mod files in directory")
    
    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    target = Path(args.fname)
    files = sorted(target.glob('*.mod')) if target.is_dir() else [target]

    for f in files:
        try:
            out = shape2obj(f)
        except ValueError as e:
            logger.warning(f'Skipping {f}: {e}')
            continue
        logger.info(f'Wrote {out}')

    return True

if __name__ == "__main__":
    main()

