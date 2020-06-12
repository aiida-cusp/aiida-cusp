# -*- coding: utf-8 -*-


"""
Collection of pytest fixtures for plugin tests
"""

import pytest

# make fixtures defined by AiiDA available
pytest_plugins = ['aiida.manage.tests.pytest_fixtures']


@pytest.fixture(scope='function', autouse=True)
def auto_clear_aiidadb(clear_database):
    """
    Automatically run clear_database_after_test() after every test function
    """
    pass


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
def aiida_sandbox():
    """
    Create and return an AiiDA sandbox folder (used for instance as argument
    in the prepare_for_submission() calculator methods
    """
    from aiida.common.folders import SandboxFolder
    with SandboxFolder() as sandbox:
        yield sandbox


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
def multi_component_structure():
    """
    Setup a complex pymatgen structure (i.e. Li6PS5Br) comprising multiple
    different species.
    """
    from pymatgen import Lattice, Structure
    lattice = Lattice.cubic(a=1.0E1)
    species, positions = list(zip(*[
        ('Li', [0.183, 0.183, 0.024]),
        ('S', [0.250, 0.250, 0.250]),
        ('S', [0.618, 0.618, 0.618]),
        ('P', [0.500, 0.500, 0.500]),
        ('Br', [0.000, 0.000, 0.000]),
    ]))
    structure = Structure.from_spacegroup(216, lattice, species, positions)
    yield structure


@pytest.fixture(scope='function')
def vasp_code(computer):
    """
    Setup a new code object.
    """
    from aiida.orm import Code
    code = Code(remote_computer_exec=(computer, '/path/to/vasp'))
    code.label = 'vaspcode'
    code.set_prepend_text('vasp code prepend')
    code.set_append_text('vasp code append')
    # do not store the code yet such that the default plugin can be set later
    yield code


@pytest.fixture(scope='function')
def cstdn_code(computer):
    """
    Setup a new code object.
    """
    from aiida.orm import Code
    code = Code(remote_computer_exec=(computer, '/path/to/cstdn'))
    code.label = 'cstdncode'
    code.set_prepend_text('custodian code prepend')
    code.set_append_text('custodian code append')
    # do not store the code yet such that the default plugin can be set later
    yield code


@pytest.fixture(scope='function')
def computer(tmpdir):
    """
    Setup a new computer object.
    """
    from aiida.orm import Computer, User
    computer = Computer(name='local_computer', hostname='localhost')
    computer.set_scheduler_type('direct')
    computer.set_transport_type('local')
    computer.set_workdir(str(tmpdir))
    computer.set_default_mpiprocs_per_machine(1)
    computer.set_mpirun_command(['mpirun', '-np', '{tot_num_mpiprocs}'])
    computer.store()
    computer.configure(user=User.objects.get_default())
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
def with_pbe_potcars(interactive_potcar_file):
    """
    Create and store a set of (PBE) potcars used in the different tests
    """
    import pathlib
    from aiida_cusp.data.inputs.vasp_potcar import VaspPotcarFile
    # define the basic attributes of the potentials stored to the set
    potcar_contents = [
        (
            "Li", "pbe",
            "\n".join([
                " PAW_PBE Li 17Jan2003",
                " 1.00000000000000000",
                " parameters from PSCTR are:",
                "   VRHFIN =Li: s1p0",
                "   TITEL  = PAW_PBE Li 17Jan2003",
                "END of PSCTR-controll parameters",
            ])
        ),  # end entry: Li
        (
            "Br", "pbe",
            "\n".join([
                " PAW_PBE Br 06Sep2000",
                " 7.00000000000000000",
                " parameters from PSCTR are:",
                "   VRHFIN =Br: s2p5",
                "   TITEL  = PAW_PBE Br 06Sep2000",
                "END of PSCTR-controll parameters",
            ])
        ),  # end entry: Br
        (
            "S", "pbe",
            "\n".join([
                " PAW_PBE S 17Jan2003",
                " 6.00000000000000000",
                " parameters from PSCTR are:",
                "   VRHFIN =S : s2p4",
                "   TITEL  = PAW_PBE S 17Jan2003",
                "END of PSCTR-controll parameters",
            ])
        ),  # end entry: S
        (
            "P", "pbe",
            "\n".join([
                " PAW_PBE P 17Jan2003",
                " 5.00000000000000000",
                " parameters from PSCTR are:",
                "   VRHFIN =P : s2p3",
                "   TITEL  = PAW_PBE P 17Jan2003",
                "END of PSCTR-controll parameters",
            ])
        ),  # end entry: P
        (
            "H", "pbe",
            "\n".join([
                " PAW_PBE H 15Jun2001",
                " 1.00000000000000000",
                " parameters from PSCTR are:",
                "   VRHFIN =H: ultrasoft test",
                "   TITEL  = PAW_PBE H 15Jun2001",
                "END of PSCTR-controll parameters",
            ])
        ),  # end entry: H
    ]  # end potcar_contents
    # store defined potentials
    for name, functional, potcar_content in potcar_contents:
        # open interative potcar file and erase all possible contents
        interactive_potcar_file.open("POTCAR")
        interactive_potcar_file.erase()
        # write the new pseudo-potential contents to the file and store it
        # to the database
        interactive_potcar_file.write(potcar_content)
        path_to_potcar = pathlib.Path(interactive_potcar_file.filepath)
        node = VaspPotcarFile.add_potential(path_to_potcar, name=name,
                                            functional=functional)
        node.store()
