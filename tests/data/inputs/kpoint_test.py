# -*- coding: utf-8 -*-


"""
Test suite for the VaspKpointData datatype and the related KpointWrapper
utility
"""


import pytest

from pymatgen.io.vasp.inputs import Kpoints_supported_modes, Poscar, Kpoints
from pymatgen.core import Structure, Lattice
from pymatgen.symmetry.bandstructure import HighSymmKpath
from aiida.orm import StructureData

from aiida_cusp.data.inputs.vasp_kpoint import VaspKpointData
from aiida_cusp.data.inputs.vasp_kpoint import KpointWrapper
from aiida_cusp.data.inputs.vasp_kpoint import KpointWrapperError


def test_unknown_init_mode_raises():
    kpoint_params = {
        'mode': 'gamma',
        'kpoints': 1,
    }
    with pytest.raises(KpointWrapperError) as exception:
        kpoints = KpointWrapper(kpoint_params)
    assert "Unsupported initialization mode" in str(exception.value)


def test_automatic_mode():
    kpoint_params = {
        'mode': 'auto',
        'kpoints': 10,
    }
    kpoints = KpointWrapper(kpoints=kpoint_params)
    assert kpoints.style == Kpoints_supported_modes.Automatic
    assert kpoints.kpts == [[10]]
    assert kpoints.num_kpts == 0
    assert kpoints.kpts_shift == (.0, .0, .0)


def test_gamma_explicit_mode():
    # grid without shift
    kpoint_params = {
        'mode': 'gamma',
        'kpoints': [5, 5, 5],
    }
    kpoints = KpointWrapper(kpoints=kpoint_params)
    assert kpoints.style == Kpoints_supported_modes.Gamma
    assert kpoints.kpts == [[5, 5, 5]]
    assert kpoints.num_kpts == 0
    assert kpoints.kpts_shift == [.0, .0, .0]
    # grid with shift
    kpoint_params = {
        'mode': 'gamma',
        'kpoints': [5, 5, 5],
        'shift': [.1, .2, .3],
    }
    kpoints = KpointWrapper(kpoints=kpoint_params)
    assert kpoints.style == Kpoints_supported_modes.Gamma
    assert kpoints.kpts == [[5, 5, 5]]
    assert kpoints.num_kpts == 0
    assert kpoints.kpts_shift == [.1, .2, .3]


def test_monkhorst_explicit_mode():
    # grid without shift
    kpoint_params = {
        'mode': 'monkhorst',
        'kpoints': [4, 4, 4],
    }
    kpoints = KpointWrapper(kpoints=kpoint_params)
    assert kpoints.style == Kpoints_supported_modes.Monkhorst
    assert kpoints.kpts == [[4, 4, 4]]
    assert kpoints.num_kpts == 0
    assert kpoints.kpts_shift == [.0, .0, .0]
    # grid with shift
    kpoint_params = {
        'mode': 'monkhorst',
        'kpoints': [4, 4, 4],
        'shift': [.1, .2, .3],
    }
    kpoints = KpointWrapper(kpoints=kpoint_params)
    assert kpoints.style == Kpoints_supported_modes.Monkhorst
    assert kpoints.kpts == [[4, 4, 4]]
    assert kpoints.num_kpts == 0
    assert kpoints.kpts_shift == [.1, .2, .3]


def test_gamma_density_mode():
    # setup minimal structure
    lattice = Lattice.cubic(1.0)
    species = ['H']
    coords = [[.0, .0, .0]]
    structure = Structure(lattice, species, coords)
    # kpoints
    kpoint_params = {
        'mode': 'gamma',
        'kpoints': 100.0,
    }
    kpoints = KpointWrapper(kpoints=kpoint_params, structure=structure)
    assert kpoints.style == Kpoints_supported_modes.Gamma
    assert kpoints.kpts == [[4, 4, 4]]
    assert kpoints.num_kpts == 0
    assert kpoints.kpts_shift == [.0, .0, .0]


def test_monkhorst_density_mode():
    # setup minimal structure
    lattice = Lattice.cubic(1.0)
    species = ['H']
    coords = [[.0, .0, .0]]
    structure = Structure(lattice, species, coords)
    # kpoints
    kpoint_params = {
        'mode': 'monkhorst',
        'kpoints': 100.0,
    }
    kpoints = KpointWrapper(kpoints=kpoint_params, structure=structure)
    assert kpoints.style == Kpoints_supported_modes.Monkhorst
    assert kpoints.kpts == [[4, 4, 4]]
    assert kpoints.num_kpts == 0
    assert kpoints.kpts_shift == [.0, .0, .0]


def test_automatic_line_mode():
    # setup minimal structure
    lattice = Lattice.cubic(1.0)
    species = ['H']
    coords = [[.0, .0, .0]]
    structure = Structure(lattice, species, coords)
    # build high symmetry path
    sympath = HighSymmKpath(structure, path_type='sc')
    generated_kpoints = [  # list of kpoints forming HighSymmKpath
        ([0.0, 0.0, 0.0], "\\Gamma"),
        ([0.0, 0.5, 0.0], "X"),
        ([0.0, 0.5, 0.0], "X"),
        ([0.5, 0.5, 0.0], "M"),
        ([0.5, 0.5, 0.0], "M"),
        ([0.0, 0.0, 0.0], "\\Gamma"),
        ([0.0, 0.0, 0.0], "\\Gamma"),
        ([0.5, 0.5, 0.5], "R"),
        ([0.5, 0.5, 0.5], "R"),
        ([0.0, 0.5, 0.0], "X"),
        ([0.5, 0.5, 0.0], "M"),
        ([0.5, 0.5, 0.5], "R"),
    ]
    # setup the kpoints object using the wrapper
    kpoint_params = {
        'mode': 'line',
        'kpoints': 100,
        'sympath': sympath,
    }
    kpoints = KpointWrapper(kpoints=kpoint_params)
    # need to use real list of lists here because pytest is a bit picky here
    kpts = list(list(zip(*generated_kpoints))[0])
    labels = list(list(zip(*generated_kpoints))[1])
    assert kpoints.style == Kpoints_supported_modes.Line_mode
    # transform kpoint list of numpy.arrays to list of lists
    assert list(map(list, kpoints.kpts)) == kpts
    assert kpoints.num_kpts == 100
    assert kpoints.labels == labels
    assert kpoints.kpts_shift == (0., 0., 0.)


def test_init_from_structure_types():
    # setup minimal structure
    lattice = Lattice.cubic(1.0)
    species = ['H']
    coords = [[.0, .0, .0]]
    # kpoint setup
    kpoint_params = {
        'mode': 'gamma',
        'kpoints': 100.0,
    }
    # setup different structure types
    pmg_structure = Structure(lattice, species, coords)
    pmg_poscar = Poscar(pmg_structure)
    aiida_structure = StructureData(pymatgen_structure=pmg_structure)
    # initialize kpoints from density for different structure types
    for struct in [pmg_structure, pmg_poscar, aiida_structure]:
        kpoints = KpointWrapper(kpoints=kpoint_params, structure=struct)
        assert kpoints.style == Kpoints_supported_modes.Gamma
        assert kpoints.kpts == [[4, 4, 4]]
        assert kpoints.num_kpts == 0
        assert kpoints.kpts_shift == [.0, .0, .0]


def test_init_from_kpoint_object():
    # get kpoints object
    pmg_kpoints = Kpoints.automatic(100)
    wrapper_kpoints = KpointWrapper(kpoints=pmg_kpoints)
    assert pmg_kpoints.__str__ == wrapper_kpoints.__str__
