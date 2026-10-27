#Last modified @recannon 20261027

import shutil
from pathlib import Path
import numpy as np
import pytest
import trimesh
from pyshape.mod.mod_io import modFile
from pyshape.mod.export_obj import shape2obj

#===Sample files===

SAMPLES = Path(__file__).parent
SAMPLE_ELLIP  = SAMPLES / "sample_ellip.mod"
SAMPLE_VERTEX = SAMPLES / "sample_vertex.mod"

#===Helpers===
#These are ignored by pytest (not a fixture and don't start with test_)

def load(path):
    return modFile.from_file(str(path))

def load_obj(path):
    return trimesh.load(path)

def make_copy(src, tmp_path):
    dest = tmp_path / src.name
    shutil.copy(src, dest)
    return dest

#===Fixtures===
#These create copies of files and return the path every time called
#Stops tests interfering with eachother

@pytest.fixture
def ellip_file(tmp_path):
    return make_copy(SAMPLE_ELLIP, tmp_path)

@pytest.fixture
def vertex_file(tmp_path):
    return make_copy(SAMPLE_VERTEX, tmp_path)

#===Tests===

class TestError:

    def test_non_vertex_model_raises(self, ellip_file):
        with pytest.raises(ValueError):
            shape2obj(ellip_file)

    def test_non_vertex_model_writes_nothing(self, ellip_file):
        with pytest.raises(ValueError):
            shape2obj(ellip_file)
        assert not ellip_file.with_suffix('.obj').exists()

class TestGeometry:

    def test_counts_and_vertices_survive(self, vertex_file):
        comp = load(vertex_file).components[0]
        mesh = load_obj(shape2obj(vertex_file))
        assert len(mesh.vertices) == len(comp.vertices)
        assert len(mesh.faces) == len(comp.facets)
        np.testing.assert_allclose(mesh.vertices, comp.vertices)

    def test_mesh_is_closed_with_outward_normals(self, vertex_file):
        """A wrong index offset scrambles topology, so this fails if it is wrong.
        Only valid if the sample is a closed shape."""
        mesh = load_obj(shape2obj(vertex_file))
        assert mesh.is_watertight
        assert mesh.volume > 0, "Negative volume means inverted facet winding"