# -*- coding: utf-8 -*-
"""
Test suite for the VaspIncarData and the related IncarWrapper utility
"""


import pytest
import pathlib

from pymatgen.io.vasp.inputs import Incar

from aiida_cusp.data.inputs.vasp_incar import IncarWrapper, VaspIncarData
from aiida_cusp.utils.exceptions import IncarWrapperError


#
# Tests for IncarWrappper
#
def test_empty_input():
    incar_parameters = None
    incar = IncarWrapper(incar=incar_parameters)
    assert str(incar).strip() == ""


def test_init_from_incar_object():
    incar_parameters = {'ISMEAR': 0, 'SIGMA': 5.0E-2}
    pmg_incar = Incar(params=incar_parameters)
    incar = IncarWrapper(incar=pmg_incar)
    assert str(pmg_incar) == str(incar)


def test_init_from_user_dict():
    incar_parameters = {'ISMEAR': 0, 'SIGMA': 5.0E-2}
    incar = IncarWrapper(incar=incar_parameters)
    pmg_incar = Incar(params=incar_parameters)
    assert str(incar) == str(pmg_incar)


@pytest.mark.parametrize('incar_param_type', [list(), tuple(), float, int])
def test_unknown_input_type_raises(incar_param_type):
    with pytest.raises(IncarWrapperError) as exception:
        incar = IncarWrapper(incar=incar_param_type)
    assert "Unknown type" in str(exception.value)


def test_keys_to_upper_case():
    mixed_case_dict = {'iSMeaR': 0, 'sigma': 0.05, 'ENCUT': 100}
    upper_case = IncarWrapper.keys_to_upper_case(mixed_case_dict)
    assert 'ISMEAR' in upper_case.keys()
    assert 'SIGMA' in upper_case.keys()
    assert 'ENCUT' in upper_case.keys()


#
# Test for VaspIncarData
#
def test_get_incar_method():
    incar_parameters = {
        'EDIFF': 1.0E-6,
        'EDIFFG': -0.001,
        'ISMEAR': 0,
        'SIGMA': 0.01,
    }
    incar = VaspIncarData(incar=incar_parameters)
    pmg_incar = Incar(params=incar_parameters)
    assert str(incar.get_incar()) == str(pmg_incar)


def test_store_and_load_incar_data():
    from aiida.orm import load_node
    incar_parameters = {
        'EDIFF': 1.0E-6,
        'EDIFFG': -0.001,
        'ISMEAR': 0,
        'SIGMA': 0.01,
    }
    incar_set = VaspIncarData(incar=incar_parameters)
    uuid = incar_set.store().uuid
    incar_get = load_node(uuid)
    assert str(incar_set.get_incar()) == str(incar_get.get_incar())


def test_write_file_method(tmpdir):
    incar_parameters = {
        'EDIFF': 1.0E-6,
        'EDIFFG': -0.001,
        'ISMEAR': 0,
        'SIGMA': 0.01,
    }
    incar = VaspIncarData(incar=incar_parameters)
    filepath = pathlib.Path(tmpdir) / 'INCAR'
    assert filepath.is_file() is False  # assert file is not already there
    incar.write_file(str(filepath))
    assert filepath.is_file() is True  # assert file has been written
    # load contents from file and compare to node contents
    with open(filepath, 'r') as stored_incar_file:
        written_contents = stored_incar_file.read()
    assert written_contents == str(incar.get_incar())
