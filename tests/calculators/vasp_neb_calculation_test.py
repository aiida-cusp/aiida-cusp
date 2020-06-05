# -*- coding: utf-8 -*-
import pytest


@pytest.mark.parametrize('valid_input', ['incar', 'kpoints', 'neb_path',
                         'potcar', 'restart'])
def test_input_port_availability(valid_input):
    from aiida.plugins import CalculationFactory
    inputs = CalculationFactory('cusp.vasp_neb').get_builder()._valid_fields
    assert valid_input in inputs
