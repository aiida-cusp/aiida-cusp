# -*- coding: utf-8 -*-
"""
Test suite for the VaspPotcarFile and VaspPotcarData datatypes
"""

import pytest

import pathlib

from aiida_cusp.data.inputs.vasp_potcar import VaspPotcarFile
from aiida_cusp.data.inputs.vasp_potcar import VaspPotcarFileError
from aiida_cusp.data.inputs.vasp_potcar import MultiplePotcarError
from aiida_cusp.utils.defaults import VaspDefaults
from aiida_cusp.utils import PotcarParser


def test_store_and_load(interactive_potcar_file, clear_database):
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
    ('Xy_abc', 'Ge', 10000101, 'abcdef', 'hash'),  # invalid functional
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
