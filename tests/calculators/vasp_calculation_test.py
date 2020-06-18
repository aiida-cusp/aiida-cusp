# -*- coding: utf-8 -*-


import pytest


@pytest.mark.parametrize('use_poscar,use_neb_path,expected_error',
[   # noqa: E128
    (False, False, "Missing non-optional structure input"),
    (True, True, "'poscar' and 'neb_path' cannot be set at the same time"),
    (False, True, ""),
    (True, False, ""),
])
def test_verify_structure_input(vasp_code, poscar, use_poscar, use_neb_path,
                                expected_error):
    from aiida.plugins import CalculationFactory
    from aiida.orm import RemoteData
    # define code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculator
    inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    if use_poscar:
        inputs.update({'poscar': poscar})
    if use_neb_path:
        neb_path = {'node_00': poscar, 'node_01': poscar, 'node_02': poscar}
        inputs.update({'neb_path': neb_path})
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc = VaspCalculation(inputs=inputs)
    if expected_error:
        with pytest.raises(Exception) as exception:
            _ = vasp_calc.verify_structure_inputs()
        assert str(exception.value) == expected_error
    else:
        _ = vasp_calc.verify_structure_inputs()


@pytest.mark.parametrize('is_restart', [True, False])
@pytest.mark.parametrize('is_neb', [True, False])
def test_is_neb(vasp_code, poscar, is_restart, is_neb):
    from aiida.orm import RemoteData
    from aiida.common.links import LinkType
    from aiida.plugins import CalculationFactory
    from aiida.engine import run_get_node
    from aiida_cusp.data import VaspPotcarData
    # define code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculator
    inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    if is_neb:
        neb_path = {'node_00': poscar, 'node_01': poscar, 'node_02': poscar}
        inputs.update({'neb_path': neb_path})
    else:
        inputs.update({'poscar': poscar})
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc_base = VaspCalculation(inputs=inputs)
    # if restart create a second calculator using a remote_folder connected
    # to the first calculation as input
    if is_restart:
        inputs.pop('poscar', None)
        inputs.pop('neb_path', None)
        remote_data = RemoteData(computer=vasp_code.computer, remote_path='')
        remote_data.add_incoming(vasp_calc_base.node.store(),
                                 link_type=LinkType.CREATE,
                                 link_label='remote_folder')
        inputs.update({'restart': {'folder': remote_data}})
        vasp_calc_base = VaspCalculation(inputs=inputs)
    # assert is_neb() returns the desired result
    result = vasp_calc_base.is_neb()
    assert result is is_neb
