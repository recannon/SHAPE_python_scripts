#Last modified by @recannon 20261126
#Tests for functions within utils.py

import numpy as np
import pytest
from pyshape import utils
from astropy.time import Time

#===Tests===

class TestTimeFormatting:
    
    @pytest.mark.parametrize('shape', [
                             '2024 9 7 13 5 9',
                             '2024  9  7 13  5  9',
                           '  2024  9  7 13  5  9  ',
                             '2024 09 07 13 05 09'
                             ])
    def test_time_shape2astropy_works(self, shape):
        '''Tests date above with different formatting'''
        assert utils.time_shape2astropy(shape).iso == '2024-09-07 13:05:09.000'

    def test_time_astropy2shape_works(self):
        '''Tests some arbitrary dates and check padding'''
        t1 = Time("2024-09-07 13:05:09", scale="utc")
        t2 = Time("2024-12-31 23:59:59", scale="utc")
        assert utils.time_astropy2shape(t1) == "2024  9  7 13  5  9"
        assert utils.time_astropy2shape(t2) == "2024 12 31 23 59 59"

    @pytest.mark.parametrize('shape2', [
        '2024  9  7 13  5  9',
        '2023 12 31 23 59 59',
        '2024  1  1  0  0  0',
        '2024  2 29 12 30 30',
        '1999  7  4  6  8 10',
    ])
    def test_roundtrip(self,shape2):
        assert utils.time_astropy2shape(utils.time_shape2astropy(shape2)) == shape2
