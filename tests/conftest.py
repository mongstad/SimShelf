import pytest

from simshelf.store import Store


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "simulation"
    root.mkdir()
    source = root / "field.py"
    source.write_text('SIMSHELF_VERSION = "1.0"\nvalue = 2\n')
    store = Store(tmp_path / "workspace")
    sim = store.add_simulation(root, name="Field", entrypoint="field.py")
    return store, sim, root, source
