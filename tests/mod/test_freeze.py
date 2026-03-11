#Last modified by @recannon 10/03/2026
#Tests for pyshape.mod.freeze

import pytest
import shutil
from pathlib import Path

from pyshape.mod.mod_io import modFile
from pyshape.mod.freeze import freeze_mod

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

def freeze_and_reload(path, mod_type, freeze, components=None):
    freeze_mod(str(path), mod_type, freeze, components)
    return load(path)

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

class TestValidation:

    def test_wrong_component_type_exits(self, ellip_file):
        """Requesting a component type that doesn't match the file should exit."""
        with pytest.raises(SystemExit):
            freeze_mod(str(ellip_file), 'v', 'f')
            
    def test_out_of_range_component_exits(self, ellip_file):
        with pytest.raises(SystemExit):
            freeze_mod(str(ellip_file), 'e', 'f', components=[99])

class TestOption_e:

    def test_free_all(self, ellip_file):
        mod = freeze_and_reload(ellip_file, 'e', 'f')
        for i, comp in enumerate(mod.components):
            assert all(f == 'f' for f in comp.values_freeze), \
                f"Component {i} has non-free params after freeing all"

    def test_free_single_component_only_affects_that_one(self, ellip_file):
        mod = freeze_and_reload(ellip_file, 'e', 'f', components=[0])
        assert all(f == 'f' for f in mod.components[0].values_freeze), \
            "Component 0 should be free"
        assert all(f == 'c' for f in mod.components[1].values_freeze), \
            "Component 1 should be unchanged"

    def test_values_unchanged_after_state_change(self, ellip_file):
        original = load(SAMPLE_ELLIP)
        mod = freeze_and_reload(ellip_file, 'e', 'f')
        for i, (c_orig, c_new) in enumerate(zip(original.components, mod.components)):
            assert list(c_orig.values) == pytest.approx(list(c_new.values)), \
                f"Component {i} numeric values changed after state change"

class TestOption_h:

    def test_free_all(self, harmonic_file):
        """Freeing should affect both offsets/scale and harmonic coefficients."""
        mod = freeze_and_reload(harmonic_file, 'h', 'f')
        comp = mod.components[0]
        assert all(f == 'f' for f in comp.values_freeze), \
            "Offsets/scale should be free"
        assert all(f == 'f' for f in comp.coeffs_freeze), \
            "Harmonic coefficients should be free"

    def test_free_single_component_only_affects_that_one(self, harmonic_file):
        mod = freeze_and_reload(harmonic_file, 'h', 'f', components=[0])
        assert all(f == 'f' for f in mod.components[0].values_freeze), \
            "Component 0 should be free"
        assert all(f == 'c' for f in mod.components[1].values_freeze), \
            "Component 1 should be unchanged"

    def test_values_unchanged_after_state_change(self, harmonic_file):
        original = load(SAMPLE_HARMONIC)
        mod = freeze_and_reload(harmonic_file, 'h', 'f')
        assert list(original.components[0].values) == pytest.approx(list(mod.components[0].values))
        assert list(original.components[0].coeffs) == pytest.approx(list(mod.components[0].coeffs))

class TestOption_v:

    def test_free_all(self, vertex_file):
        """Freeing should affect both offsets/scale and vertex deviations."""
        mod = freeze_and_reload(vertex_file, 'v', 'f')
        comp = mod.components[0]
        assert all(f == 'f' for f in comp.values_freeze), \
            "Offsets/scale should be free"
        assert all(f == 'f' for f in comp.vertices_freeze), \
            "Vertex deviations should be free"

    def test_values_unchanged_after_state_change(self, vertex_file):
        original = load(SAMPLE_VERTEX)
        mod = freeze_and_reload(vertex_file, 'v', 'f')
        assert list(original.components[0].values) == pytest.approx(list(mod.components[0].values))


class TestOption_s:

    def test_frees_correct_vals(self, ellip_file):
        mod = freeze_and_reload(ellip_file, 's', 'f')
        ss = mod.spinstate
        assert ss.lam_freeze == 'f', "lam should be free"
        assert ss.bet_freeze == 'f', "bet should be free"
        assert ss.phi_freeze == 'f', "phi should be free"
        assert ss.P_freeze   == 'f', "P should be free"

    def test_values_unchanged_after_state_change(self, ellip_file):
        original = load(SAMPLE_ELLIP)
        mod = freeze_and_reload(ellip_file, 's', 'f')
        assert list(original.spinstate.values) == pytest.approx(list(mod.spinstate.values))


class TestOption_p:

    def test_frees_correct_vals(self, ellip_file):
        """'p' should free phi and P, leaving lam and bet unchanged."""
        mod = freeze_and_reload(ellip_file, 'p', 'f')
        ss = mod.spinstate
        assert ss.phi_freeze == 'f', "phi should be free"
        assert ss.P_freeze   == 'f', "P should be free"
        assert ss.lam_freeze == 'c', "lam should be unchanged"
        assert ss.bet_freeze == 'c', "bet should be unchanged"
        
    def test_values_unchanged_after_state_change(self, ellip_file):
        original = load(SAMPLE_ELLIP)
        mod = freeze_and_reload(ellip_file, 'p', 'f')
        assert list(original.spinstate.values) == pytest.approx(list(mod.spinstate.values))


