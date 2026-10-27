import numpy as np
from pathlib import Path
import argparse
import logging
from ..cli.config import logger, error_exit
from .mod_io import modFile

def _moments(V, F):
    '''Volume, centre of mass and second-moment matrix (about origin) of a closed triangulated surface.'''
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    vol = np.einsum('ij,ij->i', a, np.cross(b, c)) / 6.0
    s = a + b + c
    com = (vol[:, None] * s / 4).sum(0) / vol.sum()
    outer = lambda x, y: np.einsum('ij,ik->ijk', x, y)
    C = (vol[:, None, None] / 20 *
         (outer(a, a) + outer(b, b) + outer(c, c) + outer(s, s))).sum(0)
    return vol.sum(), com, C

def _inertia(C):
    return np.trace(C) * np.eye(3) - C

def principal_axis_align(V, F):
    '''
    Returns (com, R, w). Aligned vertices are (V - com) @ R.
    Axes are sorted by ascending moment (x smallest, z largest), and each
    eigenvector's sign is chosen to point along the original axis, so R stays
    close to identity instead of flipping by 180 degrees.
    '''
    vol, com, _ = _moments(V, F)
    if vol <= 0:
        return None
    _, _, C = _moments(V - com, F)
    w, R = np.linalg.eigh(_inertia(C))

    # Flip each axis so its component along the matching original axis is positive
    d = np.diag(R)
    R = R * np.where(d < 0, -1.0, 1.0)

    # Keep a proper rotation. If det is -1, flip the least-aligned axis,
    # since its sign was the least certain.
    if np.linalg.det(R) < 0:
        R[:, np.argmin(np.abs(np.diag(R)))] *= -1

    return com, R, w

def align_axes(fname):
    '''
    Recentres a single-component vertex model on its centre of mass and rotates it
    so the principal axes lie along x, y, z. The shift/rotation is applied to
    base_disp and dev_dirs, so fitted deviations and freeze flags are preserved.
    Edits the file in place.
    '''
    logger.debug(f'{fname} : Aligning principal axes')

    mod_info = modFile.from_file(fname)
    comps = mod_info.components

    if len(comps) != 1 or comps[0].type != 'vertex':
        logger.warning(f'{fname} : not a single-component vertex model, skipping')
        return 0
    comp = comps[0]


    result = principal_axis_align(comp.vertices, comp.facets)
    if result is None:
        logger.warning(f'{fname} : mesh volume not positive (open mesh or inward facets), skipping')
        return 0
    com, R, w = result

    flip = None
    flip = 'x'
    if flip:
        # 180 deg about axis k: keep that coordinate, negate the other two
        D = np.ones(3)
        D[[i for i in range(3) if i != 'xyz'.index(flip)]] = -1.0
        R = R * D          # same as R @ diag(D): applies the flip after the alignment

    comp.base_disp = (comp.base_disp - com) @ R
    comp.dev_dirs = comp.dev_dirs @ R

    # Sanity check on the rebuilt vertices
    _, com2, C2 = _moments(comp.vertices, comp.facets)
    I2 = _inertia(C2)
    off = np.abs(I2 - np.diag(np.diag(I2))).max() / np.diag(I2).max()
    logger.info(f'{fname} : COM shift {np.round(com, 4)}, '
                f'moments {np.round(w / w.max(), 4)}, '
                f'residual COM {np.linalg.norm(com2):.1e}, off-diag/diag {off:.1e}')

    mod_info.write(fname)
    logger.debug('Done')
    return 1

    
#===Functions for parsing args below this point===
def parse_args():
    '''Parse command-line arguments.'''
    parser = argparse.ArgumentParser(description='Align principal axes of a single component vertex model')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')

    #Beta and lambda ranges and steps
    parser.add_argument('fname',    type=str, help='Name of file to affect. If directory, will affect all .mod files in directory')

    return parser.parse_args()

def validate_args(args):
    
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    args.fname = Path(args.fname)

    return args

#===Main===
def main():

    args = parse_args()
    args = validate_args(args)

    if args.fname.is_file():
        logger.info(f'Running script on file {args.fname}')
        align_axes(args.fname)
    elif args.fname.is_dir():
        logger.info(f'Running script on directory {args.fname}/*.mod')
        modfiles = args.fname.glob('*.mod')
        for mod in modfiles:
            align_axes(mod)
    else:
        raise error_exit('Cannot find file or directory with name [fname]')

if __name__ == '__main__':
    main()

