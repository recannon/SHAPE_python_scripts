#Last modified by @recannon 09/01/2026

from dataclasses import dataclass
from typing import ClassVar, Literal, Union
from ..utils import time_shape2astropy, time_astropy2shape
from ..cli_config import logger, error_exit
from astropy.time import Time

class obsFile:
    
    def __init__(self, datasets, raw_lines=None):
        self.datasets = datasets
        
    #===Factory methods===
    @classmethod
    def from_lines(cls, lines):
        """Parse a mod file from a list of raw lines."""
        obj = cls([], raw_lines=lines)
        obj.datasets = obj._extract_datasets()
        return obj

    @classmethod
    def from_file(cls, fname):
        """Parse a mod file directly from disk."""
        with open(fname) as f:
            lines = f.readlines()
        return cls.from_lines(lines)

#==================
#   DATACLASSES
#==================

@dataclass
class ObsSet():
    set_lines: list[str]
    set_no: int
    set_type: str
    scattering_law: int
    
    @classmethod
    def from_lines(cls, set_lines: list[str]) -> "ObsSet":
        set_no = int(set_lines[0].split()[-1].rstrip('}'))
        idx = cls._find_line('{set type}', set_lines)
        set_type = set_lines[idx].split()[0]
        idx = cls._find_line('scattering law for this set}', set_lines)
        scattering_law = int(set_lines[idx].split()[0])

        #Return specific subclass for datatype
        subclass = cls._get_subclass(set_type)
        return subclass(set_lines=set_lines, set_no=set_no, 
                        set_type=set_type, scattering_law=scattering_law)

    def set_weight(self, weight: float):
        if not hasattr(self, "frames") or self.frames is None:
            error_exit(f'Cannot find frames attribute for set {self.set_no}')
        for frame in self.frames:
            frame.weight = weight

    @staticmethod
    def _find_line(name: str, lines: list[str]) -> int:
        idx = next((i for i, line in enumerate(lines) if name in line), None)
        if idx is None:
            error_exit(f'Error: No {name} found in this set')
        return idx

    @staticmethod
    def _get_subclass(set_type: str) -> Type["ObsSet"]:
        if set_type.lower() == 'delay-doppler':
            return ObsDelayDoppler
        if set_type.lower() == 'doppler':
            return ObsDoppler
        if set_type.lower() == 'lightcurve':
            return ObsLightCurve
        return ObsSet


#===FRAMES INFO===
@dataclass
class ObsLightCurveFrame:
    fname: str
    calfact_freeze: str
    calfact: float
    weight: float

@dataclass
class ObsDopplerFrame(ObsLightCurveFrame):
    date: Time
    sdev: float
    looks: float
    mask: int
    
@dataclass
class ObsDelayDopplerFrame(ObsDopplerFrame):
    com_del_row: float


#===DOPPLER (CW)===
@dataclass
class ObsDoppler(ObsSet):
    dop_info: list[float] = None
    no_frames: int = None
    frames: list[ObsDopplerFrame] = None
        
    def __post_init__(self):
        self._parse()
        
    def _parse(self):
        res_idx = self._find_line('{dop: ',self.set_lines)
        self.dop_info = [float(x) for x in self.set_lines[res_idx].split()[:3]]
        
        frame_idx = self._find_line('{number of frames}', self.set_lines)
        self.no_frames = int(self.set_lines[frame_idx].split()[0])
        frame_lines = self.set_lines[frame_idx+2 : frame_idx+2 + self.no_frames]
        
        self.frames = [
            ObsDopplerFrame(
                fname=parts[0],
                date=time_shape2astropy(' '.join(parts[1:7])),
                sdev=float(parts[7]),
                calfact_freeze=parts[8],
                calfact=float(parts[9]),
                looks=float(parts[10]),
                weight=float(parts[11]),
                mask=int(parts[12])
            )
            for parts in (line.split() for line in frame_lines)
        ]
        
        
#===DELAY DOPPLER===
@dataclass
class ObsDelayDoppler(ObsSet):
    del_info: list[Union[float,str]] = None
    dop_info: list[float] = None
    no_frames: int = None
    frames: list[ObsDopplerFrame] = None
        
    def __post_init__(self):
        self._parse()
        
    def _parse(self):
        del_idx = self._find_line('{delay: ',self.set_lines)
        self.del_info = [float(x) for x in self.lines[del_idx].split()[:5]]
        dop_idx = self._find_line('{dop: ',self.set_lines)
        parts = self.lines[dop_idx].split()
        self.dop_info = [float(parts[0]),float(parts[1]),float(parts[2]),float(parts[3]),parts[4]]        
        
        frame_idx = self._find_line('{number of frames}', self.set_lines)
        self.no_frames = int(self.set_lines[frame_idx].split()[0])
        frame_lines = self.set_lines[frame_idx+2 : frame_idx+2 + self.no_frames]
        
        self.frames = [
            ObsDelayDopplerFrame(
                fname=parts[0],
                date=time_shape2astropy(' '.join(parts[1:7])),
                sdev=float(parts[7]),
                calfact_freeze=parts[8],
                calfact=float(parts[9]),
                looks=float(parts[10]),
                com_del_row=float(parts[11]),
                weight=float(parts[12]),
                mask=int(parts[13])
            )
            for parts in (line.split() for line in frame_lines)
        ]
            

#===LIGHT CURVE===
@dataclass
class ObsLightCurve(ObsSet):
    no_points: int = None
    frames: list[ObsDopplerFrame] = None
        
    def __post_init__(self):
        self._parse()
        
    def _parse(self):

        points_idx = self._find_line('{number of samples', self.set_lines)
        self.no_points = int(self.set_lines[points_idx].split()[0])
        
        frame_start_idx = points_idx + 2
        for line in self.lines[frame_start_idx:frame_start_idx + self.no_frames]:
            parts = line.split()
            frame = ObsLightCurveFrame(
                fname=parts[0],
                calfact_freeze=parts[1],
                calfact=float(parts[2]),
                weight=float(parts[3]),
            )
            self.frames.append(frame)