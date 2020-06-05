# -*- coding: utf-8 -*-
"""
Test suite for the VaspPotcarFile and VaspPotcarData datatypes
"""

import pytest
import pathlib

from pymatgen.io.vasp.inputs import Poscar
from aiida.orm import StructureData

from aiida_cusp.data.inputs.vasp_potcar import VaspPotcarFile, VaspPotcarData
from aiida_cusp.data.inputs.vasp_poscar import VaspPoscarData
from aiida_cusp.utils.exceptions import VaspPotcarFileError
from aiida_cusp.utils.exceptions import VaspPotcarDataError
from aiida_cusp.utils.exceptions import MultiplePotcarError
from aiida_cusp.utils.defaults import VaspDefaults
from aiida_cusp.utils import PotcarParser


#
# Tests for VaspPotcarFile class
#
def test_store_and_load_potcar_file(interactive_potcar_file, clear_database):
    from aiida.orm import load_node
    # potcar contents and attributes
    contents = "potcar file contents!"
    name = 'Ge_abc_de'
    element = 'Ge'
    version = 10000101
    functional = 'lda_us'
    checksum = 'hash12345'
    interactive_potcar_file.open("POTCAR")
    interactive_potcar_file.write(contents)
    path_to_potcar = interactive_potcar_file.filepath
    # initialize the VaspPotcarFile node
    potcar_set = VaspPotcarFile(path_to_potcar, name, element, version,
                                functional, checksum)
    uuid = potcar_set.store().uuid
    potcar_get = load_node(uuid)
    assert potcar_get.name == name
    assert potcar_get.version == version
    assert potcar_get.element == element
    assert potcar_get.hash == checksum
    assert potcar_get.functional == functional
    assert potcar_get.get_content() == contents


@pytest.mark.parametrize('potential_attrs',
[   # noqa: E128
    ('Xy_abc', 'Ge', 10000101, 'lda_us', 'hash'),  # invalid element in name
    ('xy_abc', 'Ge', 10000101, 'lda_us', 'hash'),  # invalid element in name
    ('Ge_abc', 'Xy', 10000101, 'lda_us', 'hash'),  # invalid element
    ('Ge_abc', 'Ge', 10000000, 'lda_us', 'hash'),  # invalid version
    ('Ge_abc', 'Ge', 10000101, 'abcdef', 'hash'),  # invalid functional
])
def test_invalid_attributes_raise(interactive_potcar_file, potential_attrs):
    interactive_potcar_file.open("POTCAR")
    path_to_potcar = interactive_potcar_file.filepath
    with pytest.raises(VaspPotcarFileError) as exception:
        potcar_node = VaspPotcarFile(path_to_potcar, *potential_attrs)


@pytest.mark.parametrize('query_args,num_match_expected',
[   # noqa: E128
    ({'name': 'Ge_a'}, 2),
    ({'name': 'Ge_b'}, 2),
    ({'name': 'Si_a'}, 2),
    ({'name': 'Si_b'}, 2),
    ({'element': 'Ge'}, 4),
    ({'element': 'Si'}, 4),
    ({'version': 10000101}, 4),
    ({'version': 10000102}, 4),
    ({'functional': 'lda_us'}, 8),
    ({'name': 'Si_a', 'version': 10000101}, 1),
    ({'checksum': 'hash5'}, 1),
])
def test_get_potential_from_tags(query_args, num_match_expected,
                                 interactive_potcar_file,
                                 clear_database_before_test):
    # build smalle potential database
    interactive_potcar_file.open("POTCAR")
    path_to_potcar = interactive_potcar_file.filepath
    potcar_identifiers = [
        ['Ge_a', 'Ge', 10000101, 'lda_us', 'hash1'],
        ['Ge_a', 'Ge', 10000102, 'lda_us', 'hash2'],
        ['Ge_b', 'Ge', 10000101, 'lda_us', 'hash3'],
        ['Ge_b', 'Ge', 10000102, 'lda_us', 'hash4'],
        ['Si_a', 'Si', 10000101, 'lda_us', 'hash5'],
        ['Si_a', 'Si', 10000102, 'lda_us', 'hash6'],
        ['Si_b', 'Si', 10000101, 'lda_us', 'hash7'],
        ['Si_b', 'Si', 10000102, 'lda_us', 'hash8'],
    ]
    for identifiers in potcar_identifiers:
        node = VaspPotcarFile(path_to_potcar, *identifiers)
        node.store()
    # perform different queries using the from_tags() method
    query_result = VaspPotcarFile.from_tags(**query_args)
    assert len(query_result) == num_match_expected


def test_potcar_is_unique_method(clear_database_before_test,
                                 interactive_potcar_file):
    # generate arbitrary potential and process it using the potcar parser
    potential_contents = "\n".join([
        "functional Si 01Jan2000",
        "parameters from PSCTR are:",
        "VRHFIN =Si: s100p100d100",
        "TITEL  = functional Xy 01Jan1000"
        "END of PSCTR-controll parameters",
    ])
    interactive_potcar_file.open("POTCAR")
    interactive_potcar_file.write(potential_contents)
    path_to_potcar = interactive_potcar_file.filepath
    potcar_parser = PotcarParser(path_to_potcar, functional='pbe',
                                 name='Si_abc')
    # check and assert uniqueness for clean database
    assert VaspPotcarFile.is_unique(potcar_parser) is True
    # now store the very same potential to the clean database and assert
    # that is_unique() raises
    node = VaspPotcarFile(path_to_potcar, potcar_parser.name,
                          potcar_parser.element, potcar_parser.version,
                          potcar_parser.functional, potcar_parser.hash)
    node.store()
    with pytest.raises(MultiplePotcarError) as exception:
        VaspPotcarFile.is_unique(potcar_parser)
    assert "Identical potential" in str(exception.value)
    # change the hash and check error message has changed
    potcar_parser.hash = "hash123"
    with pytest.raises(MultiplePotcarError) as exception:
        VaspPotcarFile.is_unique(potcar_parser)
    assert "Potential with matching identifiers" in str(exception.value)


def test_add_potential_classmethod(clear_database_before_test,
                                   interactive_potcar_file):
    # generate arbitrary potential and process it using the potcar parser
    potential_contents = "\n".join([
        "functional Si 01Jan2000",
        "parameters from PSCTR are:",
        "VRHFIN =Si: s100p100d100",
        "TITEL  = functional Xy 01Jan1000"
        "END of PSCTR-controll parameters",
    ])
    interactive_potcar_file.open("POTCAR")
    interactive_potcar_file.write(potential_contents)
    path_to_potcar = pathlib.Path(interactive_potcar_file.filepath)
    potcar_parser = PotcarParser(path_to_potcar, functional='pbe',
                                 name='Si_abc')
    potcar_node = VaspPotcarFile.add_potential(path_to_potcar, name='Si_abc',
                                               functional='pbe')
    assert potcar_node.name == potcar_parser.name
    assert potcar_node.element == potcar_parser.element
    assert potcar_node.version == potcar_parser.version
    assert potcar_node.hash == potcar_parser.hash
    assert potcar_node.functional == potcar_parser.functional.lower()


#
# Tests for VaspPotcarData class
#
def test_store_and_load_potcar_data(interactive_potcar_file, clear_database):
    from aiida.orm import load_node
    # generate arbitrary potential and process it using the potcar parser
    potential_contents = "\n".join([
        "functional Si 01Jan1000",
        "parameters from PSCTR are:",
        "VRHFIN =Si: s100p100d100",
        "TITEL  = functional Si 01Jan1000"
        "END of PSCTR-controll parameters",
    ])
    interactive_potcar_file.open("POTCAR")
    interactive_potcar_file.write(potential_contents)
    path_to_potcar = pathlib.Path(interactive_potcar_file.filepath)
    potcar_file_node = VaspPotcarFile.add_potential(path_to_potcar, name='Si',
                                                    functional='pbe')
    potcar_file_node.store()
    # create VaspPotcarData instance associated with the stored potential
    potcar_data_set = VaspPotcarData(name='Si', version=10000101,
                                     functional='pbe')
    uuid = potcar_data_set.store().uuid

    # load the data node and compare stored contents
    potcar_data_get = load_node(uuid)
    assert potcar_data_get.name == potcar_file_node.name
    assert potcar_data_get.version == potcar_file_node.version
    assert potcar_data_get.functional == potcar_file_node.functional
    assert potcar_data_get.element == potcar_file_node.element
    assert potcar_data_get.hash == potcar_file_node.hash
    assert potcar_data_get.filenode_uuid == potcar_file_node.uuid


@pytest.mark.parametrize('missing_prop', ['name', 'functional', 'version'])
def test_init_from_tags_rases_on_missing_parameters(missing_prop):
    # complete parameter list
    kwargs = {'name': 'Si', 'version': 10000101, 'functional': 'pbe'}
    kwargs.update({missing_prop: None})
    expected_error = "Missing non-optional argument '{}'".format(missing_prop)
    with pytest.raises(VaspPotcarDataError) as exception:
        potcar_data = VaspPotcarData(**kwargs)
    assert str(exception.value) == expected_error


def test_init_from_tags_raises_on_missing_node(clear_database_before_test):
    # try to initialize from non-existent potential
    with pytest.raises(VaspPotcarDataError) as exception:
        potcar_data = VaspPotcarData(name='Si', version=10000101,
                                     functional='pbe')
    assert "Unable to initialize VaspPotcarData" in str(exception.value)


def test_load_potential_file_node_from_uuid(clear_database_before_test,
                                            interactive_potcar_file):
    # generate arbitrary potential and process it using the potcar parser
    interactive_potcar_file.open("POTCAR")
    path = pathlib.Path(interactive_potcar_file.filepath).absolute()
    args = ['Si', 'Si', 10000101, 'pbe', 'hash']
    potcar_file_set = VaspPotcarFile(path, *args).store()
    # create VaspPotcarData instance associated with the stored potential
    potcar_data = VaspPotcarData(name='Si', version=10000101, functional='pbe')
    # load node from potcar_data instance
    potcar_file_get = potcar_data.load_potential_file_node()
    assert potcar_file_get.uuid == potcar_file_set.uuid
    assert potcar_file_get.hash == potcar_file_set.hash
    assert potcar_file_get.element == potcar_file_set.element
    assert potcar_file_get.functional == potcar_file_set.functional
    assert potcar_file_get.name == potcar_file_set.name


def test_load_potential_file_node_from_hash(clear_database_before_test,
                                            interactive_potcar_file):
    # generate arbitrary potential and process it using the potcar parser
    interactive_potcar_file.open("POTCAR")
    path = pathlib.Path(interactive_potcar_file.filepath).absolute()
    args = ['Si', 'Si', 10000101, 'pbe', 'hash']
    potcar_file_set = VaspPotcarFile(path, *args).store()
    # create VaspPotcarData instance associated with the stored potential but
    # change the associated uuid
    potcar_data = VaspPotcarData(name='Si', version=10000101, functional='pbe')
    potcar_data.update_dict({'filenode_uuid': "changed_uuid"})
    assert potcar_data.filenode_uuid == "changed_uuid"
    # try loading the potential using the stored hash instead of the uuid
    potcar_file_get = potcar_data.load_potential_file_node()
    assert potcar_file_get.uuid == potcar_file_set.uuid
    assert potcar_file_get.hash == potcar_file_set.hash
    assert potcar_file_get.element == potcar_file_set.element
    assert potcar_file_get.functional == potcar_file_set.functional
    assert potcar_file_get.name == potcar_file_set.name


def test_load_potential_file_raises_on_undiscoverable(interactive_potcar_file):
    # generate arbitrary potential and process it using the potcar parser
    interactive_potcar_file.open("POTCAR")
    path = pathlib.Path(interactive_potcar_file.filepath).absolute()
    args = ['Si', 'Si', 10000101, 'pbe', 'hash']
    potcar_file_set = VaspPotcarFile(path, *args).store()
    # create VaspPotcarData instance associated with the stored potential but
    # change uuid and hash to make the potentials undiscoverable
    potcar_data = VaspPotcarData(name='Si', version=10000101, functional='pbe')
    potcar_data.update_dict({'filenode_uuid': "changed_uuid"})
    potcar_data.update_dict({'hash': "changed_hash"})
    # try loading the potential using the stored hash instead of the uuid
    with pytest.raises(VaspPotcarDataError) as exception:
        potcar_file_get = potcar_data.load_potential_file_node()
    assert "Unable to discover associated potential" in str(exception.value)


@pytest.mark.parametrize('change_prop', ['name', 'version', 'functional',
                         'element', 'hash'])
def test_load_potential_file_node_properties_match(clear_database_before_test,
                                                   interactive_potcar_file,
                                                   change_prop):
    interactive_potcar_file.open("POTCAR")
    path = pathlib.Path(interactive_potcar_file.filepath).absolute()
    args = ['Si', 'Si', 10000101, 'pbe', 'hash']
    file_node = VaspPotcarFile(path, *args).store()
    # create VaspPotcarData instance associated with the stored potential and
    # change one of the properties
    potcar_data = VaspPotcarData(name='Si', version=10000101, functional='pbe')
    potcar_data.update_dict({change_prop: None})
    # try loading the potential file which should raise an attribute error
    # due to the mismatch in the stored potential properties
    with pytest.raises(AssertionError) as exception:
        potcar_file_get = potcar_data.load_potential_file_node()


@pytest.mark.parametrize('name', [None, 'H', 'H_pv'])
@pytest.mark.parametrize('version', [None, 10000101, 10000102])
@pytest.mark.parametrize('functional', ['pbe', 'pw91'])
@pytest.mark.parametrize('structure_type', ['pymatgen', 'aiida', 'poscar',
                         'aiida_cusp_poscar'])
def test_from_structure_classmethod(clear_database_before_test,
                                    interactive_potcar_file,
                                    minimal_pymatgen_structure, name, version,
                                    functional, structure_type):
    # create non-ordered structures of different types
    supercell = minimal_pymatgen_structure * (2, 2, 2)
    if structure_type == 'pymatgen':
        structure = supercell
    elif structure_type == 'aiida':
        structure = StructureData(pymatgen_structure=supercell)
    elif structure_type == 'poscar':
        structure = Poscar(supercell)
    elif structure_type == 'aiida_cusp_poscar':
        structure = VaspPoscarData(structure=supercell)
    # populate database with potentials
    potcar_args = [
        ['H', 'H', 10000101, 'pbe', 'hash1'],
        ['H', 'H', 10000102, 'pbe', 'hash2'],
        ['H_pv', 'H', 10000101, 'pbe', 'hash3'],
        ['H_pv', 'H', 10000102, 'pbe', 'hash4'],
        ['H', 'H', 10000101, 'pw91', 'hash5'],
        ['H', 'H', 10000102, 'pw91', 'hash6'],
        ['H_pv', 'H', 10000101, 'pw91', 'hash7'],
        ['H_pv', 'H', 10000102, 'pw91', 'hash8'],
    ]
    interactive_potcar_file.open("POTCAR")
    path = pathlib.Path(interactive_potcar_file.filepath).absolute()
    for args in potcar_args:
        VaspPotcarFile(path, *args).store()
    # setup alternative (non-default) potcar parameters
    potcar_params = {'H': {}}
    if name is not None:
        potcar_params['H'].update({'name': name})
    if version is not None:
        potcar_params['H'].update({'version': version})
    if not potcar_params['H']:
        potcar_params = {}
    # create the element-potential map
    potential_map = VaspPotcarData.from_structure(structure, functional,
                                                  potcar_params=potcar_params)
    # check that the map contains only a single entry
    assert len(potential_map.keys()) == 1
    assert list(potential_map.keys()) == ['H']
    # assert potential properties match the wanted ones
    expected_name = name or 'H'
    expected_version = version or 10000102
    assert potential_map['H'].name == expected_name
    assert potential_map['H'].version == expected_version
    assert potential_map['H'].functional == functional
