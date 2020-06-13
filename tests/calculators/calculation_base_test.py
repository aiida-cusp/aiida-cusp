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


def test_vasp_run_line_no_mpi(vasp_code):
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
def test_remote_folder_filelist(vasp_code, filename, relpath, aiida_sandbox):
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
def test_default_restart_files_exclude(submit_script_name, vasp_code):
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
    excluded_list = Base.restart_files_exclude()
    # capture if something went wrong and we have duplicate files in here
    assert len(set(excluded_list)) == len(excluded_list)
    # assert that both list contain the same elements (ignoring their index)
    assert set(excluded_list) == set(expected_list)


@pytest.mark.parametrize('method', ['create_inputs_for_restart_run',
                         'create_inputs_for_regular_run'])
def test_undefined_create_input_methods_raise(vasp_code, method,
                                              aiida_sandbox):
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


# check submit-script if only a vasp code is available
@pytest.mark.parametrize('withmpi', [True, False])
def test_prepare_for_submission_base_vasp(withmpi, vasp_code, cstdn_code,
                                          aiida_sandbox):
    from aiida_cusp.calculators import CalculationBase
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
    # silence the NotImplementedError (we do not need these methods here)
    Base.create_inputs_for_regular_run = lambda folder, calcinfo: None
    Base.create_inputs_for_restart_run = lambda folder, calcinfo: None
    # run prepare_for_submission() to write the submit script to the
    # sandbox folder
    calcinfo = Base.presubmit(aiida_sandbox)
    script = Base.inputs.metadata.options.submit_script_filename
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
    from aiida_cusp.calculators import CalculationBase
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
    Base.create_inputs_for_regular_run = lambda folder, calcinfo: None
    Base.create_inputs_for_restart_run = lambda folder, calcinfo: None
    # run prepare_for_submission() to write the submit script to the
    # sandbox folder
    calcinfo = Base.presubmit(aiida_sandbox)
    script = Base.inputs.metadata.options.submit_script_filename
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
def test_vasp_calculation_restart_copy_remote(vasp_code, cstdn_code, tmpdir,
                                              testfile, from_remote):
    import pathlib
    import shutil
    from aiida.orm import RemoteData
    from aiida.engine import run_get_node
    from aiida_cusp.utils.defaults import PluginDefaults
    from aiida_cusp.calculators import CalculationBase
    Base = CalculationBase.get_builder()

    # mock the create_inputs_for_restart_run() method which is undefined on
    # the CalculationBase class and simply replace it with a call to the
    # the restart_copy_remote() function (without any checks). Additionally
    # write the custodian spec to check if this file is accidentally copied
    # to the working directory
    def mock(self, folder, calcinfo):
        self.restart_copy_remote(folder, calcinfo)
        custodian_settings = self.setup_custodian_settings(is_neb=False)
        spec_fname = folder.get_abs_path(PluginDefaults.CSTDN_SPEC_FNAME)
        custodian_settings.write_custodian_spec(pathlib.Path(spec_fname))

    Base.process_class.create_inputs_for_restart_run = mock
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
    Base.code = vasp_code
    Base.custodian.code = cstdn_code
    Base.restart.folder = remote_data
    Base.metadata.options.resources = {'num_machines': 1}
    calc_node = run_get_node(Base)
    # inspect files
    calc_workdir = pathlib.Path(calc_node.node.get_remote_workdir())
    calc_file_name = calc_workdir / testfile
    with open(calc_file_name, 'r') as calc_input_file:
        calc_file_content = calc_input_file.read()
    if from_remote:
        assert calc_file_content == remote_content
    else:
        assert calc_file_content != remote_content
