# -*- coding: utf-8 -*-


"""
Test suite for the VaspKpointData datatype and the related KpointWrapper
utility
"""


import pytest
import pathlib

from pymatgen.io.vasp.inputs import Kpoints_supported_modes, Poscar, Kpoints
from pymatgen.symmetry.bandstructure import HighSymmKpath
from aiida.orm import StructureData

from aiida_cusp.data import VaspKpointData
from aiida_cusp.data.inputs.vasp_kpoint import KpointWrapper
from aiida_cusp.data.inputs.vasp_kpoint import KpointWrapperError


#
# Tests for VaspKpointData
#
@pytest.mark.parametrize('kpoint_params,structure,sympath',
[   # noqa: E128
    ({'mode': 'auto', 'kpoints': 100}, False, False),
    ({'mode': 'gamma', 'kpoints': [5, 5, 5]}, False, False),
    ({'mode': 'gamma', 'kpoints': [5, 5, 5], 'shift': [.1, .2, .3]}, False,
     False),
    ({'mode': 'gamma', 'kpoints': 100.0}, True, False),
    ({'mode': 'monkhorst', 'kpoints': [4, 4, 4]}, False, False),
    ({'mode': 'monkhorst', 'kpoints': [4, 4, 4], 'shift': [.1, .2, .3]}, False,
     False),
    ({'mode': 'monkhorst', 'kpoints': 100.0}, True, False),
    ({'mode': 'line', 'kpoints': 100}, False, True),
])
def test_store_and_load_kpoint_data_density(kpoint_params, structure,
                                            sympath,
                                            minimal_pymatgen_structure):
    from aiida.plugins import DataFactory
    from aiida.orm import load_node
    # setup minimal structure and high symmetry path
    struct = minimal_pymatgen_structure
    path = HighSymmKpath(struct, path_type='sc')
    # update kpoint parameters depending on set structure or high symmetry
    # path requirements
    if not structure:
        struct = None
    if sympath:
        kpoint_params.update({'sympath': path})
    # setup the kpoint data object
    KpointData = DataFactory('cusp.kpoints')
    kpoints_set = KpointData(kpoints=kpoint_params, structure=struct)
    # store and reload the object and finally compare to original inputs
    uuid = kpoints_set.store().uuid
    kpoints_get = load_node(uuid)
    assert str(kpoints_set.get_kpoints()) == str(kpoints_get.get_kpoints())


@pytest.mark.parametrize('kpoint_params,structure,sympath',
[   # noqa: E128
    ({'mode': 'auto', 'kpoints': 100}, False, False),
    ({'mode': 'gamma', 'kpoints': [5, 5, 5]}, False, False),
    ({'mode': 'gamma', 'kpoints': [5, 5, 5], 'shift': [.1, .2, .3]}, False,
     False),
    ({'mode': 'gamma', 'kpoints': 100.0}, True, False),
    ({'mode': 'monkhorst', 'kpoints': [4, 4, 4]}, False, False),
    ({'mode': 'monkhorst', 'kpoints': [4, 4, 4], 'shift': [.1, .2, .3]}, False,
     False),
    ({'mode': 'monkhorst', 'kpoints': 100.0}, True, False),
    ({'mode': 'line', 'kpoints': 100}, False, True),
])
def test_write_file_method(kpoint_params, structure, sympath, tmpdir,
                           minimal_pymatgen_structure):
    from aiida.plugins import DataFactory
    # setup minimal structure and high symmetry path
    struct = minimal_pymatgen_structure
    path = HighSymmKpath(struct, path_type='sc')
    # update kpoint parameters depending on set structure or high symmetry
    # path requirements
    if not structure:
        struct = None
    if sympath:
        kpoint_params.update({'sympath': path})
    # setup the kpoint data object
    KpointData = DataFactory('cusp.kpoints')
    kpoints = KpointData(kpoints=kpoint_params, structure=struct)
    # write node contents to file
    filepath = pathlib.Path(tmpdir) / 'KPOINTS'
    assert filepath.is_file() is False  # assert file is not there already
    kpoints.write_file(str(filepath))
    assert filepath.is_file() is True   # assert file has been written
    # load contents from file and compare to node contents
    with open(filepath, 'r') as stored_kpoints_file:
        written_contents = stored_kpoints_file.read()
    assert written_contents == str(kpoints.get_kpoints())


#
# Tests for KpointWrapper utility
#
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


def test_gamma_density_mode(minimal_pymatgen_structure):
    # setup minimal structure
    structure = minimal_pymatgen_structure
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


def test_monkhorst_density_mode(minimal_pymatgen_structure):
    # setup minimal structure
    structure = minimal_pymatgen_structure
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


def test_automatic_line_mode(minimal_pymatgen_structure):
    # setup minimal structure
    structure = minimal_pymatgen_structure
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


def test_init_from_structure_types(minimal_pymatgen_structure):
    # kpoint setup
    kpoint_params = {
        'mode': 'gamma',
        'kpoints': 100.0,
    }
    # setup different structure types
    pmg_structure = minimal_pymatgen_structure
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
    assert str(pmg_kpoints) == str(wrapper_kpoints)


@pytest.mark.parametrize('explicit_grid_list',
[   # noqa: E128
    [1, 1], [1, 1, 1, 1],
])
@pytest.mark.parametrize('explicit_grid_shift',
[   # noqa: E128
    [.1, .1], [.1, .1, .1, .1], None,
])
@pytest.mark.parametrize('explicit_grid_mode',
[   # noqa: E128
    'monkhorst', 'gamma',
])
def test_explicit_mode_kpoint_list_length(explicit_grid_list,
                                          explicit_grid_shift,
                                          explicit_grid_mode):
    # grid without shift
    kpoint_params = {
        'mode': explicit_grid_mode,
        'kpoints': explicit_grid_list,
        'shift': explicit_grid_shift,
    }
    with pytest.raises(KpointWrapperError) as exception:
        kpoints = KpointWrapper(kpoints=kpoint_params)
    assert "Expected list of length 3" in str(exception.value)
