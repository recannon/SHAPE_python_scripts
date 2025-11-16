from dataclasses import dataclass
from typing import ClassVar, Literal
from astropy.time import Time
from ..io_utils import logger,error_exit
from ..utils import time_shape2astropy,time_astropy2shape
import numpy as np
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

script_dir = Path(__file__).resolve().parent
env = Environment(loader=FileSystemLoader(f"{script_dir}/templates/"))
env.filters["fmt"] = format
env.globals["zip"] = zip
env.globals["enumerate"] = enumerate
env.globals["cnvrt_time"] = time_astropy2shape

class modFile:
    
    def __init__(self, components, phot_functions, spinstate, raw_lines=None):
        self.components = components
        self.phot_functions = phot_functions
        self.spinstate = spinstate
        self.raw_lines = raw_lines  #for debugging. Note that this does not update when changes are made
    
    #===Factory methods===
    @classmethod
    def from_lines(cls, lines):
        """Parse a mod file from a list of raw lines."""
        obj = cls([], [], None, raw_lines=lines)
        obj.spinstate = obj._extract_spin_state()
        obj.phot_functions = obj._extract_phot_functions()
        obj.components = obj._extract_components()
        return obj

    @classmethod
    def from_file(cls, fname):
        """Parse a mod file directly from disk."""
        with open(fname) as f:
            lines = f.readlines()
        return cls.from_lines(lines)

    #===Internal parsers===
    @staticmethod
    def _find_block_idx(name, lines):
        idx = next((i for i, line in enumerate(lines) if name in line), None)
        if idx is None: #None if not found
            raise SystemExit(f'Error: No {name} block found in file')
        return idx
    
    def _extract_spin_state(self):
        logger.debug('Extracting spin state')
        lines = self.raw_lines
        
        #Find spin state lines
        idx = self._find_block_idx('{SPIN STATE}',lines)
        ss_lines = lines[idx : idx + 18]

        return ModSpinState.from_lines(ss_lines)

    def _extract_phot_functions(self):
        logger.debug('Extracting photometric functions')
        lines = self.raw_lines

        pf_idx = self._find_block_idx('{PHOTOMETRIC FUNCTIONS}', lines)
        ss_idx = self._find_block_idx('{SPIN STATE}', lines)
        pf_lines = lines[pf_idx:ss_idx]

        #radar laws
        n_radar = int(pf_lines[1].split()[0])
        logger.debug(f'{n_radar} radar laws')
        radar_laws = []
        for i in range(n_radar):
            idx = self._find_block_idx(f'{{RADAR SCATTERING LAW {i}}}', pf_lines)
            rl_lines = pf_lines[idx : idx + 4]
            radar_laws.append(ModRadarLaw.from_lines(rl_lines))

        #optical laws
        n_optical = int(pf_lines[2 + 4 * n_radar].split()[0])
        logger.debug(f'{n_optical} optical laws')
        optical_laws = []
        for i in range(n_optical):
            idx = self._find_block_idx(f'{{OPTICAL SCATTERING LAW {i}}}', pf_lines)
            ol_lines = pf_lines[idx : idx + 7]
            optical_laws.append(ModOpticalLaw.from_lines(ol_lines))

        return (radar_laws, optical_laws)

    def _extract_components(self):
        logger.debug('Extracting components')
        lines = self.raw_lines

        cp_idx = self._find_block_idx('{SHAPE DESCRIPTION}',lines)
        pf_idx = self._find_block_idx('{PHOTOMETRIC FUNCTIONS}',lines)
        components_lines = lines[cp_idx:pf_idx]

        no_components = int(components_lines[1].split()[0])
        logger.debug(f'Found {no_components} components')

        components = []

        for c_no in range(no_components):

            c_idx = self._find_block_idx(f'{{COMPONENT {c_no}}}',components_lines)
            c_lines = components_lines[c_idx:]

            comp_type   = c_lines[7].split()[0]

            if comp_type == "ellipse":
                components.append(ModEllipse.from_lines(c_lines))
            elif comp_type == "harmonic":
                components.append(ModHarmonic.from_lines(c_lines))
            elif comp_type == "vertex":
                components.append(ModVertex.from_lines(c_lines))
            else:
                raise ValueError(f"Unknown component type '{comp_type}'")

        return components

    #===Writing===
    def write(self,fname=None):

        output_lines = []
        output_lines.append(f'{{MODEL FILE FOR SHAPE.C VERSION 2.10.11 BUILD Thu 1 May 13:19:01 BST 2025}}\n\n')

        output_lines.extend([f'{{SHAPE DESCRIPTION}}\n',
                             f'{len(self.components):>16} {{number of components}}\n'])
        for i,c in enumerate(self.components):
            c_lines = c.to_lines(idx=i)
            output_lines.extend(c_lines)
            output_lines.append('\n')
        
        output_lines.append(f'\n\n{{PHOTOMETRIC FUNCTIONS}}\n')
        output_lines.append(f'{len(self.phot_functions[0]):>16} {{number of radar scattering laws}}\n')
        for i,rl in enumerate(self.phot_functions[0]):
            rl_lines = rl.to_lines(idx=i)
            output_lines.extend(rl_lines)
        output_lines.append(f'{len(self.phot_functions[1]):>16} {{number of optical scattering laws}}\n')
        for i,ol in enumerate(self.phot_functions[1]):
            ol_lines = ol.to_lines(idx=i)
            output_lines.extend(ol_lines)
        output_lines.append('\n')
        
        output_lines.extend(self.spinstate.to_lines())

        if fname:
            with open(fname,'w') as f:
                f.writelines(output_lines)
            logger.debug(f'Written to {fname}')
        else:
            return output_lines
        
        return True

#==================
#   DATACLASSES
#==================

#Sets up the framework for storing values and their freeze state
@dataclass
class FreezeAwareBase:
    values: "np.ndarray | list[float]"
    values_freeze: "np.ndarray | list[str]"         
    _param_index: ClassVar[dict[str, int]] = {}  #overwrites when inherited
    _normal_freeze_names: ClassVar[list[str]] = ["values_freeze"]

    #Simple function to set both new value and freeze at the same time
    #Does not work for subclass attributes outside of 'values', or for setter attributes
    def set_param(self, name: str, value: float, freeze: str | None = None):
        if name not in self._param_index:
            raise KeyError(f"{name} is not a valid parameter")

        idx = self._param_index[name]
        self.values[idx] = value
        if freeze is not None:
            self.values_freeze[idx] = freeze

    def __setattr__(self, name: str, value):
        if name in self._param_index:
            self.values[self._param_index[name]] = value
        elif name.endswith("_freeze") and name not in self._normal_freeze_names:
            base = name[:-7]
            if base in self._param_index:
                self.values_freeze[self._param_index[base]] = value
        else:  # for t0, noimpulses, and internal arrays
            super().__setattr__(name, value)

    def __getattr__(self, name: str):
        if name in self._param_index:
            return self.values[self._param_index[name]]
        elif name.endswith("_freeze") and name not in self._normal_freeze_names:
            base = name[:-7]
            if base in self._param_index:
                return self.values_freeze[self._param_index[base]]
        raise AttributeError(f"{name} not found")

#===SPIN STATE===
@dataclass
class ModSpinState(FreezeAwareBase):
    t0: Time
    noimpulses: int

    _param_index: ClassVar[dict[str, int]] = {
        "angle0": 0, "angle1": 1, "angle2": 2, 
        "spin0": 3,  "spin1": 4, "spin2": 5, 
        "moi0": 6,   "moi1": 7,   "moi2": 8, 
        "spin0dot": 9, "spin1dot": 10, "spin2dot": 11, 
        "libamp": 12, "libfreq": 13, "libphase": 14,
    }

    @property
    def lam(self):
        return (self.angle0 - 90) % 360
    @lam.setter
    def lam(self, new_value):
        self.angle0 = (new_value + 90) % 360

    @property
    def bet(self):
        return 90 - self.angle1
    @bet.setter
    def bet(self, new_value):
        self.angle1 = 90 - new_value

    @property
    def P(self):
        return (360 * 24) / self.spin2
    @P.setter
    def P(self, new_value):
        self.spin2 = (360 * 24) / new_value
        
    #---Give custom properties freezing abilities---
    _derived_freeze_map: ClassVar[dict[str,str]] = {
        "lam_freeze": "angle0_freeze",
        "bet_freeze": "angle1_freeze",
        "P_freeze": "spin2_freeze",
    }

    def __getattr__(self, name: str):
        if name in self._derived_freeze_map:
            return getattr(self, self._derived_freeze_map[name])
        return super().__getattr__(name)

    def __setattr__(self, name: str, value):
        if name in self._derived_freeze_map:
            return setattr(self, self._derived_freeze_map[name], value)
        super().__setattr__(name, value)
    
    #---Constructor---
    @classmethod
    def from_lines(cls,ss_lines):

        #Extract components
        t0_components = ss_lines[1].split()[:6]
        t0 = ' '.join(f'{val:>2}' for val in t0_components)
        t0 = time_shape2astropy(t0)
        values = [float(line.split()[1]) for line in ss_lines[2:17]]
        values_freeze = [line.split()[0] for line in ss_lines[2:17]]
        noimpulses = int(ss_lines[17].split()[0])
        
        return cls(values, values_freeze, t0, noimpulses)

    def to_lines(self):
        logger.debug('Writing spin state')
        
        spinstate_template = env.get_template("mod_spinstate.txt")
        new_ss_lines = spinstate_template.render(spin_state=self)
        
        return new_ss_lines.splitlines(keepends=True)
            

#===SCATTERING LAWS===  
@dataclass
class ModOpticalLaw(FreezeAwareBase):
    type: str
    data: Literal["optical"] = "optical"

    _param_index: ClassVar[dict[str,int]] = {
        "R": 0, "wt": 1, "A0": 2, "D": 3, "k": 4,
    }
    
    @classmethod
    def from_lines(cls, ol_lines):
        law_type = ol_lines[1].split()[0]
        values = [float(line.split()[1]) for line in ol_lines[2:7]]
        freeze = [line.split()[0] for line in ol_lines[2:7]]
        return cls(values, freeze, law_type)
    
    def to_lines(self,idx):
        logger.debug(f'Writing optical law (no {idx})')
        
        optical_template = env.get_template("mod_opticallaw.txt")
        new_ol_lines = optical_template.render(optical_law=self,law_no=idx)
        
        return new_ol_lines.splitlines(keepends=True)

@dataclass
class ModRadarLaw(FreezeAwareBase):
    type: str
    data: Literal["radar"] = "radar"

    
    _param_index: ClassVar[dict[str,int]] = {
        "R": 0, "C": 1,
    }
    
    @classmethod
    def from_lines(cls, rl_lines):
        law_type = rl_lines[1].split()[0]
        values = [float(line.split()[1]) for line in rl_lines[2:4]]
        freeze = [line.split()[0] for line in rl_lines[2:4]]
        return cls(values, freeze, law_type)
    
    def to_lines(self,idx):
        logger.debug(f'Writing radar law (no {idx})')
        
        radar_template = env.get_template("mod_radarlaw.txt")
        new_rl_lines = radar_template.render(radar_law=self,law_no=idx)
        
        return new_rl_lines.splitlines(keepends=True)
    

#===VERTEX COMPONENTS===
@dataclass
class ModEllipse(FreezeAwareBase):
    theta: int
    type: Literal["ellipse"] = "ellipse"  # fixed value

    _param_index: ClassVar[dict[str,int]] = {
        "linoff0": 0, "linoff1": 1, "linoff2": 2,
        "rotoff0": 3, "rotoff1": 4, "rotoff2": 5,
        "two_a": 6, "ab": 7, "bc": 8,
    }
    
    def freeze_params(self, state, fields=None):
        if fields==None:
            fields=list(self._param_index.keys())

        for field in fields:
            logger.debug(f'Changing {field} to {state}')
            idx = self._param_index[field]
            self.values_freeze[idx] = state
    
    @classmethod
    def from_lines(cls, e_lines):
        
        offsets   = [float(line.split()[1]) for line in e_lines[1:7]]
        offsets_f = [line.split()[0] for line in e_lines[1:7]]
        ellipse   = [float(line.split()[1]) for line in e_lines[8:11]]
        ellipse_f = [str(line.split()[0]) for line in e_lines[8:11]]
        theta = int(e_lines[11].split()[0])
        
        values = np.concatenate([offsets,ellipse])
        values_freeze = np.concatenate([offsets_f,ellipse_f])
        
        return cls(values, values_freeze, theta)
    
    def to_lines(self,idx):
        logger.debug(f'Writing ellipse (component {idx})')
        
        ellipse_template = env.get_template("mod_ellipse.txt")
        new_e_lines = ellipse_template.render(component=self,comp_no=idx)
        
        return new_e_lines.splitlines(keepends=True)

@dataclass
class ModHarmonic(FreezeAwareBase):
    coeffs: "np.ndarray | list[float]"
    coeffs_freeze: "np.ndarray | list[str]"
    degree: int   
    theta: int
    type: Literal["harmonic"] = "harmonic"  # fixed value

    _param_index: ClassVar[dict[str,int]] = {
        "linoff0": 0, "linoff1": 1, "linoff2": 2,
        "rotoff0": 3, "rotoff1": 4, "rotoff2": 5,
        "scale0": 6, "scale1": 7, "scale2": 8,
    }
    _normal_freeze_names: ClassVar[list[str]] = [
        "values_freeze", "coeffs_freeze",
    ]
    
    @classmethod
    def from_lines(cls, h_lines):
        
        harmonic_degree = int(h_lines[8].split()[0])
        no_coeffs = (harmonic_degree+1)**2

        offsets   = [float(line.split()[1]) for line in h_lines[1:7]]
        offsets_f = [line.split()[0] for line in h_lines[1:7]]
        scale   = [float(line.split()[1]) for line in h_lines[9:12]]
        scale_f = [str(line.split()[0]) for line in h_lines[9:12]]
        
        harmonic   = [float(line.split()[1]) for line in h_lines[12:12+no_coeffs]]
        harmonic_f = [str(line.split()[0]) for line in h_lines[12:12+no_coeffs]] 
        theta = int(h_lines[12+no_coeffs].split()[0])

        values = np.concatenate([offsets,scale])
        values_freeze = np.concatenate([offsets_f,scale_f])
        
        return cls(values=values, values_freeze=values_freeze, 
                   coeffs=harmonic, coeffs_freeze=harmonic_f, 
                   degree=harmonic_degree, theta=theta)
        
    def to_lines(self,idx):
        logger.debug(f'Writing harmonic (component {idx})')
        
        harmonic_template = env.get_template("mod_harmonic.txt")
        new_h_lines = harmonic_template.render(component=self,comp_no=idx)
        
        return new_h_lines.splitlines(keepends=True)
        
@dataclass
class ModVertex(FreezeAwareBase):
    deviations: np.ndarray[float]
    dev_dirs: np.ndarray[float,float]
    base_disp: np.ndarray[float,float]
    facets: np.ndarray[float,float]
    vertices_freeze: "np.ndarray | list[str]"  
    no_vert: int
    no_fac: int 
    type: Literal["vertex"] = "vertex"  # fixed value

    _param_index: ClassVar[dict[str,int]] = {
        "linoff0": 0, "linoff1": 1, "linoff2": 2,
        "rotoff0": 3, "rotoff1": 4, "rotoff2": 5,
        "scale0": 6, "scale1": 7, "scale2": 8,
    }
    _normal_freeze_names: ClassVar[list[str]] = [
        "values_freeze", "vertices_freeze",
    ]

    @property
    def vertices(self):
        return self.base_disp + self.dev_dirs * self.deviations[:, np.newaxis]
    
    @property
    def FN(self):
        v = self.vertices
        f = self.facets
        a = v[f[:, 1]] - v[f[:, 0]]
        b = v[f[:, 2]] - v[f[:, 0]]
        normals = np.cross(a, b)
        norms = np.linalg.norm(normals, axis=1, keepdims=True)
        # Avoid divide-by-zero
        with np.errstate(invalid='ignore'):
            normals_unit = np.where(norms > 0, normals / norms, 0.0)
        return normals_unit
    
    @property
    def FNa(self) -> np.ndarray:
        v = self.vertices
        f = self.facets
        a = v[f[:, 1]] - v[f[:, 0]]
        b = v[f[:, 2]] - v[f[:, 0]]
        cross = np.cross(a, b)
        return np.linalg.norm(cross, axis=1) * 0.5

    def shuffle_vertices(self, rng: np.random.Generator | None = None):
        if rng is None:
            rng = np.random.default_rng()

        n = len(self.base_disp)
        perm = rng.permutation(n)

        self.base_disp = self.base_disp[perm]
        self.dev_dirs = self.dev_dirs[perm]
        self.deviations = self.deviations[perm]

        index_map = np.zeros_like(perm)
        index_map[perm] = np.arange(n)
        self.facets = index_map[self.facets]
        return

    def freeze_params(self, state, fields=None):
        if fields is None:
            fields = list(self._param_index.keys()) + ['vertices']

        for field in fields:
            if field == 'vertices':
                logger.debug(f'Changing vertices to {state}')
                self.vertices_freeze = [state]*self.no_vert
            else:
                logger.debug(f'Changing {field} to {state}')
                idx = self._param_index[field]
                self.values_freeze[idx] = state
    

    @classmethod
    def from_lines(cls, v_lines):
        
        no_vert = int(v_lines[8].split()[0])
        no_fac  = int(v_lines[12+2*no_vert].split()[0])

        offsets   = [float(line.split()[1]) for line in v_lines[1:7]]
        offsets_f = [line.split()[0] for line in v_lines[1:7]]
        scale   = [float(line.split()[1]) for line in v_lines[9:12]]
        scale_f = [str(line.split()[0]) for line in v_lines[9:12]]
        
        #Vertices are described in two lines (see SHAPE INTRO)
        vlines1 = v_lines[12:12+2*no_vert:2]
        vlines2 = v_lines[13:13+2*no_vert:2]
        facet_lines = v_lines[13+2*no_vert:13+2*no_vert+no_fac]
        vertices_freeze = [str(l.split()[0]) for l in vlines1]
        deviations = np.array([float(l.split()[1]) for l in vlines1])
        dev_dirs  = np.array([list(map(float, l.split()[2:])) for l in vlines1])
        base_disp  = np.array([list(map(float, l.split()[:3])) for l in vlines2])
        facets = np.array([list(map(int,l.split()[:3])) for l in facet_lines])

        values = np.concatenate([offsets,scale])
        values_freeze = np.concatenate([offsets_f,scale_f])
        
        return cls(values, values_freeze, deviations, dev_dirs, base_disp, facets, vertices_freeze, no_vert, no_fac, )

    def to_lines(self,idx):
        logger.debug(f'Writing vertex (component {idx})')
        
        vertex_template = env.get_template("mod_vertex.txt")
        new_v_lines = vertex_template.render(component=self,comp_no=idx)
        
        return new_v_lines.splitlines(keepends=True)