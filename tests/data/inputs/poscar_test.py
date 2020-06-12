# -*- coding: utf-8 -*-


"""
Test suite for the VaspPoscarData and the related PoscarWrapper utility
"""


import pytest
import pathlib

from aiida.orm import StructureData
from pymatgen.core import Lattice, Structure
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.io.vasp.inputs import Poscar

from aiida_cusp.data.inputs.vasp_poscar import VaspPoscarData
from aiida_cusp.data.inputs.vasp_poscar import PoscarWrapper
from aiida_cusp.utils.exceptions import PoscarWrapperError


#
# Tests for PoscarWrapper
#
def test_empty_structure_raises():
    with pytest.raises(PoscarWrapperError) as exception:
        poscar = PoscarWrapper()
    assert "Missing non-optional parameter" in str(exception.value)


def test_small_structure_init_from_temp_raises(minimal_pymatgen_structure):
    kwargs = {
        'structure': minimal_pymatgen_structure,
        'temperature': 300.0,
    }
    with pytest.raises(PoscarWrapperError) as exception:
        poscar = PoscarWrapper(**kwargs)
    assert "Initialization of velocities from" in str(exception.value)


def test_temp_below_zero_raises(minimal_pymatgen_structure):
    kwargs = {
        # assure structure contains at least two atoms
        'structure': minimal_pymatgen_structure * (2, 1, 1),
        'temperature': -1.0,
    }
    with pytest.raises(PoscarWrapperError) as exception:
        poscar = PoscarWrapper(**kwargs)
    assert "Given temperature must not be smaller" in str(exception.value)


def test_init_from_temperature(minimal_pymatgen_structure):
    kwargs = {
        # assure structure contains at least two atoms
        'structure': minimal_pymatgen_structure * (2, 1, 1),
        # use initialization at zero kelvin to generate reproducible results
        # since initialization at T =/= 0.0 K results in randomly drawn
        # velocities
        'temperature': 0.0,
    }
    poscar = PoscarWrapper(**kwargs)
    assert poscar.velocities == [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]


@pytest.mark.parametrize('selector1', [True, False])
@pytest.mark.parametrize('selector2', [True, False])
@pytest.mark.parametrize('selector3', [True, False])
def test_poscar_selective_dynamics(minimal_pymatgen_structure, selector1,
                                   selector2, selector3):
    constraints = [[selector1, selector2, selector3]]
    kwargs = {
        'structure': minimal_pymatgen_structure,
        'constraints': constraints,
    }
    poscar = PoscarWrapper(**kwargs)
    assert poscar.selective_dynamics == constraints


@pytest.mark.parametrize('v1', [-1.0, 0.0, +1.0])
@pytest.mark.parametrize('v2', [-1.0, 0.0, +1.0])
@pytest.mark.parametrize('v3', [-1.0, 0.0, +1.0])
def test_poscar_velocities(minimal_pymatgen_structure, v1, v2, v3):
    velocities = [[v1, v2, v3]]
    kwargs = {
        'structure': minimal_pymatgen_structure,
        'velocities': velocities,
    }
    poscar = PoscarWrapper(**kwargs)
    assert poscar.velocities == velocities


#
# Tests for VaspPoscarData
#
@pytest.mark.parametrize('constraints,velocities,temperature',
[   # noqa: E128
    ([[True, False, True]], None, None),
    (None, [[-1.0, -1.0, 1.0]], None),
    (None, None, 300.0),
])
def test_store_and_load_poscar_data(minimal_pymatgen_structure, constraints,
                                    velocities, temperature):
    from aiida.plugins import DataFactory
    from aiida.orm import load_node
    PoscarData = DataFactory('cusp.poscar')
    # assure at least two atoms are present in the structure to allow for
    # initialization of velocities from temperature
    if temperature is not None:
        pymatgen_structure = minimal_pymatgen_structure * (2, 1, 1)
    else:
        pymatgen_structure = minimal_pymatgen_structure
    poscar_set = PoscarData(structure=pymatgen_structure,
                            constraints=constraints, velocities=velocities,
                            temperature=temperature)
    uuid = poscar_set.store().uuid
    poscar_get = load_node(uuid)
    assert str(poscar_set.get_poscar()) == str(poscar_get.get_poscar())


@pytest.mark.parametrize('constraints,velocities,temperature',
[   # noqa: E128
    ([[True, False, True]], None, None),
    (None, [[-1.0, -1.0, 1.0]], None),
    (None, None, 300.0),
])
def test_write_file_method(minimal_pymatgen_structure, tmpdir,
                           velocities, constraints, temperature):
    from aiida.plugins import DataFactory
    # assure at least two atoms are present in the structure to allow for
    # initialization of velocities from temperature
    if temperature is not None:
        pymatgen_structure = minimal_pymatgen_structure * (2, 1, 1)
    else:
        pymatgen_structure = minimal_pymatgen_structure
    PoscarData = DataFactory('cusp.poscar')
    poscar = PoscarData(structure=pymatgen_structure,
                        constraints=constraints, velocities=velocities,
                        temperature=temperature)
    # write node contents to file
    filepath = pathlib.Path(tmpdir) / 'POSCAR'
    assert filepath.is_file() is False  # assert file is not there already
    poscar.write_file(str(filepath))
    assert filepath.is_file() is True   # assert file has been written
    # load contents from file and compare to node contents
    with open(filepath, 'r') as stored_poscar_file:
        written_contents = stored_poscar_file.read()
    assert written_contents == str(poscar.get_poscar())


def test_get_poscar_method(minimal_pymatgen_structure):
    poscar = VaspPoscarData(structure=minimal_pymatgen_structure)
    # assert retrieved poscar equals reference
    reference_poscar = Poscar(structure=minimal_pymatgen_structure)
    retrieved_poscar = poscar.get_poscar()
    assert str(retrieved_poscar) == str(reference_poscar)


def test_get_structure_method(minimal_pymatgen_structure):
    poscar = VaspPoscarData(structure=minimal_pymatgen_structure)
    # assert retrieved structure equals reference
    reference_structure = minimal_pymatgen_structure
    retrieved_structure = poscar.get_structure()
    assert str(retrieved_structure) == str(reference_structure)


def test_get_atoms_method(minimal_pymatgen_structure):
    poscar = VaspPoscarData(structure=minimal_pymatgen_structure)
    # assert retrieved atoms equal reference
    reference_atoms = AseAtomsAdaptor.get_atoms(minimal_pymatgen_structure)
    retrieved_atoms = poscar.get_atoms()
    assert str(retrieved_atoms) == str(reference_atoms)


def test_init_from_structure_types(minimal_pymatgen_structure):
    pymatgen_structure = minimal_pymatgen_structure
    pymatgen_poscar = Poscar(minimal_pymatgen_structure)
    aiida_structure = StructureData(pymatgen_structure=pymatgen_structure)
    reference_poscar = pymatgen_poscar
    # initialize poscar using different structure types
    for struct in [pymatgen_structure, pymatgen_poscar, aiida_structure]:
        poscar = VaspPoscarData(structure=struct)
        assert str(poscar.get_poscar()) == str(reference_poscar)


def test_description_string(minimal_pymatgen_structure):
    # check for single atom
    poscar = VaspPoscarData(structure=minimal_pymatgen_structure)
    assert poscar.get_description() == 'H1'
    # test for supercell with 8 atoms
    supercell = minimal_pymatgen_structure * (2, 2, 2)
    poscar = VaspPoscarData(structure=supercell)
    assert poscar.get_description() == 'H8'
    # test for a mixed structure containing two different atom types (note:
    # replace with atom for which pymatgen knows the electronegativity to
    # avoid annoying warnings)
    for index in range(0, len(supercell), 2):
        supercell.replace(index, 'Al')
    poscar = VaspPoscarData(structure=supercell)
    assert poscar.get_description() == 'Al4H4'
