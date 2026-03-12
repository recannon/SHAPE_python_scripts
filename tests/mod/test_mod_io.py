#Last modified by @recannon 12/03/2026
#Tests for pyshape.mod.mod_io

import pytest
import shutil
import numpy as np
from pathlib import Path

from pyshape.mod.mod_io import modFile

#===Sample files===

SAMPLES = Path(__file__).parent
SAMPLE_ELLIP    = SAMPLES / "sample_ellip.mod"
SAMPLE_VERTEX   = SAMPLES / "sample_vertex.mod"
SAMPLE_HARMONIC = SAMPLES / "sample_harmonic.mod"

#===Helpers===
#These are ignored by pytest (not a fixture and don't start with test_)

def load(path):
    return modFile.from_file(str(path))

def make_copy(src, tmp_path):
    dest = tmp_path / src.name
    shutil.copy(src, dest)
    return dest

def assert_component_values_match(c_orig, c_new, i):
    assert list(c_orig.values) == pytest.approx(list(c_new.values)), \
        f"Component {i} numeric values changed after round-trip"
    assert list(c_orig.values_freeze) == list(c_new.values_freeze), \
        f"Component {i} freeze states changed after round-trip"

def assert_phot_functions_match(mod_in, mod_out):
    for i, (rl_orig, rl_new) in enumerate(zip(mod_in.phot_functions.radar, mod_out.phot_functions.radar)):
        assert list(rl_orig.values) == pytest.approx(list(rl_new.values)), \
            f"Radar law {i} numeric values changed after round-trip"
        assert list(rl_orig.values_freeze) == list(rl_new.values_freeze), \
            f"Radar law {i} freeze states changed after round-trip"
    for i, (ol_orig, ol_new) in enumerate(zip(mod_in.phot_functions.optical, mod_out.phot_functions.optical)):
        assert list(ol_orig.values) == pytest.approx(list(ol_new.values)), \
            f"Optical law {i} numeric values changed after round-trip"
        assert list(ol_orig.values_freeze) == list(ol_new.values_freeze), \
            f"Optical law {i} freeze states changed after round-trip"

def assert_spinstate_matches(mod_in, mod_out):
    assert list(mod_in.spinstate.values) == pytest.approx(list(mod_out.spinstate.values)), \
        "Spin state numeric values changed after round-trip"
    assert list(mod_in.spinstate.values_freeze) == list(mod_out.spinstate.values_freeze), \
        "Spin state freeze states changed after round-trip"

#===Fixtures===
#These create copies of files and return the path every time called
#Stops tests interfering with eachother

@pytest.fixture
def ellip_file(tmp_path):
    return make_copy(SAMPLE_ELLIP, tmp_path)

@pytest.fixture
def vertex_file(tmp_path):
    return make_copy(SAMPLE_VERTEX, tmp_path)

@pytest.fixture
def harmonic_file(tmp_path):
    return make_copy(SAMPLE_HARMONIC, tmp_path)

#===Tests===
#Round trip tests only

def test_round_trip_ellipse(ellip_file):
    mod_in = load(SAMPLE_ELLIP)
    mod_in.write(str(ellip_file))
    mod_out = load(ellip_file)
    for i, (c_orig, c_new) in enumerate(zip(mod_in.components, mod_out.components)):
        assert_component_values_match(c_orig, c_new, i)
    assert_phot_functions_match(mod_in, mod_out)
    assert_spinstate_matches(mod_in, mod_out)

def test_round_trip_harmonic(harmonic_file):
    mod_in = load(SAMPLE_HARMONIC)
    mod_in.write(str(harmonic_file))
    mod_out = load(harmonic_file)
    for i, (c_orig, c_new) in enumerate(zip(mod_in.components, mod_out.components)):
        assert_component_values_match(c_orig, c_new, i)
        assert list(c_orig.coeffs) == pytest.approx(list(c_new.coeffs)), \
            f"Component {i} harmonic coefficients changed after round-trip"
        assert list(c_orig.coeffs_freeze) == list(c_new.coeffs_freeze), \
            f"Component {i} coefficient freeze states changed after round-trip"
    assert_phot_functions_match(mod_in, mod_out)
    assert_spinstate_matches(mod_in, mod_out)

def test_round_trip_vertex(vertex_file):
    mod_in = load(SAMPLE_VERTEX)
    mod_in.write(str(vertex_file))
    mod_out = load(vertex_file)
    for i, (c_orig, c_new) in enumerate(zip(mod_in.components, mod_out.components)):
        assert_component_values_match(c_orig, c_new, i)
        assert np.allclose(c_orig.vertices, c_new.vertices), \
            f"Component {i} vertices changed after round-trip"
        assert np.array_equal(c_orig.facets, c_new.facets), \
            f"Component {i} facets changed after round-trip"
        assert list(c_orig.vertices_freeze) == list(c_new.vertices_freeze), \
            f"Component {i} vertex freeze states changed after round-trip"
    assert_phot_functions_match(mod_in, mod_out)
    assert_spinstate_matches(mod_in, mod_out)