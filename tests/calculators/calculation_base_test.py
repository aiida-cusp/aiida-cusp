# -*- coding: utf-8 -*-


"""
Test module for the CalculationBase calculator base class. This module
only tests the basic support methods and does not check the methods used
for the calculation setup. Other methods like for instance the
prepare_for_submission() methods should be tested in the subclassed
calculator tests
"""


import pytest


@pytest.mark.parametrize('procs,procs_per_machine,extraparams,expected',
[   # noqa: E128
    (1, 1, [], ['mpirun', '-np', '1']),
    (2, 1, [], ['mpirun', '-np', '2']),
    (2, 2, [], ['mpirun', '-np', '4']),
    (1, 1, ['-extra'], ['mpirun', '-np', '1', '-extra']),
])
def test_vasp_run_line(vasp_code, procs, procs_per_machine, extraparams,
                       expected, clear_database_after_test):
    from aiida_cusp.calculators import CalculationBase
    vasp_code.computer.set_default_mpiprocs_per_machine(procs_per_machine)
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': procs},
                'mpirun_extra_params': extraparams,
            },
        },
    }
    Base = CalculationBase(inputs=inputs)
    expected_runline = expected + [vasp_code.get_execname()]
    assert Base.vasp_run_line() == expected_runline


def test_vasp_run_line_no_mpi(vasp_code, clear_database_after_test):
    from aiida_cusp.calculators import CalculationBase
    vasp_code.computer.set_default_mpiprocs_per_machine(100)
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 100},
                'mpirun_extra_params': ['some', 'mpi', 'extra', 'params'],
                'withmpi': False,  # disable MPI
            },
        },
    }
    Base = CalculationBase(inputs=inputs)
    assert Base.vasp_run_line() == [vasp_code.get_execname()]


@pytest.mark.parametrize('filename', ['MyFile', '.Hidden'])
@pytest.mark.parametrize('relpath', ['.', '00', '01', '02', 'sub1',
                         'sub1/sub2', 'sub1/sub2/sub3', '.hidden1'])
def test_remote_folder_filelist(vasp_code, filename, relpath, aiida_sandbox,
                                clear_database_after_test):
    import pathlib
    from aiida.orm import RemoteData
    from aiida.orm import load_computer
    from aiida_cusp.calculators import CalculationBase
    sandbox = pathlib.Path(aiida_sandbox.abspath).absolute()
    remote = RemoteData(computer=vasp_code.computer, remote_path=str(sandbox))
    sandbox = pathlib.Path(aiida_sandbox.abspath).absolute()
    # create file with name at given subdir
    filepath = (sandbox / relpath).absolute()
    if not relpath == '.':
        filepath.mkdir(parents=True)
    filepath = filepath / filename
    filepath.touch()
    assert filepath.exists() is True
    # initialize remote directory from sandbox folder
    remote = RemoteData(computer=vasp_code.computer, remote_path=str(sandbox))
    # setup the calculator
    inputs = {
        'code': vasp_code,
        'restart': {'folder': remote},
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
            },
        },
    }
    Base = CalculationBase(inputs=inputs)
    remote_filelist = Base.remote_filelist(remote)
    expected_filelist = [(
        filename,  # the file name
        str(filepath),  # the absolute path including the file's name
        str(relpath),  # the relative path without the file
    )]
    assert remote_filelist == expected_filelist


@pytest.mark.parametrize('submit_script_name', [None, 'foo.bar'])
def test_default_restart_exclude_files(submit_script_name, vasp_code,
                                       clear_database_after_test):
    from aiida_cusp.calculators import CalculationBase
    from aiida_cusp.utils.defaults import PluginDefaults
    # setup the calculator
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
            },
        },
    }
    if submit_script_name is not None:
        inputs['metadata']['options'].update({'submit_script_filename':
                                              submit_script_name})
    Base = CalculationBase(inputs=inputs)
    # submit_script_name == None -> check for AiiDA's default value
    script_name = submit_script_name or '_aiidasubmit.sh'
    expected_list = ['job_tmpl.json', 'calcinfo.json', script_name,
                     PluginDefaults.CSTDN_SPEC_FNAME]
    excluded_list = Base.restart_exclude_files()
    # capture if something went wrong and we have duplicate files in here
    assert len(set(excluded_list)) == len(excluded_list)
    # assert that both list contain the same elements (ignoring their index)
    assert set(excluded_list) == set(expected_list)


@pytest.mark.parametrize('method', ['create_inputs_for_restart_run',
                         'create_inputs_for_regular_run'])
def test_undefined_create_input_methods_raise(vasp_code, method, aiida_sandbox,
                                              clear_database_after_test):
    from aiida.common import CalcInfo
    from aiida_cusp.calculators import CalculationBase
    # setup the calculator
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
            },
        },
    }
    Base = CalculationBase(inputs=inputs)
    calcinfo = CalcInfo()
    with pytest.raises(NotImplementedError) as exception:
        assert getattr(Base, method)(aiida_sandbox, calcinfo)
