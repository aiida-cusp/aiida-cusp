# -*- coding: utf-8 -*-


"""
Test suite for Custodian and related settings utility
"""


import pytest

from aiida_cusp.utils.defaults import CustodianDefaults


@pytest.mark.parametrize('is_neb', [True, False])
def test_setup_vasjob_settings_no_input(is_neb):
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
    defaults = dict(CustodianDefaults.CUSTODIAN_SETTINGS)
    updated = {key: val for key in defaults.keys()}
    settings = dict(updated)
    # instantiate custodian settings and test setup_vaspjob_settings method
    # with defined settings
    custodian_settings = CustodianSettings(val, val, val, settings={})
    output_settings = custodian_settings.setup_custodian_settings(settings)
    assert output_settings == updated


@pytest.mark.parametrize('handler_type', ['list', 'tuple', 'dict'])
def test_setup_custodian_handlers_from_valid_types(handler_type):
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import CustodianDefaults, PluginDefaults
    handlers_avail = dict(CustodianDefaults.ERROR_HANDLER_SETTINGS)
    if handler_type == 'list':
        handlers = list(handlers_avail.keys())
    elif handler_type == 'tuple':
        handlers = tuple(handlers_avail.keys())
    elif handler_type == 'dict':
        handlers = {h: {} for h in handlers_avail.keys()}
    else:
        raise
    # instantiate custodian settings and test setup_vaspjob_settings method
    # with defined settings
    vasp_cmd = None
    stdout = PluginDefaults.STDOUT_FNAME
    stderr = PluginDefaults.STDERR_FNAME
    custodian_settings = CustodianSettings(stdout, stderr, stdout)
    output_handlers = custodian_settings.setup_custodian_handlers(handlers)
    import_path = CustodianDefaults.HANDLER_IMPORT_PATH
    expected_output = {".".join([import_path, name]): params for name, params
                       in handlers_avail.items()}
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


@pytest.mark.parametrize('handler_name,handler_params',
                         CustodianDefaults.ERROR_HANDLER_SETTINGS.items())
def test_setup_custodian_handlers_with_params(handler_name, handler_params):
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import CustodianDefaults
    val = 'updated_val'
    custodian_settings = CustodianSettings(val, val, val)
    hdlr_param_updated = {p: val for p in dict(handler_params).keys()}
    hdlr_input = {handler_name: hdlr_param_updated}
    hdlr_output = custodian_settings.setup_custodian_handlers(hdlr_input)
    path = CustodianDefaults.HANDLER_IMPORT_PATH
    expected_output = {".".join([path, handler_name]): hdlr_param_updated}
    assert hdlr_output == expected_output


@pytest.mark.parametrize('handler_name',
                         CustodianDefaults.ERROR_HANDLER_SETTINGS.keys())
def test_setup_custodian_handlers_raises_for_invalid_param(handler_name):
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import CustodianDefaults, PluginDefaults
    from aiida_cusp.utils.exceptions import CustodianSettingsError
    vasp_cmd = None
    stdout = PluginDefaults.STDOUT_FNAME
    stderr = PluginDefaults.STDERR_FNAME
    custodian_settings = CustodianSettings(vasp_cmd, stdout, stderr)
    hdlr_input = {handler_name: {'this_is_an_invalid_handler_parameter': None}}
    with pytest.raises(CustodianSettingsError) as exception:
        hdlr_output = custodian_settings.setup_custodian_handlers(hdlr_input)
    assert "Invalid parameter" in str(exception.value)


@pytest.mark.parametrize('handler_type', ['list', 'tuple', 'dict'])
def test_custodian_settings_raises_on_unprocessed_handler(handler_type):
    from aiida_cusp.utils.custodian import CustodianSettings
    from aiida_cusp.utils.defaults import PluginDefaults
    from aiida_cusp.utils.exceptions import CustodianSettingsError
    if handler_type == 'list':
        handlers = ["ThisIsAnUnknownHandler"]
    elif handler_type == 'tuple':
        handlers = ("ThisIsAnUnknownHandler",)
    elif handler_type == 'dict':
        handlers = {"ThisIsAnUnknownHandler": {}}
    else:
        raise
    # instantiate custodian settings and test setup_vaspjob_settings method
    # with defined settings
    vasp_cmd = None
    stdout = PluginDefaults.STDOUT_FNAME
    stderr = PluginDefaults.STDERR_FNAME
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
    assert "Unknown Custodian setting(s)" in str(exception.value)


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
    handlers = []
    settings = {}  # use the default vasp / custodian settings
    cstdn_settings = CustodianSettings(vasp_cmd, stdout, stderr, is_neb=False,
                                       handlers=handlers, settings=settings)
    with pytest.raises(CustodianSettingsError) as exception:
        cstdn_settings.write_custodian_spec(outfile)
    assert str(exception.value).startswith('Given path') is True


def test_write_custodian_spec_yaml_format_with_handler_regular(tmpdir):
    import pathlib
    from aiida_cusp.utils.custodian import CustodianSettings
    outfile = pathlib.Path(tmpdir) / 'custodian_spec_file.yaml'
    # setup custom inputs including handler: use default settings for
    # vasp, custodian and the chosen handler
    vasp_cmd = ['mpirun', '-np', '4', '/path/to/vasp']
    stdout = 'stdout.txt'
    stderr = 'stderr.txt'
    handlers = ['VaspErrorHandler']  # use default settings for handler
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
        "    errors_subset_to_catch: null",
        "    natoms_large_cell: 100",
        "    output_filename: aiida.out",
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
    handlers = []  # use default settings for handler
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
    from aiida_cusp.utils.custodian import CustodianSettings
    outfile = pathlib.Path(tmpdir) / 'custodian_spec_file.yaml'
    # setup custom inputs including handler: use default settings for
    # vasp, custodian and the chosen handler
    vasp_cmd = ['mpirun', '-np', '4', '/path/to/vasp']
    stdout = 'stdout.txt'
    stderr = 'stderr.txt'
    handlers = ['VaspErrorHandler']  # use default settings for handler
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
        "    errors_subset_to_catch: null",
        "    natoms_large_cell: 100",
        "    output_filename: aiida.out",
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
        "    copy_magmom: false",
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
    handlers = []  # use default settings for handler
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
        "    copy_magmom: false",
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
