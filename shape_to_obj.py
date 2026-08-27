#Last modified by @recannon 10/02/2026

import trimesh
import numpy as np
from pyshape.mod.mod_io import modFile
from pathlib import Path

#Read modfile for shape (Assumes one vertex component only)
mod_filename = Path('/home/rcannon/Code/Radar/SHAPE/2024on/PS6/2-vx/v1500-02/modfiles/lat-86lon312.mod')
mod_info = modFile.from_file(mod_filename)
mod_vx = mod_info.components[0]
V,F,FN,FNa = mod_vx.vertices, mod_vx.facets, mod_vx.FN, mod_vx.FNa

mesh = trimesh.Trimesh(vertices=V, faces=F)
obj_name = mod_filename.with_suffix('.obj')
mesh.export(obj_name)