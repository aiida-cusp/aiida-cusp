# -*- coding: utf-8 -*-


import pytest

import json


def test_store_and_load(testdata):
    from aiida.orm import load_node
    from aiida_cusp.data.outputs.vasp_outcar import VaspOutcarData
    outcar = testdata / 'OUTCAR'
    outcar_node = VaspOutcarData(file=outcar)
    uuid = outcar_node.store().uuid
    # load contents from stored node and compare to original
    loaded_content = load_node(uuid).get_content()
    with open(outcar, 'rb') as outcar_file:
        original_content = outcar_file.read()
    assert loaded_content == original_content


def test_get_outcar_method(testdata):
    from pymatgen.io.vasp.outputs import Outcar
    from aiida_cusp.data.outputs.vasp_outcar import VaspOutcarData
    outcar = testdata / 'OUTCAR'
    outcar_node = VaspOutcarData(file=outcar)
    # create Outcar object from node and compare to the original
    # pymatgen class generated from the test file
    outcar_obj_node = outcar_node.get_outcar()
    outcar_obj_pmg = Outcar(outcar)
    node_contents = json.dumps(outcar_obj_node.as_dict(), sort_keys=True)
    pmg_contents = json.dumps(outcar_obj_pmg.as_dict(), sort_keys=True)
    assert node_contents == pmg_contents
