#Last modified by @recannon 11/03/2026
#Tests for pyshape.mod.shuffle_vertices

import pytest
import shutil
import numpy as np
from pathlib import Path

from pyshape.mod.mod_io import modFile
from pyshape.mod.shuffle_vertices import shuffle_vertices

#===Sample files===

SAMPLES = Path(__file__).parent
SAMPLE_VERTEX   = SAMPLES / "sample_vertex.mod"


#===Helpers===
#These are ignored by pytest (not a fixture and don't start with test_)

def load(path):
    return modFile.from_file(str(path))

def make_copy(src, tmp_path):
    dest = tmp_path / src.name
    shutil.copy(src, dest)
    return dest

def shuffle_and_reload(path, reorder=False, seed=None):
    if seed is not None:
        rng = np.random.default_rng(seed=seed)
    else:
        rng = None
    shuffle_vertices(str(path), reorder=reorder, rng=rng)
    return load(path)

def get_face_coords(comp):
    """Return the actual vertex coordinates for each facet — order independent."""
    v = comp.vertices
    f = comp.facets
    return [tuple(sorted(map(tuple, v[face]))) for face in f]

#===Fixtures===
#These create copies of files and return the path every time called
#Stops tests interfering with eachother

@pytest.fixture
def vertex_file(tmp_path):
    return make_copy(SAMPLE_VERTEX, tmp_path)

#===Tests===
class TestApplyPermutation:
    """Tests for the shared _apply_permutation logic."""

    def test_facets_describe_same_geometry_after_shuffle(self, vertex_file):
        """Facets should still describe the same faces after shuffle."""
        original = load(SAMPLE_VERTEX)
        mod = shuffle_and_reload(vertex_file, reorder=False, seed=42)
        assert get_face_coords(original.components[0]) == get_face_coords(mod.components[0]), \
            "Faces should describe the same geometry after shuffle"

    def test_facets_describe_same_geometry_after_reorder(self, vertex_file):
        """Facets should still describe the same faces after reorder."""
        original = load(SAMPLE_VERTEX)
        mod = shuffle_and_reload(vertex_file, reorder=True)
        assert get_face_coords(original.components[0]) == get_face_coords(mod.components[0]), \
            "Faces should describe the same geometry after reorder"

    def test_values_unchanged_after_shuffle(self, vertex_file):
        """Non-vertex parameters should be untouched by shuffle."""
        original = load(SAMPLE_VERTEX)
        mod = shuffle_and_reload(vertex_file, reorder=False, seed=42)
        assert list(original.components[0].values) == pytest.approx(list(mod.components[0].values))

    def test_values_unchanged_after_reorder(self, vertex_file):
        """Non-vertex parameters should be untouched by reorder."""
        original = load(SAMPLE_VERTEX)
        mod = shuffle_and_reload(vertex_file, reorder=True)
        assert list(original.components[0].values) == pytest.approx(list(mod.components[0].values))


class TestOption_shuffle:

    def test_order_changes(self, vertex_file):
        """With a fixed seed, vertices should be in a different order after shuffle."""
        original = load(SAMPLE_VERTEX)
        mod = shuffle_and_reload(vertex_file, reorder=False, seed=42)
        assert not np.allclose(original.components[0].vertices, mod.components[0].vertices), \
            "Vertices should be in a different order after shuffle"

    def test_same_vertices_after_shuffle(self, vertex_file):
        """All vertices should still exist after shuffle, just reordered."""
        original = load(SAMPLE_VERTEX)
        mod = shuffle_and_reload(vertex_file, reorder=False, seed=42)
        orig_verts = set(map(tuple, original.components[0].vertices))
        new_verts  = set(map(tuple, mod.components[0].vertices))
        assert orig_verts == new_verts, \
            "Vertex set should be identical after shuffle"


class TestOption_reorder:

    def test_z_coords_descending(self, vertex_file):
        """After reorder, base_disp z-coordinates should be in descending order."""
        mod = shuffle_and_reload(vertex_file, reorder=True)
        z_coords = mod.components[0].base_disp[:, 2]
        assert all(z_coords[i] >= z_coords[i+1] for i in range(len(z_coords) - 1)), \
            "Z coordinates should be in descending order after reorder"