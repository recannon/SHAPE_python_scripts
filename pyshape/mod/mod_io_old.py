#Last modified 12/09/2025

from dataclasses import dataclass
from pathlib import Path
from astropy.time import Time, TimeDelta
import numpy as np
from jinja2 import Environment, FileSystemLoader
from ..utils import time_shape2astropy,time_astropy2shape
from ..io_utils import logger,error_exit

#Framework for describing modfile as a series dataclasses
#use read and write, and then any individual value can be edited
#before rewriting.

def extract_spin_state(lines):
    logger.debug('Extracting spin state')
    #Find spin state
    for line in lines:
        if '{SPIN STATE}' in line:
            ss_lines = lines[lines.index(line):]
            continue
    #Extract components
    t0_components = ss_lines[1].split()[:6]
    t0 = ' '.join(f'{val:>2}' for val in t0_components)
    t0 = time_shape2astropy(t0)
    values = [float(ss_lines[i].split()[1]) for i in range(2, 17)]
    noimpulses = int(ss_lines[17].split()[0])
    freeze_str = [str(ss_lines[i].split()[0]) for i in range(2, 17)]
    return ModSpinState(t0, *values, noimpulses, ModSpinStateFreeze(*freeze_str))


def extract_phot_functions(lines):
    #Photometric functions
    for line in lines:
        if '{PHOTOMETRIC FUNCTIONS}' in line:
            pf_lines = lines[lines.index(line):]
            continue
    
    #Radar scattering
    no_radar_scattering = int(pf_lines[1].split()[0])
    logger.debug(f'{no_radar_scattering} radar scattering laws')
    #Loop through lines and find and save radar scattering laws
    radar_laws = []
    for rl in range(no_radar_scattering):
        for line in pf_lines:
            if f'{{RADAR SCATTERING LAW {rl}}}' in line:
                rl_lines = pf_lines[pf_lines.index(line):]
                continue
        rl_type    = rl_lines[1].split()[0]
        values     = [float(rl_lines[i].split()[1]) for i in range(2, 4)]
        freeze_str = [  str(rl_lines[i].split()[0]) for i in range(2, 4)]
        radar_laws.append(ModRadarLaw(rl_type, *values, ModRadarLawFreeze(*freeze_str)))

    #Optical scattering
    no_optical_scattering = int(pf_lines[2+4*no_radar_scattering].split()[0])
    logger.debug(f'{no_optical_scattering} optical scattering laws')
    #Loop through lines and find and save optical scattering laws
    optical_laws = []
    for ol in range(no_optical_scattering):
        for line in pf_lines:
            if f'{{OPTICAL SCATTERING LAW {ol}}}' in line:
                ol_lines = pf_lines[pf_lines.index(line):]
                continue
        ol_type    = ol_lines[1].split()[0]
        values     = [float(ol_lines[i].split()[1]) for i in range(2, 7)]
        freeze_str = [  str(ol_lines[i].split()[0]) for i in range(2, 7)]
        optical_laws.append(ModOpticalLaw(ol_type, *values, ModOpticalLawFreeze(*freeze_str)))

    return radar_laws,optical_laws


def extract_components(lines):
    no_components = int(lines[3].strip().split()[0])
    logger.debug(f'{no_components} components')

    #Photometric functions
    for line in lines:
        if '{PHOTOMETRIC FUNCTIONS}' in line:
            shape_lines = lines[:lines.index(line)]
            continue

    components = []
    for comp in range(no_components):
        for line in shape_lines:
            if f'{{COMPONENT {comp}}}' in line:
                comp_lines = shape_lines[shape_lines.index(line):]
                continue

        offsets = [float(comp_lines[i].split()[1]) for i in range(1, 7)]
        offsets_f = [str(comp_lines[i].split()[0]) for i in range(1, 7)]

        comp_type = comp_lines[7].split()[0]

        if comp_type == 'ellipse':
            logger.debug(f'Component {comp}, type {comp_type}')
            ellipse   = [float(comp_lines[i].split()[1]) for i in range(8, 11)]
            ellipse_f = [str(comp_lines[i].split()[0]) for i in range(8, 11)]
            theta = int(comp_lines[11].split()[0])
            freeze_state = ModEllipseFreeze(*offsets_f,*ellipse_f)
            
            components.append(ModEllipse(comp_type,*offsets,*ellipse,theta,freeze_state))

        elif comp_type == 'harmonic':
            logger.debug(f'Component {comp}, type {comp_type}')
            
            harmonic_degree = int(comp_lines[8].split()[0])
            no_coeffs = (harmonic_degree+1)**2

            scale_factors   = [float(comp_lines[i].split()[1]) for i in range(9, 12)]
            scale_factors_f = [str(comp_lines[i].split()[0]) for i in range(9, 12)]
            
            harmonic   = [float(comp_lines[i].split()[1]) for i in range(12, 12+no_coeffs)]
            harmonic_f = [str(comp_lines[i].split()[0]) for i in range(12, 12+no_coeffs)]
            
            theta = int(comp_lines[12+no_coeffs].split()[0])
            
            freeze_state = ModHarmonicFreeze(*offsets_f,*scale_factors_f,harmonic_f)
            
            components.append(ModHarmonic(comp_type,harmonic_degree,*offsets,*scale_factors,harmonic,theta,freeze_state))

        elif comp_type == 'vertex':
            logger.debug(f'Component {comp}, type {comp_type}')

            no_vert = int(comp_lines[8].split()[0])
            no_facets = int(comp_lines[12+2*no_vert].split()[0])

            scale_factors   = [float(comp_lines[i].split()[1]) for i in range(9, 12)]
            scale_factors_f = [str(comp_lines[i].split()[0]) for i in range(9, 12)]

            #Vertices are described in two lines (see SHAPE INTRO)
            vlines1 = comp_lines[12:12+2*no_vert:2]
            vlines2 = comp_lines[13:13+2*no_vert:2]
            facet_lines = comp_lines[13+2*no_vert:13+2*no_vert+no_facets]
            vertex_f = [str(l.split()[0]) for l in vlines1]
            deviations = np.array([float(l.split()[1]) for l in vlines1])
            dev_dirs  = np.array([list(map(float, l.split()[2:])) for l in vlines1])
            base_disp  = np.array([list(map(float, l.split()[:3])) for l in vlines2])
            facets = np.array([list(map(int,l.split()[:3])) for l in facet_lines])

            freeze_state = ModVertexFreeze(*offsets_f,*scale_factors_f,vertex_f)
            components.append(ModVertex(comp_type,no_vert,no_facets,*offsets,*scale_factors,
                                        deviations,dev_dirs,base_disp,facets,freeze_state))

    return components

# fname = '/home/rcannon/Code/Radar/2000rs11/init/mod.template'
def read(fname):
    logger.debug(f'Reading {fname}')
    f = open(fname)
    file_lines = f.readlines()
    f.close()

    components = extract_components(file_lines)
    radar_laws,optical_laws = extract_phot_functions(file_lines)
    spin_state = extract_spin_state(file_lines)
    
    # if len(components) == 1: #If 1 component, adjust for rotation of the component
    #     adjust_angle = 90 + components[0].rotoff0
    # else:
    #     adjust_angle = 90
    # spin_state.t0 -= TimeDelta(adjust_angle/spin_state.spin2,format='jd') #Format to rotation phase 0 degrees (shape uses 90)

    return ModFile(components,radar_laws,optical_laws,spin_state)

def write(ModFile,fname : str) -> bool:
    
    script_dir = Path(__file__).resolve().parent
    env = Environment(loader=FileSystemLoader(f"{script_dir}/templates/"))
    env.filters["fmt"] = format
    env.globals["zip"] = zip
    env.globals["enumerate"] = enumerate
    env.globals["cnvrt_time"] = time_astropy2shape

    output_lines = []
    output_lines.append(f'{{MODEL FILE FOR SHAPE.C VERSION 2.10.11 BUILD Thu 1 May 13:19:01 BST 2025}}\n')

    output_lines.append(f'''{{SHAPE DESCRIPTION}}
               {len(ModFile.components)} {{number of components}}''')
    logger.debug('Writing components')
    for i,c in enumerate(ModFile.components):
        if c.type == 'vertex':
            comp_template = env.get_template("mod_vertex.txt")
        elif c.type == 'ellipse':
            comp_template = env.get_template('mod_ellipse.txt')
        elif c.type == 'harmonic':
            comp_template = env.get_template('mod_harmonic.txt')
        else:
            error_exit('Do not have template for this')
        output_lines.append(comp_template.render(comp_no=i,component=c))
    output_lines.append('\n')
    
    logger.debug('Writing radar laws')
    output_lines.append(f'''{{PHOTOMETRIC FUNCTIONS}}
               {len(ModFile.radar_laws): 2} {{number of radar scattering laws}}''')
    rl_template = env.get_template("mod_scat_radar.txt")
    for i,r in enumerate(ModFile.radar_laws):
        output_lines.append(rl_template.render(law_no=i,radar_law=r))
    logger.debug('Writing optical laws')
    output_lines.append(f'''              {len(ModFile.optical_laws): 2} {{number of optical scattering laws}}''')
    ol_template = env.get_template("mod_scat_optical.txt")
    for i,r in enumerate(ModFile.optical_laws):
        output_lines.append(ol_template.render(law_no=i,optical_law=r))

    logger.debug('Writing spin state')
    output_lines.append('')
    spinstate_template = env.get_template("mod_spin_state.txt")
    output_lines.append(spinstate_template.render(spin_state=ModFile.spin_state))

    with open(fname,'w') as f:
        f.write("\n".join(output_lines))
    logger.debug(f'Written to {fname}')

    return True

@dataclass
class ModSpinStateFreeze:
    angle0: str
    angle1: str
    angle2: str
    spin0: str
    spin1: str
    spin2: str
    moi0: str
    moi1: str
    moi2: str
    spin0dot: str
    spin1dot: str
    spin2dot: str
    libamp: str
    libfreq: str
    libphase: str

@dataclass
class ModSpinState:
    t0: Time
    angle0: float
    angle1: float
    angle2: float
    spin0: float
    spin1: float
    spin2: float
    moi0: float
    moi1: float
    moi2: float
    spin0dot: float
    spin1dot: float
    spin2dot: float
    libamp: float
    libfreq: float
    libphase: float
    noimpulses: int
    freeze_state: ModSpinStateFreeze

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
        return (360*24) / self.spin2

@dataclass
class ModRadarLawFreeze:
    R: str
    C: str

@dataclass
class ModRadarLaw:
    type: str
    R: float
    C: float
    freeze_state: ModRadarLawFreeze

@dataclass
class ModOpticalLawFreeze:
    R: str
    wt: str
    A0: str
    D: str
    k: str

@dataclass
class ModOpticalLaw:
    type: str
    R: float
    wt: float
    A0: float
    D: float
    k: float
    freeze_state: ModOpticalLawFreeze

@dataclass
class ModEllipseFreeze:
    linoff0: str
    linoff1: str
    linoff2: str
    rotoff0: str
    rotoff1: str
    rotoff2: str
    two_a: str
    ab: str
    bc: str

@dataclass
class ModEllipse:
    type: str
    linoff0: float
    linoff1: float
    linoff2: float
    rotoff0: float
    rotoff1: float
    rotoff2: float
    two_a: float
    ab: float
    bc: float
    theta: int
    freeze_state: ModEllipseFreeze

@dataclass
class ModHarmonicFreeze:
    linoff0: str
    linoff1: str
    linoff2: str
    rotoff0: str
    rotoff1: str
    rotoff2: str
    scale0: str
    scale1: str
    scale2: str
    coeffs: list[str]

@dataclass
class ModHarmonic:
    type: str
    degree: int
    linoff0: float
    linoff1: float
    linoff2: float
    rotoff0: float
    rotoff1: float
    rotoff2: float
    scale0: float
    scale1: float
    scale2: float
    coeffs: list[float]
    theta: int
    freeze_state: ModHarmonicFreeze


@dataclass
class ModVertexFreeze:
    linoff0: str
    linoff1: str
    linoff2: str
    rotoff0: str
    rotoff1: str
    rotoff2: str
    scale0: str
    scale1: str
    scale2: str
    vertices: list[str]

@dataclass
class ModVertex:
    type: str
    no_vert: int
    no_fac: int
    linoff0: float
    linoff1: float
    linoff2: float
    rotoff0: float
    rotoff1: float
    rotoff2: float
    scale0: float
    scale1: float
    scale2: float
    deviations: np.ndarray[float]
    dev_dirs: np.ndarray[float,float]
    base_disp: np.ndarray[float,float]
    facets: np.ndarray[float,float]
    freeze_state: ModVertexFreeze

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
        return np.linalg.norm(cross, axis=1)


@dataclass
class ModFile:
    components: list[dataclass]
    radar_laws: list[dataclass]
    optical_laws: list[dataclass]
    spin_state: dataclass