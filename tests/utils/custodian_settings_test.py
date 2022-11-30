# -*- coding: utf-8 -*-


"""
Test suite for Custodian and related settings utility
"""


import pytest

from aiida_cusp.utils.defaults import CustodianDefaults


@pytest.mark.parametrize('job_type,fixed_args,default_args',
[  # noqa: E128
    ('VaspJob',
     CustodianDefaults.VASP_JOB_FIXED_SETTINGS,
     CustodianDefaults.VASP_JOB_SETTINGS),
    ('VaspNEBJob',
     CustodianDefaults.VASP_NEB_JOB_FIXED_SETTINGS,
     CustodianDefaults.VASP_NEB_JOB_SETTINGS),
])
def test_jobargs_from_string(job_type, fixed_args, default_args):
    """Test jobargs_from_string() function return types"""
    from aiida_cusp.utils.custodian import CustodianSettings
    csettings = CustodianSettings("", "", "")
    return_value = csettings.jobargs_from_string(job_type)
    assert isinstance(return_value, tuple)
    assert len(return_value) == 2
    assert return_value[0] == default_args
    assert return_value[1] == fixed_args


@pytest.mark.parametrize('fixed_arg',
                         CustodianDefaults.VASP_JOB_FIXED_SETTINGS)
def test_setup_jobs_raises_on_missing_arg(fixed_arg):
    """Check we raise if fixed arguments are missing during job setup"""
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.custodian import job_serializer
    from aiida_cusp.utils.exceptions import CustodianSettingsError
    from custodian.vasp.jobs import VaspJob
    job_dict = job_serializer(VaspJob('vasp_cmd')).get_dict()
    # try to setup the custodian job and assert we do not raise
    csettings = CustodianSettings("", "", "")
    csettings.setup_custodian_jobs(job_dict)
    # remove fixed argument from the job arguments and assert we do raise
    _ = job_dict['0']['args'].pop(fixed_arg)
    with pytest.raises(CustodianSettingsError) as exc:
        _ = csettings.setup_custodian_jobs(job_dict)
    assert f"Expected parameter '{fixed_arg}' not found" in str(exc.value)


@pytest.mark.parametrize('fixed_arg',
                         CustodianDefaults.VASP_NEB_JOB_FIXED_SETTINGS)
def test_setup_neb_jobs_raises_on_missing_arg(fixed_arg):
    """Check we raise if fixed arguments are missing during NEB job setup"""
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.custodian import job_serializer
    from aiida_cusp.utils.exceptions import CustodianSettingsError
    from custodian.vasp.jobs import VaspNEBJob
    job_dict = job_serializer(VaspNEBJob('vasp_cmd')).get_dict()
    # try to setup the custodian job and assert we do not raise
    csettings = CustodianSettings("", "", "")
    csettings.setup_custodian_jobs(job_dict)
    # remove fixed argument from the job arguments and assert we do raise
    _ = job_dict['0']['args'].pop(fixed_arg)
    with pytest.raises(CustodianSettingsError) as exc:
        _ = csettings.setup_custodian_jobs(job_dict)
    assert f"Expected parameter '{fixed_arg}' not found" in str(exc.value)


@pytest.mark.parametrize('fixed_args,default_args',
[  # noqa: E128
    (CustodianDefaults.VASP_JOB_FIXED_SETTINGS,
     CustodianDefaults.VASP_JOB_SETTINGS),
    (CustodianDefaults.VASP_NEB_JOB_FIXED_SETTINGS,
     CustodianDefaults.VASP_NEB_JOB_SETTINGS),
])
def test_overwrite_only_fixed_job_args(fixed_args, default_args):
    """Assert only fixed parameters are overwritten"""
    from aiida_cusp.utils.custodian import CustodianSettings
    value = "user_input_value"
    vasp_cmd = "vasp.exe"
    # try to setup the custodian job and assert we do not raise
    csettings = CustodianSettings(vasp_cmd, "", "")
    args = {fixed_arg: value for fixed_arg in fixed_args}
    args['non_fixed_arg'] = value
    job_dict = {
        '0': {
            'name': 'VaspJob',
            'import_path': 'NotRequired',
            'args': args,
        }
    }
    (_, args) = csettings.setup_custodian_jobs(job_dict)[0]
    # the vasp_cmd is not set from the provided default parameters but
    # rather from the value passed to CustodianSettins.__init__()
    assert args.pop('vasp_cmd') == vasp_cmd
    # other fixed arguments should have been replaced with the defined
    # defaults, tough
    for fixed_arg in fixed_args:
        if fixed_arg == 'vasp_cmd':
            continue
        assert args.pop(fixed_arg) == default_args[fixed_arg]
    # finally, we check that the only remaining parameter is the one
    # defined by the user and that it is, indeed, unchanged
    assert len(args) == 1
    assert args.pop('non_fixed_arg') == value


def test_preserve_jobid_start():
    """Check assertion error if jobid does not start at zero index"""
    from aiida_cusp.utils.custodian import CustodianSettings
    csettings = CustodianSettings("", "", "")
    job_dict = {'1': {}}  # not further args required as we should fail early
    with pytest.raises(AssertionError) as exception:
        _ = csettings.setup_custodian_jobs(job_dict)


@pytest.mark.parametrize('is_neb', [True, False])
def test_setup_vaspjob_settings_no_input(is_neb):
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import CustodianDefaults, PluginDefaults
    vasp_cmd = None
    stdout = PluginDefaults.STDOUT_FNAME
    stderr = PluginDefaults.STDERR_FNAME
    if is_neb:
        defaults = dict(CustodianDefaults.VASP_NEB_JOB_SETTINGS)
    else:
        defaults = dict(CustodianDefaults.VASP_JOB_SETTINGS)
    # instantiate custodian settings with default values for vasp_cmd, stdout
    # and stderr
    custodian_settings = CustodianSettings(vasp_cmd, stdout, stderr,
                                           settings={}, is_neb=is_neb)
    output_settings = custodian_settings.setup_vaspjob_settings({})
    assert output_settings == defaults


@pytest.mark.parametrize('is_neb', [True, False])
def test_setup_vaspjob_settings_with_inputs(is_neb):
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import CustodianDefaults
    val = 'updated_value'
    if is_neb:
        defaults = dict(CustodianDefaults.VASP_NEB_JOB_SETTINGS)
    else:
        defaults = dict(CustodianDefaults.VASP_JOB_SETTINGS)
    updated = {key: val for key in defaults.keys()}
    settings = dict(updated)
    # pop non-optional parameters from settings
    settings.pop('vasp_cmd')
    settings.pop('output_file')
    settings.pop('stderr_file')
    # instantiate custodian settings and test setup_vaspjob_settings method
    # with defined settings
    custodian_settings = CustodianSettings(val, val, val, settings={},
                                           is_neb=is_neb)
    output_settings = custodian_settings.setup_vaspjob_settings(settings)
    assert output_settings == updated


def test_setup_custodian_settings_no_inputs():
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import CustodianDefaults
    val = 'updated_value'
    defaults = dict(CustodianDefaults.CUSTODIAN_SETTINGS)
    # instantiate custodian settings and test setup_vaspjob_settings method
    # with defined settings
    custodian_settings = CustodianSettings(val, val, val, settings={})
    output_settings = custodian_settings.setup_custodian_settings({})
    assert output_settings == defaults


def test_setup_custodian_settings_with_inputs():
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import CustodianDefaults
    val = 'updated_value'
    settings = {key: val for key in CustodianDefaults.MODIFIABLE_SETTINGS}
    # update default parameters with given value
    expected_settings = dict(CustodianDefaults.CUSTODIAN_SETTINGS)
    expected_settings.update(settings)
    # instantiate custodian settings and test setup_custodian_settings method
    # with defined settings
    custodian_settings = CustodianSettings(val, val, val, settings={})
    output_settings = custodian_settings.setup_custodian_settings(settings)
    assert output_settings == expected_settings


@pytest.mark.parametrize('protected_custodian_setting',
[   # noqa: E128
    'max_errors_per_job',
    'scratch_dir',
    'gzipped_output',
    'checkpoint',
    'terminate_func',
    'terminate_on_nonzero_returncode',
])
def test_protected_custodian_settings(protected_custodian_setting):
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.exceptions import CustodianSettingsError
    settings = {protected_custodian_setting: None}
    with pytest.raises(CustodianSettingsError) as exception:
        _ = CustodianSettings("", "", "", settings=settings)
    expected_error = "cannot set value for protected custodian setting"
    assert expected_error in str(exception.value)


def test_setup_custodian_handlers_from_valid_types():
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import CustodianDefaults, PluginDefaults
    handlers_avail = dict(CustodianDefaults.ERROR_HANDLER_SETTINGS)
    handlers = {}
    for handler, arguments in handlers_avail.items():
        handlers[handler] = {
            'name': handler,
            'import_path': f"some.random.python.path.{handler}",
            'args': arguments,
        }
    # instantiate custodian settings and test setup_vaspjob_settings method
    # with defined settings
    vasp_cmd = None
    stdout = PluginDefaults.STDOUT_FNAME
    stderr = PluginDefaults.STDERR_FNAME
    custodian_settings = CustodianSettings(stdout, stderr, stdout)
    output_handlers = custodian_settings.setup_custodian_handlers(handlers)
    expected_output = {item['import_path']: item['args'] for key, item
                       in handlers.items()}
    assert output_handlers == expected_output


# mark this as parametrize to easily add possibly future tests (the only
# reasonable invalid type that may be passed for the handler I can think of
# is a string)
@pytest.mark.parametrize('handler', ["VaspErrorHandler"])
def test_setup_custodian_handlers_raises_on_invalid_type(handler):
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import CustodianDefaults, PluginDefaults
    from aiida_cusp.utils.exceptions import CustodianSettingsError
    # instantiate custodian settings and test setup_vaspjob_settings method
    # with defined settings
    vasp_cmd = None
    stdout = PluginDefaults.STDOUT_FNAME
    stderr = PluginDefaults.STDERR_FNAME
    custodian_settings = CustodianSettings(vasp_cmd, stderr, stdout)
    # test invalid handler type
    with pytest.raises(CustodianSettingsError) as exception:
        _ = custodian_settings.setup_custodian_handlers(handler)
    assert "Invalid input type for 'handler'" in str(exception.value)
    # verify this works for a dictionary being passed
    _ = custodian_settings.setup_custodian_handlers(dict())


@pytest.mark.parametrize('handler_name,handler_params',
                         CustodianDefaults.ERROR_HANDLER_SETTINGS.items())
def test_setup_custodian_handlers_uses_defaults(handler_name, handler_params):
    """Verify defaults override user input"""
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import CustodianDefaults
    path = CustodianDefaults.HANDLER_IMPORT_PATH
    val = 'updated_val'
    custodian_settings = CustodianSettings(val, val, val)
    hdlr_param_updated = {
        'name': handler_name,
        'import_path': f"{path}.{handler_name}",
        'args': {p: val for p in dict(handler_params).keys()},
    }
    hdlr_input = {handler_name: hdlr_param_updated}
    hdlr_output = custodian_settings.setup_custodian_handlers(hdlr_input)
    path = CustodianDefaults.HANDLER_IMPORT_PATH
    # assert generated output now contains the defined default values
    expected_output = {".".join([path, handler_name]): handler_params}
    assert hdlr_output == expected_output


def test_custodian_validate_handlers():
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import PluginDefaults
    from aiida_cusp.utils.exceptions import CustodianSettingsError
    # instantiate custodian settings and test setup_vaspjob_settings method
    # with defined settings
    vasp_cmd = None
    stdout = PluginDefaults.STDOUT_FNAME
    stderr = PluginDefaults.STDERR_FNAME
    # check that we do not raise on an empty dict (i.e. all handlers have
    # been processed inside the setup_custodian_handlers() method
    _ = CustodianSettings(vasp_cmd, stdout, stderr, handlers=dict())
    # otherwise, check that we raise
    handlers = {'UnprocessedHandler': {}}
    with pytest.raises(CustodianSettingsError) as exception:
        _ = CustodianSettings(vasp_cmd, stdout, stderr, handlers=handlers)
    assert "Unknown Error-Handler(s)" in str(exception.value)


def test_custodian_settings_raises_on_unprocessed_settings():
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import PluginDefaults
    from aiida_cusp.utils.exceptions import CustodianSettingsError
    settings = {"this_is_and_unknown_settings_key": None}
    # instantiate custodian settings and test setup_vaspjob_settings method
    # with defined settings
    vasp_cmd = None
    stdout = PluginDefaults.STDOUT_FNAME
    stderr = PluginDefaults.STDERR_FNAME
    with pytest.raises(CustodianSettingsError) as exception:
        _ = CustodianSettings(vasp_cmd, stdout, stderr, settings=settings)
    assert "got an invalid custodian setting" in str(exception.value)


def test_write_custodian_spec_raises_on_wrong_filetype(tmpdir):
    import pathlib
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.exceptions import CustodianSettingsError
    outfile = pathlib.Path(tmpdir) / 'custodian_spec_file.not_yaml_suffix'
    # setup custom inputs including handler: use default settings for
    # vasp, custodian and the chosen handler
    vasp_cmd = ['vasp']
    stdout = 'stdout.txt'
    stderr = 'stderr.txt'
    handlers = {}
    settings = {}  # use the default vasp / custodian settings
    cstdn_settings = CustodianSettings(vasp_cmd, stdout, stderr, is_neb=False,
                                       handlers=handlers, settings=settings)
    with pytest.raises(CustodianSettingsError) as exception:
        cstdn_settings.write_custodian_spec(outfile)
    assert str(exception.value).startswith('Given path') is True


def test_write_custodian_spec_yaml_format_with_handler_regular(tmpdir):
    import pathlib
    from custodian.vasp.handlers import VaspErrorHandler
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.custodian import handler_serializer
    outfile = pathlib.Path(tmpdir) / 'custodian_spec_file.yaml'
    # setup custom inputs including handler: use default settings for
    # vasp, custodian and the chosen handler
    vasp_cmd = ['mpirun', '-np', '4', '/path/to/vasp']
    stdout = 'stdout.txt'
    stderr = 'stderr.txt'
    handlers = dict(handler_serializer(VaspErrorHandler()))
    settings = {}  # use the default vasp / custodian settings
    cstdn_settings = CustodianSettings(vasp_cmd, stdout, stderr, is_neb=False,
                                       handlers=handlers, settings=settings)
    assert outfile.is_file() is False  # check file is not already there
    cstdn_settings.write_custodian_spec(outfile)
    assert outfile.is_file() is True  # check file was written
    expected_spec_file_content = "\n".join([
        "custodian_params:",
        "  checkpoint: false",
        "  gzipped_output: false",
        "  max_errors: 10",
        "  max_errors_per_job: null",
        "  monitor_freq: 30",
        "  polling_time_step: 10",
        "  scratch_dir: null",
        "  skip_over_errors: false",
        "  terminate_func: null",
        "  terminate_on_nonzero_returncode: false",
        "handlers:",
        "- hdlr: custodian.vasp.handlers.VaspErrorHandler",
        "  params:",
        "    errors_subset_to_catch:",
        "    - tet",
        "    - inv_rot_mat",
        "    - brmix",
        "    - subspacematrix",
        "    - tetirr",
        "    - incorrect_shift",
        "    - real_optlay",
        "    - rspher",
        "    - dentet",
        "    - too_few_bands",
        "    - triple_product",
        "    - rot_matrix",
        "    - brions",
        "    - pricel",
        "    - zpotrf",
        "    - amin",
        "    - zbrent",
        "    - pssyevx",
        "    - eddrmm",
        "    - edddav",
        "    - algo_tet",
        "    - grad_not_orth",
        "    - nicht_konv",
        "    - zheev",
        "    - elf_kpar",
        "    - elf_ncl",
        "    - rhosyg",
        "    - posmap",
        "    - point_group",
        "    - symprec_noise",
        "    - dfpt_ncore",
        "    - bravais",
        "    - nbands_not_sufficient",
        "    - hnform",
        "    - coef",
        "    natoms_large_cell: null",
        "    output_filename: aiida.out",
        "    vtst_fixes: false",
        "jobs:",
        "- jb: custodian.vasp.jobs.VaspJob",
        "  params:",
        "    $vasp_cmd:",
        "    - mpirun",
        "    - -np",
        "    - '4'",
        "    - /path/to/vasp",
        "    auto_continue: false",
        "    auto_gamma: false",
        "    auto_npar: false",
        "    backup: true",
        "    copy_magmom: false",
        "    final: true",
        "    gamma_vasp_cmd: null",
        "    output_file: stdout.txt",
        "    settings_override: null",
        "    stderr_file: stderr.txt",
        "    suffix: ''",
    ]) + "\n"
    with open(outfile, 'r') as custodian_spec_file:
        custodian_spec_file_content = custodian_spec_file.read()
    assert custodian_spec_file_content == expected_spec_file_content


def test_write_custodian_spec_yaml_format_without_handler_regular(tmpdir):
    import pathlib
    from aiida_cusp.utils.custodian import CustodianSettings
    outfile = pathlib.Path(tmpdir) / 'custodian_spec_file.yaml'
    # setup custom inputs including handler: use default settings for
    # vasp, custodian and the chosen handler
    vasp_cmd = ['mpirun', '-np', '4', '/path/to/vasp']
    stdout = 'stdout.txt'
    stderr = 'stderr.txt'
    handlers = {}  # use default settings for handler
    settings = {}  # use the default vasp / custodian settings
    cstdn_settings = CustodianSettings(vasp_cmd, stdout, stderr, is_neb=False,
                                       handlers=handlers, settings=settings)
    assert outfile.is_file() is False  # check file is not already there
    cstdn_settings.write_custodian_spec(outfile)
    assert outfile.is_file() is True  # check file was written
    expected_spec_file_content = "\n".join([
        "custodian_params:",
        "  checkpoint: false",
        "  gzipped_output: false",
        "  max_errors: 10",
        "  max_errors_per_job: null",
        "  monitor_freq: 30",
        "  polling_time_step: 10",
        "  scratch_dir: null",
        "  skip_over_errors: false",
        "  terminate_func: null",
        "  terminate_on_nonzero_returncode: false",
        "handlers: []",
        "jobs:",
        "- jb: custodian.vasp.jobs.VaspJob",
        "  params:",
        "    $vasp_cmd:",
        "    - mpirun",
        "    - -np",
        "    - '4'",
        "    - /path/to/vasp",
        "    auto_continue: false",
        "    auto_gamma: false",
        "    auto_npar: false",
        "    backup: true",
        "    copy_magmom: false",
        "    final: true",
        "    gamma_vasp_cmd: null",
        "    output_file: stdout.txt",
        "    settings_override: null",
        "    stderr_file: stderr.txt",
        "    suffix: ''",
    ]) + "\n"
    with open(outfile, 'r') as custodian_spec_file:
        custodian_spec_file_content = custodian_spec_file.read()
    assert custodian_spec_file_content == expected_spec_file_content


def test_write_custodian_spec_yaml_format_with_handler_neb(tmpdir):
    import pathlib
    from custodian.vasp.handlers import VaspErrorHandler
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.custodian import handler_serializer
    outfile = pathlib.Path(tmpdir) / 'custodian_spec_file.yaml'
    # setup custom inputs including handler: use default settings for
    # vasp, custodian and the chosen handler
    vasp_cmd = ['mpirun', '-np', '4', '/path/to/vasp']
    stdout = 'stdout.txt'
    stderr = 'stderr.txt'
    handlers = dict(handler_serializer(VaspErrorHandler()))
    settings = {}  # use the default vasp / custodian settings
    cstdn_settings = CustodianSettings(vasp_cmd, stdout, stderr, is_neb=True,
                                       handlers=handlers, settings=settings)
    assert outfile.is_file() is False  # check file is not already there
    cstdn_settings.write_custodian_spec(outfile)
    assert outfile.is_file() is True  # check file was written
    expected_spec_file_content = "\n".join([
        "custodian_params:",
        "  checkpoint: false",
        "  gzipped_output: false",
        "  max_errors: 10",
        "  max_errors_per_job: null",
        "  monitor_freq: 30",
        "  polling_time_step: 10",
        "  scratch_dir: null",
        "  skip_over_errors: false",
        "  terminate_func: null",
        "  terminate_on_nonzero_returncode: false",
        "handlers:",
        "- hdlr: custodian.vasp.handlers.VaspErrorHandler",
        "  params:",
        "    errors_subset_to_catch:",
        "    - tet",
        "    - inv_rot_mat",
        "    - brmix",
        "    - subspacematrix",
        "    - tetirr",
        "    - incorrect_shift",
        "    - real_optlay",
        "    - rspher",
        "    - dentet",
        "    - too_few_bands",
        "    - triple_product",
        "    - rot_matrix",
        "    - brions",
        "    - pricel",
        "    - zpotrf",
        "    - amin",
        "    - zbrent",
        "    - pssyevx",
        "    - eddrmm",
        "    - edddav",
        "    - algo_tet",
        "    - grad_not_orth",
        "    - nicht_konv",
        "    - zheev",
        "    - elf_kpar",
        "    - elf_ncl",
        "    - rhosyg",
        "    - posmap",
        "    - point_group",
        "    - symprec_noise",
        "    - dfpt_ncore",
        "    - bravais",
        "    - nbands_not_sufficient",
        "    - hnform",
        "    - coef",
        "    natoms_large_cell: null",
        "    output_filename: aiida.out",
        "    vtst_fixes: false",
        "jobs:",
        "- jb: custodian.vasp.jobs.VaspNEBJob",
        "  params:",
        "    $vasp_cmd:",
        "    - mpirun",
        "    - -np",
        "    - '4'",
        "    - /path/to/vasp",
        "    auto_continue: false",
        "    auto_gamma: false",
        "    auto_npar: false",
        "    backup: true",
        "    final: true",
        "    gamma_vasp_cmd: null",
        "    half_kpts: false",
        "    output_file: stdout.txt",
        "    settings_override: null",
        "    stderr_file: stderr.txt",
        "    suffix: ''",
    ]) + "\n"
    with open(outfile, 'r') as custodian_spec_file:
        custodian_spec_file_content = custodian_spec_file.read()
    assert custodian_spec_file_content == expected_spec_file_content


def test_write_custodian_spec_yaml_format_without_handler_neb(tmpdir):
    import pathlib
    from aiida_cusp.utils.custodian import CustodianSettings
    outfile = pathlib.Path(tmpdir) / 'custodian_spec_file.yaml'
    # setup custom inputs including handler: use default settings for
    # vasp, custodian and the chosen handler
    vasp_cmd = ['mpirun', '-np', '4', '/path/to/vasp']
    stdout = 'stdout.txt'
    stderr = 'stderr.txt'
    handlers = {}  # use default settings for handler
    settings = {}  # use the default vasp / custodian settings
    cstdn_settings = CustodianSettings(vasp_cmd, stdout, stderr, is_neb=True,
                                       handlers=handlers, settings=settings)
    assert outfile.is_file() is False  # check file is not already there
    cstdn_settings.write_custodian_spec(outfile)
    assert outfile.is_file() is True  # check file was written
    expected_spec_file_content = "\n".join([
        "custodian_params:",
        "  checkpoint: false",
        "  gzipped_output: false",
        "  max_errors: 10",
        "  max_errors_per_job: null",
        "  monitor_freq: 30",
        "  polling_time_step: 10",
        "  scratch_dir: null",
        "  skip_over_errors: false",
        "  terminate_func: null",
        "  terminate_on_nonzero_returncode: false",
        "handlers: []",
        "jobs:",
        "- jb: custodian.vasp.jobs.VaspNEBJob",
        "  params:",
        "    $vasp_cmd:",
        "    - mpirun",
        "    - -np",
        "    - '4'",
        "    - /path/to/vasp",
        "    auto_continue: false",
        "    auto_gamma: false",
        "    auto_npar: false",
        "    backup: true",
        "    final: true",
        "    gamma_vasp_cmd: null",
        "    half_kpts: false",
        "    output_file: stdout.txt",
        "    settings_override: null",
        "    stderr_file: stderr.txt",
        "    suffix: ''",
    ]) + "\n"
    with open(outfile, 'r') as custodian_spec_file:
        custodian_spec_file_content = custodian_spec_file.read()
    assert custodian_spec_file_content == expected_spec_file_content
