# -*- coding: utf-8 -*-


import pytest


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


@pytest.mark.parametrize('invalid_input', ['poscar', 'potcar'])
def test_invalid_restart_inputs_raise(vasp_code, poscar, with_pbe_potcars,
                                      invalid_input):
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
    VaspBasicCalculation = CalculationFactory('cusp.vasp')
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
            },
        },
    }
    if invalid_input == 'poscar':
        inputs.update({'poscar': poscar})
    if invalid_input == 'potcar':
        potcar = VaspPotcarData.from_structure(poscar, 'pbe')
        inputs.update({'potcar': potcar})
    vasp_basic_calculation = VaspBasicCalculation(inputs=inputs)
    with pytest.raises(Exception) as exception:
        vasp_basic_calculation.verify_restart_inputs()
    err_msg = "the following defined inputs are not allowed in a restarted"
    assert err_msg in str(exception.value)


@pytest.mark.parametrize('switch', [True, False])
def test_poscar_overwrite_switch(switch, tmpdir, vasp_code, aiida_sandbox):
    import pathlib
    from aiida.orm import RemoteData
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
    # set the input plugin for code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup a remote restart directory with POSCAR and CONTCAR
    computer = vasp_code.computer
    pathlib.Path(tmpdir / 'POSCAR').touch()
    pathlib.Path(tmpdir / 'CONTCAR').touch()
    remote_path = str(tmpdir)

    remote_data = RemoteData(computer=computer, remote_path=remote_path)
    VaspBasicCalculation = CalculationFactory('cusp.vasp')
    inputs = {
        'code': vasp_code,
        'restart': {
            'folder': remote_data,
            'contcar_to_poscar': switch,
        },
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
            },
        },
    }
    vasp_basic_calculation = VaspBasicCalculation(inputs=inputs)
    calcinfo = vasp_basic_calculation.prepare_for_submission(aiida_sandbox)
    remote_copy_list = calcinfo.remote_copy_list
    copied_files = [pathlib.Path(f).name for (_, f, _) in remote_copy_list]
    # the contcar file will always be copied no matter if the switch is set
    # or not
    assert 'CONTCAR' in copied_files
    # now check if CONTCAR is copied on itself or on the new POSCAR
    for (uuid, abspath_remote, relpath_input) in remote_copy_list:
        filename_remote = pathlib.Path(abspath_remote).name
        filename_input = pathlib.Path(relpath_input).name
        if filename_remote == 'CONTCAR':
            if switch:  # True: CONTCAR --> POSCAR
                assert filename_input == 'POSCAR'
                assert 'POSCAR' not in copied_files
            else:  # False: CONTCAR --> CONTCAR
                assert filename_input == 'CONTCAR'
                assert 'POSCAR' in copied_files


@pytest.mark.parametrize('use_incar', [False, True])
@pytest.mark.parametrize('use_kpoints', [False, True])
def test_defined_inputs_are_preferred(use_incar, use_kpoints, tmpdir,
                                      vasp_code, aiida_sandbox, incar,
                                      kpoints):
    import pathlib
    from aiida.orm import RemoteData
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
    # set the input plugin for code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup a remote restart directory with POSCAR and CONTCAR
    computer = vasp_code.computer
    pathlib.Path(tmpdir / 'INCAR').touch()
    pathlib.Path(tmpdir / 'KPOINTS').touch()
    remote_path = str(tmpdir)
    remote_data = RemoteData(computer=computer, remote_path=remote_path)
    VaspBasicCalculation = CalculationFactory('cusp.vasp')
    inputs = {
        'code': vasp_code,
        'restart': {
            'folder': remote_data,
        },
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
    vasp_basic_calculation = VaspBasicCalculation(inputs=inputs)
    calcinfo = vasp_basic_calculation.prepare_for_submission(aiida_sandbox)
    remote_copy_list = calcinfo.remote_copy_list
    files_to_copy = [pathlib.Path(f).name for (_, f, _) in remote_copy_list]
    if use_incar:  # incar input defined: do not copy
        assert 'INCAR' not in files_to_copy
    else:
        assert 'INCAR' in files_to_copy
    if use_kpoints:  # kpoint input defined: do not copy
        assert 'KPOINTS' not in files_to_copy
    else:
        assert 'KPOINTS' in files_to_copy
