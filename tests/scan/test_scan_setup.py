#Last modified by @recannon 20261125
#Tests for functions within run_grid

#This file should have tests for writing and subscans as well

import numpy as np

import pyshape.scan.run_grid as rg
from pyshape.io.scan_io import ParamInfo

#===Tests===

class TestPolescanSetup:

    def test_polescan_no_duplicates(self):
        a1, a0 = rg.create_polescan_lists(-90, 90, 30, 0, 360, 30)
        pairs = list(zip(a1, a0))
        assert len(pairs) == len(set(pairs))
        
    def test_polescan_poles_have_single_entry(self):
        a1, _ = rg.create_polescan_lists(-90, 90, 30, 0, 360, 30)
        assert np.sum(a1 == 0) == 1       # beta = +90
        assert np.sum(a1 == 180) == 1     # beta = -90
        
class TestBuildGrid:
    
    def test_build_grid_generic(self):
        p1 = ParamInfo("shape0", "scale", 1, 5, 1)
        p2 = ParamInfo("rs0", "C", 1, 3, 1)
        p1_vals, p2_vals, polescan = rg.build_grid(p1, p2)
        assert polescan is False
        assert len(p1_vals) == len(p2_vals) == 15
        assert set(zip(p1_vals, p2_vals)) == {(a, b) for a in (1,2,3,4,5) for b in (1,2,3)}
 

    def test_build_grid_detects_polescan(self):
        _, _, polescan  = rg.build_grid(ParamInfo("spin", "angle1", 0, 0, 1),
                                        ParamInfo("spin", "angle0", 0, 360, 90))
        _, _, polescan2 = rg.build_grid(ParamInfo("spin", "period", 1, 2, 1),
                                        ParamInfo("spin", "angle2", 0, 10, 5))
        assert polescan  is True
        assert polescan2 is False
        


 
    