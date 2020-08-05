# -*- coding: utf-8 -*-


import pytest


@pytest.mark.parametrize('valid_input', ['incar', 'kpoints', 'neb_path',
                         'potcar', 'restart'])
def test_neb_input_port_availability(valid_input):
    from aiida.plugins import CalculationFactory
    inputs = CalculationFactory('cusp.vasp').get_builder()._valid_fields
    assert valid_input in inputs


# No check for missing neb_path as structure check is already performed
# in the VaspCalculation class
@pytest.mark.parametrize('use_incar', [True, False])
@pytest.mark.parametrize('use_kpoints', [True, False])
@pytest.mark.parametrize('use_potcar', [True, False])
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_missing_neb_input_raises(incar, kpoints, poscar, with_pbe_potcars,
                                  vasp_code, aiida_sandbox, use_incar,
                                  use_potcar, use_kpoints):
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
    # set the input plugin for code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculation inputs
    neb_path = {'node_00': poscar, 'node_01': poscar, 'node_02': poscar}
    inputs = {
        'code': vasp_code,
        'neb_path': neb_path,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    if use_incar:
        inputs.update({'incar': incar})
    if use_kpoints:
        inputs.update({'kpoints': kpoints})
    if use_potcar:
        inputs.update({'potcar': VaspPotcarData.from_structure(poscar, 'pbe')})
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_neb_calc = VaspCalculation(inputs=inputs)
    # this should pass
    if all([use_incar, use_kpoints, use_potcar]):
        vasp_neb_calc.prepare_for_submission(aiida_sandbox)
    else:  # while this should raise
        with pytest.raises(Exception) as exception:
            vasp_neb_calc.prepare_for_submission(aiida_sandbox)
        assert "non-optional NEB inputs are missing" in str(exception.value)


# build a set of different key patterns to test the expected key regex
@pytest.mark.parametrize('prefix', ['{:0>1d}', '{:0>3d}', '{:0>4d}', 'node',
                         ''])
@pytest.mark.parametrize('main_key', ['node', 'image'])
@pytest.mark.parametrize('suffix', ['{:0>1d}', '{:0>3d}', '{:0>4d}'])
def test_wrong_neb_path_identifer_raises(vasp_code, cstdn_code, incar, kpoints,
                                         poscar, with_pbe_potcars,
                                         aiida_sandbox, prefix, main_key,
                                         suffix):
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
    neb_path = {}
    for i in range(3):
        image_key = main_key
        if prefix:
            image_key = prefix.format(i) + '_' + image_key
        if suffix:
            s = suffix.format(i)
            image_key = image_key + suffix.format(i)
        neb_path[image_key] = poscar
    # set the input plugin for code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculation inputs
    inputs = {
        'code': vasp_code,
        'incar': incar,
        'kpoints': kpoints,
        'potcar': VaspPotcarData.from_structure(poscar, 'pbe'),
        'neb_path': neb_path,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_neb_calc = VaspCalculation(inputs=inputs)
    with pytest.raises(Exception) as exception:
        vasp_neb_calc.prepare_for_submission(aiida_sandbox)
    err_msg = "Ill NEB path node identifier key format for key"
    assert err_msg in str(exception.value)


# ignore BadPotcarWarning raised by pymatgen. i don't care if pymatgen does
# not like my test "potential"
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_vasp_neb_calculation_setup(vasp_code, cstdn_code, incar, kpoints,
                                    poscar, with_pbe_potcars, aiida_sandbox):
    import pathlib
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
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
        'neb_path': {'node_00': poscar, 'node_01': poscar, 'node_02': poscar},
        'potcar': potcar_linklist,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_neb_calc = VaspCalculation(inputs=inputs)
    vasp_neb_calc.prepare_for_submission(aiida_sandbox)
    sandbox = pathlib.Path(aiida_sandbox.abspath)
    # check NEB folder structure
    assert (sandbox / '00').exists() is True
    assert (sandbox / '01').exists() is True
    assert (sandbox / '02').exists() is True
    # check top folder files are written and content is correct
    potcar = VaspPotcarData.potcar_from_linklist(poscar, potcar_linklist)
    topfolder_inputs = [
        ('INCAR', incar.get_incar()),
        ('KPOINTS', kpoints.get_kpoints()),
        ('POTCAR', potcar),
    ]
    for topfolder_file, expected_content in topfolder_inputs:
        fpath = sandbox / topfolder_file
        assert fpath.is_file() is True
        with open(fpath, 'r') as infile:
            content = infile.read()
        assert content == str(expected_content)
    # test neb path nodes
    for nodename in ['00', '01', '02']:
        fpath = sandbox / nodename / 'POSCAR'
        assert fpath.is_file() is True
        with open(fpath, 'r') as infile:
            content = infile.read()
        assert content == str(poscar.get_poscar())


@pytest.mark.parametrize('invalid_input', ['neb_path', 'potcar'])
def test_invalid_restart_neb_inputs_raise(vasp_code, poscar, with_pbe_potcars,
                                          invalid_input):
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
    inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    if invalid_input == 'neb_path':
        neb_path = {'node_00': poscar, 'node_01': poscar, 'node_02': poscar}
        inputs.update({'neb_path': neb_path})
    if invalid_input == 'potcar':
        potcar = VaspPotcarData.from_structure(poscar, 'pbe')
        inputs.update({'potcar': potcar})
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_neb_calculation = VaspCalculation(inputs=inputs)
    with pytest.raises(Exception) as exception:
        # need to call the name mangeled protected method explicitly
        vasp_neb_calculation._VaspNebCalculation__verify_restart_inputs()
    err_msg = ("the following defined inputs are not allowed in a restarted "
               "NEB calculation")
    assert err_msg in str(exception.value)


@pytest.mark.parametrize('switch', [True, False])
def test_neb_poscar_overwrite_switch(switch, tmpdir, vasp_code, aiida_sandbox,
                                     monkeypatch):
    import pathlib
    from aiida.orm import RemoteData
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
    # set the input plugin for code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup a remote restart directory with POSCAR and CONTCAR
    computer = vasp_code.computer
    subfolders = ['00', '01', '02']
    for subfolder in subfolders:
        pathlib.Path(tmpdir / subfolder).mkdir()
        pathlib.Path(tmpdir / subfolder / 'POSCAR').touch()
        pathlib.Path(tmpdir / subfolder / 'CONTCAR').touch()
    remote_path = str(tmpdir)
    remote_data = RemoteData(computer=computer, remote_path=remote_path)
    inputs = {
        'code': vasp_code,
        'restart': {'folder': remote_data, 'contcar_to_poscar': switch},
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    # mock the is_neb() method to avoid the search of the remote_folders
    # parent CalcJobNode (we know it **is** a NEB calculation!)
    monkeypatch.setattr(VaspCalculation, 'is_neb', lambda self: True)
    vasp_neb_calculation = VaspCalculation(inputs=inputs)
    calcinfo = vasp_neb_calculation.prepare_for_submission(aiida_sandbox)
    remote_copy_list = calcinfo.remote_copy_list
    for subfolder in subfolders:
        # find the remote_copy_list for a specific NEB subfolder
        reduced_remote_list = []
        for (uuid, abspath_remote, relpath_input) in remote_copy_list:
            if pathlib.Path(abspath_remote).parent.name == subfolder:
                reduced_remote_list.append((abspath_remote, relpath_input))
        copied_files = [pathlib.Path(f).name for (f, _) in reduced_remote_list]
        # the contcar file will always be copied no matter if the switch is
        # set or not
        assert 'CONTCAR' in copied_files
        # now check for a single NEB subfolder if CONTCAR is copied on itself
        # or on the new POSCAR
        for (abspath_remote, relpath_input) in reduced_remote_list:
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
def test_neb_defined_inputs_are_preferred(use_incar, use_kpoints, tmpdir,
                                          vasp_code, aiida_sandbox, incar,
                                          kpoints, monkeypatch):
    import pathlib
    from aiida.orm import RemoteData
    from aiida.plugins import CalculationFactory
    from aiida_cusp.data import VaspPotcarData
    # set the input plugin for code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp_neb')
    # setup a remote restart directory with POSCAR and CONTCAR
    computer = vasp_code.computer
    pathlib.Path(tmpdir / 'INCAR').touch()
    pathlib.Path(tmpdir / 'KPOINTS').touch()
    remote_path = str(tmpdir)
    remote_data = RemoteData(computer=computer, remote_path=remote_path)
    inputs = {
        'code': vasp_code,
        'restart': {'folder': remote_data},
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    if use_incar:
        inputs.update({'incar': incar})
    if use_kpoints:
        inputs.update({'kpoints': kpoints})
    VaspCalculation = CalculationFactory('cusp.vasp')
    # mock the is_neb() method to avoid the search of the remote_folders
    # parent CalcJobNode (we know it **is** a NEB calculation!)
    monkeypatch.setattr(VaspCalculation, 'is_neb', lambda self: True)
    vasp_neb_calculation = VaspCalculation(inputs=inputs)
    calcinfo = vasp_neb_calculation.prepare_for_submission(aiida_sandbox)
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
