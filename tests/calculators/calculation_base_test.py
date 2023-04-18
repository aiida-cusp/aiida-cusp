# -*- coding: utf-8 -*-


"""
Test module for the CalculationBase calculator base class. This module
only tests the basic support methods and does not check the methods used
for the calculation setup. Other methods like for instance the
prepare_for_submission() methods should be tested in the subclassed
calculator tests
"""


import pytest

from aiida_cusp.utils.defaults import PluginDefaults


@pytest.mark.parametrize('procs,procs_per_machine,extraparams,expected',
[   # noqa: E128
    (1, 1, [], ['mpirun', '-np', '1']),
    (2, 1, [], ['mpirun', '-np', '2']),
    (2, 2, [], ['mpirun', '-np', '4']),
    (1, 1, ['-extra'], ['mpirun', '-np', '1', '-extra']),
])
def test_vasp_run_line(vasp_code, procs, procs_per_machine, extraparams,
                       expected):
    from aiida_cusp.calculators.calculation_base import CalculationBase
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


def test_vasp_run_line_no_mpi(vasp_code):
    from aiida_cusp.calculators.calculation_base import CalculationBase
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
def test_remote_folder_filelist(vasp_code, filename, relpath, aiida_sandbox):
    import pathlib
    from aiida.orm import RemoteData
    from aiida.orm import load_computer
    from aiida_cusp.calculators.calculation_base import CalculationBase
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
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    Base = CalculationBase(inputs=inputs)
    remote_filelist = Base.remote_filelist(remote)
    expected_filelist = [(
        filename,  # the file name
        str(filepath),  # the absolute path including the file's name
        str(relpath),  # the relative path without the file
    )]
    assert remote_filelist == expected_filelist


# FIXME: Setting a custom submit script name should be skippe for AiiDA
#        versions below 1.2.1 where this option was first introduced
#        if aiida.__version__ < 1.2.1 and submit_script_name:
#              pytest.skip('submit_script_filename option not available for
#                          AiiDA versions below 1.2.1')
@pytest.mark.parametrize('submit_script_name', [None, 'foo.bar'])
@pytest.mark.parametrize('contcar_to_poscar', [True, False])
def test_default_restart_files_exclude(submit_script_name, contcar_to_poscar,
                                       vasp_code):
    from aiida_cusp.calculators.calculation_base import CalculationBase
    from aiida_cusp.utils.defaults import PluginDefaults, VaspDefaults
    inputs = {
        'code': vasp_code,
        'restart': {'contcar_to_poscar': contcar_to_poscar},
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
    if contcar_to_poscar:  # add POSCAR to expected list
        expected_list += [VaspDefaults.FNAMES['poscar']]
    excluded_list = Base.restart_files_exclude()
    # capture if something went wrong and we have duplicate files in here
    assert len(set(excluded_list)) == len(excluded_list)
    # assert that both list contain the same elements (ignoring their index)
    assert set(excluded_list) == set(expected_list)


def test_undefined_create_calculation_inputs_raise(vasp_code, aiida_sandbox):
    from aiida.common import CalcInfo
    from aiida_cusp.calculators.calculation_base import CalculationBase
    # setup the calculator
    inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    Base = CalculationBase(inputs=inputs)
    calcinfo = CalcInfo()
    with pytest.raises(NotImplementedError) as exception:
        assert Base.create_calculation_inputs(aiida_sandbox, calcinfo)


# check submit-script if only a vasp code is available
@pytest.mark.parametrize('withmpi', [True, False])
def test_prepare_for_submission_base_vasp(withmpi, vasp_code, cstdn_code,
                                          aiida_sandbox):
    from aiida_cusp.calculators.calculation_base import CalculationBase
    # setup the calculator
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
                'withmpi': withmpi,
            },
        },
    }
    Base = CalculationBase(inputs=inputs)
    # silence the NotImplementedErrors (we do not need these methods here)
    Base.create_calculation_inputs = lambda folder, calcinfo: calcinfo
    Base.expected_files = lambda: None
    # run prepare_for_submission() to write the submit script to the
    # sandbox folder
    calcinfo = Base.presubmit(aiida_sandbox)
    script = Base.inputs.metadata.options.get('submit_script_filename',
                                              '_aiidasubmit.sh')
    with open(aiida_sandbox.abspath + '/' + script, 'r') as script_file:
        script_file_contents = script_file.read()
    if withmpi:
        expected_runline = ("'mpirun' '-np' '1' '/path/to/vasp'  > "
                            "'aiida.out' 2> 'aiida.err'")
    else:
        expected_runline = "'/path/to/vasp'  > 'aiida.out' 2> 'aiida.err'"
    # assert vasp related runline and prepends/appends are set
    assert expected_runline in script_file_contents
    assert vasp_code.get_prepend_text() in script_file_contents
    assert vasp_code.get_append_text() in script_file_contents
    # assert no custodian related stuff is present in the script
    assert cstdn_code.get_prepend_text() not in script_file_contents
    assert cstdn_code.get_append_text() not in script_file_contents


# check submit-script if custodian code is available
@pytest.mark.parametrize('withmpi', [True, False])
def test_prepare_for_submission_base_cstdn(withmpi, vasp_code, cstdn_code,
                                           aiida_sandbox):
    from aiida_cusp.calculators.calculation_base import CalculationBase
    # setup the calculator
    inputs = {
        'code': vasp_code,
        'custodian': {'code': cstdn_code},
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
                'withmpi': withmpi,
            },
        },
    }
    Base = CalculationBase(inputs=inputs)
    # silence the NotImplementedError (we do not need these methods here)
    Base.create_calculation_inputs = lambda folder, calcinfo: calcinfo
    Base.expected_files = lambda: None
    # run prepare_for_submission() to write the submit script to the
    # sandbox folder
    calcinfo = Base.presubmit(aiida_sandbox)
    script = Base.inputs.metadata.options.get('submit_script_filename',
                                              '_aiidasubmit.sh')
    with open(aiida_sandbox.abspath + '/' + script, 'r') as script_file:
        script_file_contents = script_file.read()
    # `withmpi` only affects the contents of the cstdn_spec.yaml and thus the
    # runline should stay the same in case a custodian code is present
    expected_runline = "'/path/to/cstdn' 'run' 'cstdn_spec.yaml'"
    # assert vasp related runline and prepends/appends are set
    assert expected_runline in script_file_contents
    assert vasp_code.get_prepend_text() in script_file_contents
    assert vasp_code.get_append_text() in script_file_contents
    # assert custodian related stuff is present in the script
    assert cstdn_code.get_prepend_text() in script_file_contents
    assert cstdn_code.get_append_text() in script_file_contents


# test remote copying of files works as expected (each entry is defined
# as relative_path_in_remote/filename with from_remote defining if the
# file is expected to be replaced with the remote version or not)
@pytest.mark.parametrize('testfile,from_remote',
[   # noqa: E128
    # some files that are never copied from the remote
    ('.aiida/calcinfo.json', False),
    ('.aiida/job_tmpl.json', False),
    ('_aiidasubmit.sh', False),
    (PluginDefaults.CSTDN_SPEC_FNAME, False),
    # other files that **should** be copied from the remote
    ('SomeFile', True),
    ('sub/AnotherFile', True),
    ('deeply/nested/folder/structure/MoreFiles', True),
])
def test_calculation_restart_copy_remote(vasp_code, cstdn_code, tmpdir,
                                         testfile, from_remote, monkeypatch):
    import pathlib
    import shutil
    from aiida.orm import RemoteData
    from aiida.engine import run_get_node
    from aiida_cusp.utils.defaults import PluginDefaults
    from aiida_cusp.calculators.calculation_base import CalculationBase
    # set the input plugin for code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    cstdn_code.set_attribute('input_plugin', 'cusp.vasp')
    # configure computer
    computer = vasp_code.computer
    # create a clean workdir used by the computer
    workdir = pathlib.Path(tmpdir) / 'workdir'
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    computer.set_workdir(str(workdir.absolute()))
    # create a clean remote dir and populate it with the testfile
    remote_path = pathlib.Path(tmpdir) / 'remote_dir'
    if remote_path.exists():
        shutil.rmtree(remote_path)
    remote_path.mkdir(parents=True)
    # full path to the file of the remote (also create any subdirs inside
    # the remote folder if necessary)
    fpath = remote_path / testfile
    if not fpath.parent.exists():
        fpath.parent.mkdir(parents=True)
    # write some unique content to the file which allows it to be
    # identifies as file copied in from remote
    remote_content = "{} remote file of parent calculation".format(fpath.name)
    with open(fpath, 'w') as remote_file:
        remote_file.write(remote_content)
    remote_data = RemoteData(computer=computer, remote_path=str(remote_path))
    # connect the created remote folder to the calculation to simulate a
    # restarted calculation
    inputs = {
        'code': vasp_code,
        'custodian': {'code': cstdn_code},
        'restart': {'folder': remote_data},
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }

    # mock the central create_calculation_inputs() method which is defined
    # on the corresponding subclasses. here we simply replace it with a
    # a call to the restart_copy_remote() method (without any checks).
    # additionally the custodian spec file is written to check if it gets
    # accidentially copied to the working directory
    def mock(self, folder, calcinfo):
        self.restart_copy_remote(folder, calcinfo)
        spec_fname = folder.get_abs_path(PluginDefaults.CSTDN_SPEC_FNAME)
        pathlib.Path(spec_fname).touch()
        return calcinfo

    monkeypatch.setattr(CalculationBase, 'create_calculation_inputs', mock)
    monkeypatch.setattr(CalculationBase, 'expected_files', lambda self: None)
    # actually submit the calculation to check that remote contents are
    # indeed copied to the working directory
    calc_node = run_get_node(CalculationBase, **inputs)
    # inspect working directory files
    calc_workdir = pathlib.Path(calc_node.node.get_remote_workdir())
    calc_file_name = calc_workdir / testfile
    with open(calc_file_name, 'r') as calc_input_file:
        calc_file_content = calc_input_file.read()
    if from_remote:
        assert calc_file_content == remote_content
    else:
        assert calc_file_content != remote_content


@pytest.mark.parametrize('expected', [None, ['EXPECTED_FILE']])
def test_temporary_retrieve_list_default(vasp_code, expected):
    """Test temporary_retrieve list contents when no user input was defined"""
    from aiida_cusp.calculators.calculation_base import CalculationBase
    # the expected base retrieve list
    expected_list = [
        ('vasprun.xml', '.', 2),
        ('OUTCAR', '.', 2),
        ('CONTCAR', '.', 2),
        ('*/vasprun.xml', '.', 2),
        ('*/OUTCAR', '.', 2),
        ('*/CONTCAR', '.', 2),
    ]
    if expected is not None:
        expected_list.append((f'{expected[0]}', '.', 2))
        expected_list.append((f'*/{expected[0]}', '.', 2))
    inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    calc_base = CalculationBase(inputs=inputs)
    # setup the expected list that would have been returned by the parser
    calc_base.expected_files = lambda: expected
    calc_temp_list = calc_base.retrieve_temporary_list()
    assert len(calc_temp_list) == len(set(calc_temp_list))
    assert set(calc_temp_list) == set(expected_list)


@pytest.mark.parametrize('expected', [None, ['EXPECTED_FILE']])
def test_temporary_retrieve_list_user(vasp_code, expected):
    """Test temporary_retrieve list contents when user input was defined"""
    from aiida_cusp.calculators.calculation_base import CalculationBase
    # the expected retrieve list
    user_defined_file = 'USERFILE'
    expected_list = [
        (f"{user_defined_file}", '.', 2),
        (f"*/{user_defined_file}", '.', 2),
    ]
    if expected is not None:
        expected_list.append((f'{expected[0]}', '.', 2))
        expected_list.append((f'*/{expected[0]}', '.', 2))
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
                'retrieve_files': [user_defined_file],
            },
        },
    }
    calc_base = CalculationBase(inputs=inputs)
    # setup the expected list that would have been returned by the parser
    calc_base.expected_files = lambda: expected
    calc_temp_list = calc_base.retrieve_temporary_list()
    assert len(calc_temp_list) == len(set(calc_temp_list))
    assert set(calc_temp_list) == set(expected_list)


@pytest.mark.parametrize('expected', [None, ['EXPECTED_FILE']])
def test_temporary_retrieve_list_user_empty(vasp_code, expected):
    """
    Test temporary_retrieve list contents when user input was defined
    but list is empty list
    """
    from aiida_cusp.calculators.calculation_base import CalculationBase
    # the expected retrieve list
    expected_list = []
    if expected is not None:
        expected_list.append((f'{expected[0]}', '.', 2))
        expected_list.append((f'*/{expected[0]}', '.', 2))
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
                'retrieve_files': [],
            },
        },
    }
    calc_base = CalculationBase(inputs=inputs)
    # setup the expected list that would have been returned by the parser
    calc_base.expected_files = lambda: expected
    calc_temp_list = calc_base.retrieve_temporary_list()
    assert len(calc_temp_list) == len(set(calc_temp_list))
    assert set(calc_temp_list) == set(expected_list)


def test_permanent_retrieve_list(vasp_code):
    from aiida_cusp.calculators.calculation_base import CalculationBase
    from aiida_cusp.utils.defaults import PluginDefaults, CustodianDefaults
    # the expected retrieve list
    expected_list = [
        '_scheduler-stderr.txt',  # default AiiDA file for scheduler stderr
        '_scheduler-stdout.txt',  # default AiiDA file for scheduler stdout
        PluginDefaults.STDOUT_FNAME,  # aiida.out
        PluginDefaults.STDERR_FNAME,  # aiida.err
        '_aiidasubmit.sh',  # AiiDA's default submit script name
        PluginDefaults.CSTDN_SPEC_FNAME,  # cstdn_spec.yaml
        CustodianDefaults.RUN_LOG_FNAME,  # run.log
    ]
    inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }
    calc_base = CalculationBase(inputs=inputs)
    calc_perm_list = calc_base.retrieve_permanent_list()
    assert len(calc_perm_list) == len(expected_list)
    assert len(calc_perm_list) == len(set(calc_perm_list))
    assert set(calc_perm_list) == set(expected_list)


@pytest.mark.parametrize('suffixes', [[''], ['.job1'], ['.a', '.b', '.c'],
                         ['.samesuffix', '.samesuffix']])
def test_permanent_retrieve_list_with_suffix(vasp_code, suffixes):
    from aiida_cusp.calculators.calculation_base import CalculationBase
    from aiida_cusp.utils.defaults import PluginDefaults, CustodianDefaults
    from custodian.vasp.jobs import VaspJob
    # this is the permanent retrieve list that is not affected by any suffix
    # set for connected custodian jobs
    static_files = [
        '_scheduler-stderr.txt',  # default AiiDA file for scheduler stderr
        '_scheduler-stdout.txt',  # default AiiDA file for scheduler stdout
        PluginDefaults.STDERR_FNAME,  # aiida.err
        '_aiidasubmit.sh',  # AiiDA's default submit script name
        PluginDefaults.CSTDN_SPEC_FNAME,  # cstdn_spec.yaml
        CustodianDefaults.RUN_LOG_FNAME,  # run.log
    ]
    # these are the dynamic files contained in the permanent retrieved list
    # which are affected by the suffixes defined by connected custodian
    # jobs
    dynamic_files = [f"{PluginDefaults.STDOUT_FNAME}{s}" for s in suffixes]
    # the expected list is then the combination of all static and all
    # dynamically added files
    expected_files = static_files + dynamic_files
    # for each suffix, connect an individual VaspJob to the calculation
    jobs = [VaspJob(None, suffix=s) for s in suffixes]
    inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
        'custodian': {'jobs': jobs},
    }
    calc_base = CalculationBase(inputs=inputs)
    calc_perm_list = calc_base.retrieve_permanent_list()
    # check the calculated permanent retrieve list against the expected
    # list of permanent files
    assert len(calc_perm_list) == len(expected_files)
    assert set(calc_perm_list) == set(expected_files)


@pytest.mark.parametrize('retrieve_list', [[], ['A', 'B', 'C']])
@pytest.mark.parametrize('expected_list', [None, [], ['D', 'E', 'F'],
                         ['B', 'C', 'D']])
def test_files_to_retrieve_method(vasp_code, retrieve_list, expected_list):
    from aiida_cusp.calculators.calculation_base import CalculationBase
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
                'retrieve_files': retrieve_list,
            },
        },
    }
    calc_base = CalculationBase(inputs=inputs)
    # setup the expected list that would have been returned by the parser
    calc_base.expected_files = lambda: expected_list
    calc_temp_list = calc_base.files_to_retrieve()
    if expected_list is None:
        assert calc_temp_list == retrieve_list
    else:
        assert calc_temp_list == list(set(retrieve_list + expected_list))


def test_expected_files_method_raises_on_base(vasp_code):
    """
    Assure the expected_file() prototype method raises NotImplementedError
    on the calculation base class.
    """
    from aiida_cusp.calculators.calculation_base import CalculationBase
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
                'retrieve_files': [],
            },
        },
    }
    calc_base = CalculationBase(inputs=inputs)
    with pytest.raises(NotImplementedError) as exception:
        assert calc_base.expected_files()
