# -*- coding: utf-8 -*-


"""
Test module for the ParserBase class representing the basic parser class.
"""


import pytest


def test_missing_temp_folder_fails(vasp_code):
    from aiida.plugins import CalculationFactory
    from aiida_cusp.parsers.parser_base import ParserBase
    # define code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculator
    inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc_node = VaspCalculation(inputs=inputs).node
    exitcode = ParserBase(vasp_calc_node).parse()
    assert exitcode.status == 300


@pytest.mark.parametrize('parser_settings', [{'has': 'settings'}, {}])
def test_parser_settings_being_set(vasp_code, parser_settings):
    from aiida.plugins import CalculationFactory
    from aiida_cusp.parsers.parser_base import ParserBase
    # define code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculator
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
                'parser_settings': parser_settings,
            }
        },
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc_node = VaspCalculation(inputs=inputs).node
    # init custom options and instantiate the parser class
    parser = ParserBase(vasp_calc_node)
    assert parser.settings == parser_settings


def test_register_output_nodes_method(vasp_code):
    from aiida.plugins import CalculationFactory
    from aiida.orm import Node
    from aiida_cusp.parsers.parser_base import ParserBase
    from aiida_cusp.utils.defaults import PluginDefaults
    # define code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculator and instantiate parser class
    inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc_node = VaspCalculation(inputs=inputs).node
    parser = ParserBase(vasp_calc_node)
    # test add output node
    linkname = 'output_node'
    # all parsed outputs are expected to be registered through the dynamic
    # parsed_results namespace
    expected = "{}.{}".format(PluginDefaults.PARSER_OUTPUT_NAMESPACE,
                              linkname)
    node = Node()
    exit_code = parser.register_output_nodes([(linkname, node)])
    assert exit_code is None
    assert expected in parser.outputs
    assert isinstance(parser.outputs.get(expected), Node) is True
    # test storing the node with same linkname fails
    exit_code = parser.register_output_nodes([(linkname, node)])
    assert exit_code.status == 303


def test_expected_files_method_default_value():
    """
    Assert that the expected_files() method returns `None` by default
    """
    from aiida_cusp.parsers.parser_base import ParserBase
    assert ParserBase.expected_files() is None
