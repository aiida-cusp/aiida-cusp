# -*- coding: utf-8 -*-


import pytest

import json


def test_store_and_load_node(testdata):
    from aiida.orm import load_node
    from aiida_cusp.data.outputs.vasp_vasprun import VaspVasprunData
    vasprun_xml = testdata / 'vasprun.xml'
    vasprun_node = VaspVasprunData(file=vasprun_xml)
    uuid = vasprun_node.store().uuid
    # load contents from stored node and compare to original
    loaded_content = load_node(uuid).get_content()
    with open(vasprun_xml, 'rb') as vasprun:
        original_content = vasprun.read()
    assert loaded_content == original_content


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_get_vasprun_method(testdata):
    from pymatgen.io.vasp.outputs import Vasprun
    from aiida_cusp.data.outputs.vasp_vasprun import VaspVasprunData
    from aiida_cusp.utils.defaults import VasprunParsingDefaults
    default_parsing_args = VasprunParsingDefaults.PARSER_ARGS
    vasprun_xml = testdata / 'vasprun.xml'
    vasprun_node = VaspVasprunData(file=vasprun_xml)
    # create vasprun object from node and compare to the original
    # pymatgen class generated from the test file
    vasprun_obj_node = vasprun_node.get_vasprun()
    vasprun_obj_pmg = Vasprun(vasprun_xml, **default_parsing_args)
    node_contents = json.dumps(vasprun_obj_node.as_dict(), sort_keys=True)
    pmg_contents = json.dumps(vasprun_obj_pmg.as_dict(), sort_keys=True)
    assert node_contents == pmg_contents


def test_parser_settings_update(testdata):
    from aiida_cusp.data.outputs.vasp_vasprun import VaspVasprunData
    from aiida_cusp.utils.defaults import VasprunParsingDefaults
    vasprun_xml = testdata / 'vasprun.xml'
    vasprun_node = VaspVasprunData(file=vasprun_xml)
    # try to set all arguments to a defined value, i.e -1, and get the
    # updated parser args
    kwargs = {key: -1 for key in VasprunParsingDefaults.PARSER_ARGS}
    updated_kwargs = vasprun_node.parser_settings(**kwargs)
    # first check that parse_potcar_file remains as set to False (we never
    # want to parse the POTCAR!)
    assert updated_kwargs.pop('parse_potcar_file') is False
    # then check the remaining values
    for key, value in updated_kwargs.items():
        assert value == -1


def test_unknown_argument_raises(testdata):
    from aiida_cusp.data.outputs.vasp_vasprun import VaspVasprunData
    vasprun_xml = testdata / 'vasprun.xml'
    vasprun_node = VaspVasprunData(file=vasprun_xml)
    unknown_kwarg = {'unknown': None}
    with pytest.raises(TypeError) as exception:
        _ = vasprun_node.parser_settings(**unknown_kwarg)
    expected_error = ("get_vasprun() got an unexpected keyword argument(s) "
                      "'unknown'")
    assert str(exception.value) == expected_error
