# -*- coding: utf-8 -*-


"""
Collection of pytest fixtures for plugin tests
"""

import pytest

# make fixtures defined by AiiDA available
pytest_plugins = ['aiida.manage.tests.pytest_fixtures']


@pytest.fixture(scope='function')
def interactive_potcar_file(tmpdir):
    """
    Opens a variably named POTCAR file with interactive access to it's
    contents.
    """
    import pathlib

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
def temporary_cwd(tmpdir):
    """
    Switch the current working directory (CWD) to a temporary location and
    revert to the original CWD on exit.
    """
    import os
    import pathlib
    prev_cwd = pathlib.Path.cwd().absolute()
    os.chdir(tmpdir)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@pytest.fixture(scope='function')
def minimal_pymatgen_structure():
    """
    Create a minimal pymatgen structure object for a fictitious simple-cubic
    structure with a lattice constant of length 1.0 containing a single
    hydrogen atom located at the origin of the cell.
    """
    from pymatgen.core import Lattice, Structure
    # setup the simple-cubic lattice with H at the origin
    lattice = Lattice.cubic(1.0)
    species = ['H']
    coords = [[.0, .0, .0]]
    # setup pymatgen structure and associated poscar object
    pymatgen_structure = Structure(lattice, species, coords)
    yield pymatgen_structure


@pytest.fixture(scope='function')
def vasp_code(computer):
    """
    Setup a new code object.
    """
    from aiida.orm import Code
    code = Code(remote_computer_exec=(computer, '/path/to/vasp'))
    code.label = 'vaspcode'
    # do not store the code yet such that subsequent fixtures can use this
    # code as base for different input plugins
    yield code


@pytest.fixture(scope='function')
def cstdn_code(computer):
    """
    Setup a new code object.
    """
    from aiida.orm import Code
    code = Code(remote_computer_exec=(computer, '/path/to/cstdn'))
    code.label = 'cstdncode'
    # do not store the code yet such that subsequent fixtures can use this
    # code as base for different input plugins
    yield code


@pytest.fixture(scope='function')
def computer(tmpdir):
    """
    Setup a new computer object.
    """
    from aiida.orm import Computer
    computer = Computer(name='local_computer', hostname='localhost')
    computer.set_scheduler_type('direct')
    computer.set_transport_type('local')
    computer.set_workdir(str(tmpdir))
    computer.set_default_mpiprocs_per_machine(1)
    computer.set_mpirun_command(['mpirun', '-np', '{tot_num_mpiprocs}'])
    computer.store()
    yield computer


@pytest.fixture(scope='function')
def incar():
    """
    Create simple VaspIncarData instance.
    """
    from aiida_cusp.data import VaspIncarData
    yield VaspIncarData()


@pytest.fixture(scope='function')
def poscar(minimal_pymatgen_structure):
    """
    Create simple VaspPoscarData instance.
    """
    from aiida_cusp.data import VaspPoscarData
    yield VaspPoscarData(structure=minimal_pymatgen_structure)


@pytest.fixture(scope='function')
def kpoints():
    """
    Create simple VaspKpointData instance.
    """
    from aiida_cusp.data import VaspKpointData
    kpoints = {
        'mode': 'auto',
        'kpoints': 100,
    }
    yield VaspKpointData(kpoints=kpoints)


@pytest.fixture(scope='function')
def with_H_PBE_potcar(interactive_potcar_file):
    """
    Create and store hydrogen potcar with PBE functional.
    """
    import pathlib
    from aiida_cusp.data.inputs.vasp_potcar import VaspPotcarFile
    potcar_contents = "\n".join([
        " PAW_PBE H 15Jun2001",
        " 1.00000000000000000",
        " parameters from PSCTR are:",
        "   VRHFIN =H: ultrasoft test",
        "   TITEL  = PAW_PBE H 15Jun2001",
        "END of PSCTR-controll parameters",
    ])
    interactive_potcar_file.open("POTCAR")
    interactive_potcar_file.write(potcar_contents)
    path_to_potcar = pathlib.Path(interactive_potcar_file.filepath)
    node = VaspPotcarFile.add_potential(path_to_potcar, name='H',
                                        functional='pbe')
    node.store()
