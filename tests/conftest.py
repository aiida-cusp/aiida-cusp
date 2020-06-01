# -*- coding: utf-8 -*-


"""
Collection of pytest fixtures for plugin tests
"""

import pytest
import pathlib
import tempfile

from pymatgen.core import Lattice, Structure


# make fixtures defined by AiiDA available
pytest_plugins = ['aiida.manage.tests.pytest_fixtures']


@pytest.fixture(scope='function')
def interactive_potcar_file(tmpdir):
    """
    Opens a variably named POTCAR file with interactive access to it's
    contents.
    """
    class InteractivePotcar(object):
        def __init__(self, tmpfolder):
            """Setup internal variables."""
            self._tmpfolder = pathlib.Path(tmpdir)
            self._filepath = None
            self._file = None

        @property
        def filepath(self):
            """Return the path to the file as string."""
            return str(self._filepath.absolute())

        def open(self, filename):
            """Open file with name `filename`."""
            self._filepath = self._tmpfolder / filename
            self._file = open(self._filepath, 'a+')

        def write(self, content):
            """Write contents given in `content` to the file."""
            self.check_file_open()
            self._file.write(content)
            self._file.flush()

        def erase(self):
            """Erase all contents from current file."""
            self.check_file_open()
            self._file.truncate(0)

        def close(self):
            """Close the currently open file handle."""
            if self._file:
                self._file.close()
            if self._filepath:
                self._filepath.unlink()
            self._file = None
            self._filepath = None

        def check_file_open(self):
            """Check if file handle is available."""
            if self._file is None:
                raise Exception("Unable to write contents to file, currently "
                                "no open file handle available.")
    return InteractivePotcar(tmpdir)


@pytest.fixture(scope='function')
def minimal_pymatgen_structure():
    """
    Create a minimal pymatgen structure object for a fictitious simple-cubic
    structure with a lattice constant of length 1.0 containing a single
    hydrogen atom located at the origin of the cell.
    """
    # setup the simple-cubic lattice with H at the origin
    lattice = Lattice.cubic(1.0)
    species = ['H']
    coords = [[.0, .0, .0]]
    # setup pymatgen structure and associated poscar object
    pymatgen_structure = Structure(lattice, species, coords)
    yield pymatgen_structure
