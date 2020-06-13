# -*- coding: utf-8 -*-


import pytest


# TODO: Test restart with poscar overwrite ON / OFF (simply check the copy list
#       in the calcinfo because actualy copying is already tested)
# TODO: Test invalid inputs raise on restart (No copy needed)
# TODO: Test defined inputs are preferred (once again simply check the copy
#       list and possibly the list of excluded files as well)


@pytest.mark.parametrize('valid_input', ['incar', 'kpoints', 'poscar',
                         'potcar', 'restart'])
def test_input_port_availability(valid_input):
    from aiida.plugins import CalculationFactory
    inputs = CalculationFactory('cusp.vasp').get_builder()._valid_fields
    assert valid_input in inputs


@pytest.mark.parametrize('use_incar', [True, False])
@pytest.mark.parametrize('use_kpoints', [True, False])
@pytest.mark.parametrize('use_poscar', [True, False])
@pytest.mark.parametrize('use_potcar', [True, False])
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_missing_input_raises(incar, kpoints, poscar, with_pbe_potcars,
                              vasp_code, aiida_sandbox, use_incar,
                              use_poscar, use_potcar, use_kpoints):
    import pathlib
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
    # set the input plugin for code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculation inputs
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
            },
        },
    }
    if use_incar:
        inputs.update({'incar': incar})
    if use_kpoints:
        inputs.update({'kpoints': kpoints})
    if use_poscar:
        inputs.update({'poscar': poscar})
    if use_potcar:
        inputs.update({'potcar': VaspPotcarData.from_structure(poscar, 'pbe')})
    VaspBasicCalculation = CalculationFactory('cusp.vasp')
    vasp_calc = VaspBasicCalculation(inputs=inputs)
    if all([use_incar, use_kpoints, use_poscar, use_potcar]):
        vasp_calc.prepare_for_submission(aiida_sandbox)
    else:
        with pytest.raises(Exception) as exception:
            vasp_calc.prepare_for_submission(aiida_sandbox)
        assert "non-optional inputs are missing" in str(exception.value)


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_vasp_calculation_setup(vasp_code, cstdn_code, incar, kpoints, poscar,
                                with_pbe_potcars, aiida_sandbox):
    import pathlib
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
    from aiida_cusp.utils.defaults import PluginDefaults
    # set the input plugin for code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    cstdn_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculation inputs
    potcar_linklist = VaspPotcarData.from_structure(poscar, 'pbe')
    inputs = {
        'code': vasp_code,
        'custodian': {'code': cstdn_code},
        'incar': incar,
        'kpoints': kpoints,
        'poscar': poscar,
        'potcar': potcar_linklist,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
            },
        },
    }
    VaspBasicCalculation = CalculationFactory('cusp.vasp')
    vasp_calc = VaspBasicCalculation(inputs=inputs)
    vasp_calc.prepare_for_submission(aiida_sandbox)
    potcar = VaspPotcarData.potcar_from_linklist(poscar, potcar_linklist)
    filenames = [
        ('INCAR', incar.get_incar()),
        ('KPOINTS', kpoints.get_kpoints()),
        ('POSCAR', poscar.get_poscar()),
        ('POTCAR', potcar),
    ]
    for (filename, expected_content) in filenames:
        filepath = pathlib.Path(aiida_sandbox.abspath) / filename
        assert filepath.is_file() is True
        with open(filepath, 'r') as outfile:
            content = outfile.read()
        assert content == str(expected_content)
    # assert the specfile was written to the folder
    c = pathlib.Path(aiida_sandbox.abspath) / PluginDefaults.CSTDN_SPEC_FNAME
    assert c.is_file() is True
