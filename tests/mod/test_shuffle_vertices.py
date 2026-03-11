#Last modified by @recannon 10/03/2026
#Tests for pyshape.mod.shuffle_vertices

import pytest
import shutil
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


def shuffle_and_reload(path, reorder=False):
    shuffle_vertices(str(path), reorder=reorder)
    return load(path)

#===Fixtures===
#These create copies of files and return the path every time called
#Stops tests interfering with eachother

@pytest.fixture
def vertex_file(tmp_path):
    return make_copy(SAMPLE_VERTEX, tmp_path)

#===Tests===

class TestOption_v:

    def test_free_all(self, vertex_file):
        """Freeing should affect both offsets/scale and vertex deviations."""
        mod = freeze_and_reload(vertex_file, 'v', 'f')
        comp = mod.components[0]
        assert all(f == 'f' for f in comp.values_freeze), \
            "Offsets/scale should be free"
        assert all(f == 'f' for f in comp.vertices_freeze), \
            "Vertex deviations should be free"

    def test_reorder_vertices(self, vertex_file):
        original = load(SAMPLE_VERTEX)
        shuffle_vertices(vertex_file)
        shuffle_and_reload(vertex_file, reorder=True)
        assert list(original.components[0].values) == pytest.approx(list(mod.components[0].values))
