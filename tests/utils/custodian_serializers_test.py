# -*- coding: utf-8 -*-


"""
Test suite for Custodian and related settings utility
"""


import pytest


def test_handler_serializer_return_val():
    """Test serializer returns aiida.orm.List type"""
    from aiida.orm import List
    from custodian.custodian import ErrorHandler
    from aiida_cusp.utils.custodian import handler_serializer
    generic_handler = ErrorHandler()
    retval = handler_serializer(generic_handler)
    assert isinstance(retval, List)
    assert len(retval) == 1
    retval = handler_serializer([generic_handler])
    assert isinstance(retval, List)
    assert len(retval) == 1
    n_hdlrs = 3
    retval = handler_serializer(n_hdlrs * [generic_handler])
    assert isinstance(retval, List)
    assert len(retval) == n_hdlrs


@pytest.mark.parametrize('entry_index,should_pass',
[   # noqa: E128
    (None, True),
    (0, False),
    (1, False),
    (2, False),
])
def test_demand_handler_types(entry_index, should_pass):
    """Check that only ErrorHandler types are accepted"""
    from aiida_cusp.utils.custodian import handler_serializer
    from custodian.custodian import ErrorHandler
    non_error_handler = "I am not a VaspJob Type!"
    generic_error_handler = ErrorHandler()
    testcase = 3 * [generic_error_handler]
    # taint the input list with a non VaspJob type
    if entry_index is not None:
        testcase[entry_index] = non_error_handler
    if not should_pass:
        with pytest.raises(AssertionError):
            result = handler_serializer(testcase)
    else:
        result = handler_serializer(testcase)


def test_handler_serialization():
    """Check serialized outputs for Handlers"""
    from aiida_cusp.utils.custodian import handler_serializer
    from custodian.custodian import ErrorHandler
    from custodian.vasp.handlers import VaspErrorHandler
    from aiida.orm import List
    expected_name = "custodian.custodian.ErrorHandler"
    expected_args = dict()
    # run serialization
    result = handler_serializer([ErrorHandler()])
    # check output
    assert isinstance(result, List)
    assert len(result) == 1
    # check serialized entries
    serialized_contents = result[0]
    assert isinstance(serialized_contents, dict)
    assert serialized_contents['name'] == expected_name
    assert serialized_contents['args'] == {}
    # also test with real ErrorHandler class and arguments
    expected_name = "custodian.vasp.handlers.VaspErrorHandler"
    expected_args = {
        "output_filename": "mycustom.fname",
        "natoms_large_cell": None,
        # instead of None (which expands to the full list of catchable
        # errors) use a defined subset to make this test predictable
        "errors_subset_to_catch": ["tet", "brmix", "too_few_bands"],
        "vtst_fixes": False,
    }
    handler = VaspErrorHandler(**expected_args)
    result = handler_serializer([handler])
    # check output
    assert isinstance(result, List)
    assert len(result) == 1
    # check serialized entries
    serialized_contents = result[0]
    assert isinstance(serialized_contents, dict)
    assert serialized_contents['name'] == expected_name
    serialized_args = serialized_contents['args']
    assert isinstance(serialized_args, dict)
    assert serialized_args == expected_args


def test_job_serializer_return_val():
    """Test serializer returns aiida.orm.List type"""
    from aiida.orm import List
    from custodian.vasp.jobs import VaspJob
    from aiida_cusp.utils.custodian import job_serializer
    vasp_job = VaspJob(vasp_cmd='vasp.exe')
    retval = job_serializer(vasp_job)
    assert isinstance(retval, List)
    assert len(retval) == 1
    retval = job_serializer([vasp_job])
    assert isinstance(retval, List)
    assert len(retval) == 1
    n_jobs = 7
    retval = job_serializer(n_jobs * [vasp_job])
    assert isinstance(retval, List)
    assert len(retval) == n_jobs


@pytest.mark.parametrize('jobtype', ['vasp_standard', 'vasp_neb'])
@pytest.mark.parametrize('entry_index,should_pass',
[   # noqa: E128
    (None, True),
    (0, False),
    (1, False),
    (2, False),
])
def test_demand_job_types(jobtype, entry_index, should_pass):
    """Check that only VaspJob types are accepted"""
    from aiida_cusp.utils.custodian import job_serializer
    from custodian.vasp.jobs import VaspJob, VaspNEBJob
    non_vasp_job = "I am not a VaspJob Type!"
    if jobtype == 'vasp_standard':
        vasp_job = VaspJob(vasp_cmd='vasp.exe')
    elif jobtype == 'vasp_neb':
        vasp_job = VaspNEBJob(vasp_cmd='vasp.exe')
    testcase = 3 * [vasp_job]
    # taint the input list with a non VaspJob type
    if entry_index is not None:
        testcase[entry_index] = non_vasp_job
    if not should_pass:
        with pytest.raises(AssertionError):
            result = job_serializer(testcase)
    else:
        result = job_serializer(testcase)


@pytest.mark.parametrize('jobtype', ['VaspJob', 'VaspNEBJob'])
def test_job_serialization(jobtype):
    """Check serialized outputs for Handlers"""
    from aiida_cusp.utils.custodian import job_serializer
    from custodian.vasp.jobs import VaspJob, VaspNEBJob
    from aiida.orm import List
    expected_args = {
        'vasp_cmd': 'my_vasp_cmd.exe',
        'output_file': 'vasp_output.txt',
        'stderr_file': 'vasp_stferr.txt',
        'suffix': 'thisismysuffixforthisjob',
        'final': True,
        'backup': True,
        'auto_npar': False,
        'auto_gamma': True,
        'settings_override': None,
        'gamma_vasp_cmd': None,
        'copy_magmom': False,
        'auto_continue': False,
    }
    if jobtype == 'VaspJob':
        expected_name = "custodian.vasp.jobs.VaspJob"
        Job = VaspJob
    elif jobtype == 'VaspNEBJob':
        expected_name = "custodian.vasp.jobs.VaspNEBJob"
        # update the argument list for neb jobs
        expected_args.pop('copy_magmom')
        expected_args['auto_continue'] = True
        expected_args['half_kpts'] = False
        Job = VaspNEBJob
    result = job_serializer([Job(**expected_args)])
    assert isinstance(result, List)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert result[0]['name'] == expected_name
    assert result[0]['args'] == expected_args
