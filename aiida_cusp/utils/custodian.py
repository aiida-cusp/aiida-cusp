# -*- coding: utf-8 -*-


"""
Utility for translating plugin input parameters for Custodian and setting
up the input scripts for the Custodian executable.
"""


import yaml
import copy

from aiida_cusp.utils.exceptions import CustodianSettingsError
from aiida_cusp.utils.defaults import CustodianDefaults


def handler_serializer(input_data):
    """
    AiiDA compliant serializer for Custodian Handlers

    :param input_data: single custodian handler instance or list of multiple
        handler instances to be serialized
    :type input_data: `~custodian.custodian.ErrorHandler` or `list`
    :returns: dictionary containing the json serialzed contents of all
        handler passed in the `input_data` argument
    :rtype: `dict`
    """
    from custodian.custodian import ErrorHandler
    from aiida.orm import Dict

    try:
        handler_input_list = list(input_data)
    except TypeError:
        handler_input_list = [input_data]
    assert all([isinstance(h, ErrorHandler) for h in handler_input_list])
    handlers = dict()
    for (hdlr_id, handler) in enumerate(handler_input_list):
        hdlr_attr = handler.as_dict()
        hdlr_ver = hdlr_attr.pop('@version')
        hdlr_mod = hdlr_attr.pop('@module')
        hdlr_cls = hdlr_attr.pop('@class')
        hdlr_arg = hdlr_attr
        handlers[hdlr_cls] = {
            'name': hdlr_cls,
            'import_path': f"{hdlr_mod}.{hdlr_cls}",
            'args': hdlr_arg,
        }
    return Dict(dict=handlers)


def job_serializer(input_data):
    """
    AiiDA compliant serializer for Custodian Jobs

    :param input_data: single `~custodian.vasp.jobs.VaspJob` instance or list
        of multiple `~custodian.vasp.jobs.VaspJob` instances to be serialized
    :type input_data: `~custodian.vasp.jobs.VaspJob` or `list`
    :returns: dictionary containing the json serialzed contents of all
        `~custodian.vasp.jobs.VaspJob`s passed in the `input_data` argument
    :rtype: `dict`
    """
    from custodian.vasp.jobs import VaspJob
    from aiida.orm import Dict

    try:
        job_input_list = list(input_data)
    except TypeError:
        job_input_list = [input_data]
    assert all([isinstance(j, VaspJob) for j in job_input_list])
    jobs = dict()
    for (job_id, job) in enumerate(job_input_list):
        job_attr = job.as_dict()
        job_ver = job_attr.pop('@version')
        job_mod = job_attr.pop('@module')
        job_cls = job_attr.pop('@class')
        job_arg = job_attr
        jobs[f"{job_id}"] = {
            'name': job_cls,
            'import_path': f"{job_mod}.{job_cls}",
            'args': job_arg,
        }
    return Dict(dict=jobs)


def custodian_job_suffixes(jobs):
    """
    Extract and return possibly defined suffixes of Custodian jobs

    :param jobs: dictionary of Custodian jobs as defined by the
        aiida_cusp.utils.custodian.job_serializer() function
    :type jobs: `dict`
    :returns: a list composed of all suffixed extracted from the job
        dictionary
    :rtype: `list`
    """
    # if no jobs were passed to the calculation, we'll initialize a
    # single job internally with suffix set to `""`
    if not jobs:
        suffixes = [""]
    else:
        suffixes = []
        for job_id, job_attrs in jobs.items():
            suffix = job_attrs['args'].get('suffix', "")
            suffixes.append(suffix)
    return suffixes


class CustodianSettings(object):
    """
    Class to store Custodian settings and generate the required input files

    Any error handlers may be passed as either a `list` containing the handler
    names or a `dict` with handler names set as keys and the corresponding
    item defining the handler-settings as `dict`. In case of the handlers
    being passed as a `list` the default settings for the defined handlers
    will be applied.

    :param vasp_cmd: list of commands requird to run the VASP calculation
    :type vasp_cmd: `list`
    :param jobs: non-optional jobs parameter for custodian jobs being
        passed to the calculator
    :type jobs: `dict`
    :param settings: settings for the Custodian job
    :type settings: `dict`
    :param handlers: a set of error-correction handlers used to correct any
        errors occuring during the VASP calculation
    :type handlers: `list` or `dict`
    """

    def __init__(self, vasp_cmd, jobs, settings={}, handlers={},
                 validators={}):
        # store shared variables
        self.vasp_cmd = vasp_cmd
        # setup VASP error handlers connected to the calculation
        self.custodian_handlers = self.setup_custodian_handlers(handlers)
        # setup VASP jobs connected to the calculation
        self.custodian_jobs = self.setup_custodian_jobs(jobs)
        # setup VASP validators connected to the calculation
        self.custodian_validators = self.setup_custodian_validators(validators)
        # setup Custodian program settings
        self.custodian_settings = self.setup_custodian_settings(settings)

    def setup_custodian_settings(self, settings):
        """
        Define settings for the custodian program.

        Removes all Custodian program specific input parameters from the
        passed `settings` and complements missing parameters with given
        defaults.

        :param settings: dictionary containing the settings for the Custodian
            program
        :type settings: `dict`
        :returns: input settings for the Custodian program
        :rtype: `dict`
        """
        user_settings = copy.deepcopy(settings)
        default_settings = CustodianDefaults.CUSTODIAN_SETTINGS
        fixed_settings = CustodianDefaults.FIXED_CUSTODIAN_SETTINGS
        for parameter in list(user_settings.keys()):
            # fail if the parameter is not a valid custodian setting at all
            if parameter not in default_settings.keys():
                valid = ", ".join(default_settings.keys())
                raise CustodianSettingsError("got an invalid custodian "
                                             "setting '{}' (valid settings: "
                                             "{})".format(parameter, valid))
            # check if parameter is among the fixed parameters for which
            # defined default values shall be used only
            if parameter in fixed_settings:
                # we need to pop the value here so that we do not fail
                # the verify_settings() function
                _ = user_settings.pop(parameter)
                continue
            # otherwise: update the defaults from the user input
            default_settings[parameter] = user_settings.pop(parameter)
        self.validate_settings(user_settings)
        return default_settings

    def setup_custodian_handlers(self, handlers):
        """
        Define error handlers used by custodian.

        Accepts a dictionary of serialized custodian handler classes
        as returned by the `~aiida_cusp.utils.custodian.handler_serializer`
        function.

        :param handlers: dictionary of handlers and their corresponding
            parameters
        :type handlers: `dict`
        :returns: dictionary of handler module paths and the corresponding
            handler setings for all handlers defined in the input `handlers`
        :rtype: `dict`
        :raises CustodianSettingsError: if input parameter handlers is not
            of the correct type (i.e. list, tuple or dict)
        :raises CustodianSettingsError: if invalid parameter settings are
            found for a handler
        :raises CustodianSettingsError: if an invalid handler name is found
        """
        if not isinstance(handlers, dict):
            raise CustodianSettingsError("Invalid input type for 'handler', "
                                         "expected type '{}' but got type "
                                         "'{}'".format(type(dict()),
                                                       type(handlers)))
        handlers_dict = copy.deepcopy(handlers)
        handlers_and_settings = dict(CustodianDefaults.ERROR_HANDLER_SETTINGS)
        handler_import_and_params = {}
        for handler_name, handler_params in handlers_and_settings.items():
            try:
                user_handler_params = handlers_dict.pop(handler_name)
                user_handler_args = user_handler_params.pop('args')
                import_path = user_handler_params.pop('import_path')
                # override user-defined parameters with defined defaults
                # if there are any
                for param, value in handler_params.items():
                    user_handler_args[param] = value
                handler_import_and_params[import_path] = user_handler_args
            except KeyError:  # proceed with next handler if not found
                continue
        # raise if any remaining (i.e. unprocessed) handlers are found
        self.validate_handlers(handlers_dict)
        return handler_import_and_params

    def setup_custodian_jobs(self, jobs):
        """
        Define calculation jobs used by custodian

        Accepts a dictionary of serialized custodian job classes
        as returned by the `~aiida_cusp.utils.custodian.job_serializer`
        function.

        :param jobs: dictionary of custodian jobs and their corresponding
            parameters
        :type jobs: `dict`
        :returns: a list of tuples with the jobs import path as string
            in the first index and a dictionary of the job's parameters
            in the second index
        :rtype: `tuple`
        :raises AssertionError: if the job indices, used within the passed
            input dictionary, do not start at zero and are not consecutive
        :raises AssertionError: if the `vasp_cmd` parameter was not set to
            `None` before overwriting with the current path
        :raises CustodianSettingsError: if a non-modifiable parameter is
            missing from the given job inputs (this should never happen!)
        """
        jobs_dict = copy.deepcopy(dict(sorted(jobs.items())))
        job_import_and_params = []
        for (index, (jobid, job_dictionary)) in enumerate(jobs_dict.items()):
            # make sure we start at zero and preserve the correct order!
            assert index == int(jobid)
            job_type = job_dictionary.pop('name')
            job_import_path = job_dictionary.pop('import_path')
            job_args = job_dictionary.pop('args')
            # load the correct fixed parameters
            (default_args, fixed_args) = self.jobargs_from_string(job_type)
            # update non-modifiable job settings inplace
            for (arg_name, arg_value) in default_args.items():
                if arg_name not in fixed_args:
                    continue
                if arg_name not in job_args:
                    errmsg = (f"Expected parameter '{arg_name}' not found "
                              f"for given {job_type}")
                    raise CustodianSettingsError(errmsg)
                job_args[arg_name] = arg_value
            # finally, assert vasp_cmd was overwritten and set value
            # obtained from connected code
            assert job_args.pop('vasp_cmd') is None
            # replace vasp_cmd with $vasp_cmd to properly expand given
            # arguments when spec file is read by custodian
            job_args['$vasp_cmd'] = self.vasp_cmd
            # build list with import path and assiged parameters
            job_import_and_params.append((job_import_path, job_args))
        return job_import_and_params

    def setup_custodian_validators(self, validators):
        """
        Define validators classes used by custodian
        """
        # TODO: Validators are currently not supported to b setup
        #       for a custodian calculation.
        return []

    def jobargs_from_string(self, jobtype_name_as_string):
        """
        Take the jobtype, i.e. 'VaspJob' or 'VaspNEBJob', as string and
        return the corresponding fixed and default arguments

        :param jobtype_name_as_string: the name of the jobtype to be
            returned
        :type jobtype_name_as_string: `str`
        :returns: tuple with fixed and default parameters for the jobtype
            as defined by the plugin's defaults
        :rtype: `tuple`
        """
        if jobtype_name_as_string == 'VaspJob':
            default_args = CustodianDefaults.VASP_JOB_SETTINGS
            fixed_args = CustodianDefaults.VASP_JOB_FIXED_SETTINGS
        elif jobtype_name_as_string == 'VaspNEBJob':
            default_args = CustodianDefaults.VASP_NEB_JOB_SETTINGS
            fixed_args = CustodianDefaults.VASP_NEB_JOB_FIXED_SETTINGS
        return (default_args, fixed_args)

    def validate_handlers(self, handlers):
        """
        Check if `handlers` is empty, i.e. verify all handlers have been
        consumed.

        :param handlers: dictionary of handlers and parameters
        :type handlers: `dict`
        :raises CustodianSettingsError: if any remaining handler is found in
            the passed dictionary
        """
        if handlers:
            unknown_handlers = ", ".join(list(handlers.keys()))
            raise CustodianSettingsError("Unknown Error-Handler(s) '{}'"
                                         .format(unknown_handlers))

    def validate_settings(self, settings):
        """
        Check if `settings` is empty, i.e. verify that all custodian and vasp
        job settinhs have been consumed.

        :param settings: dictionary containing custodian and VASP job settings
        :type settings: `dict`
        :raises CustodianSettingsError: if any remaining setting is found in
            the passed dictionary
        """
        if settings:
            unknown_settings = ", ".join(list(settings.keys()))
            raise CustodianSettingsError("Unknown Custodian setting(s) '{}'"
                                         .format(unknown_settings))

    def write_custodian_spec(self, path_to_file):
        """
        Generate custodian specification yaml-file.

        Before writing the file all settings and handler contents are properly
        re-arranged such that the generated yaml-file is understood by the
        custodian command-line executable.

        :param path_to_file:
        :type path_to_file:
        :raises CustodianSettingsError: if the file defined by the passed
            `path_to_file` variable does not contain the .yaml suffix
        :return: None
        """
        # perform initial file-check
        expected_suffix = '.yaml'
        if not path_to_file.suffix == expected_suffix:
            raise CustodianSettingsError("Given path '{}' does not seem to "
                                         "represent a valid yaml file (suffix "
                                         "'{}' =/= '{}')"
                                         .format(path_to_file,
                                                 path_to_file.suffix,
                                                 expected_suffix))
        # job specification is expected as list of the form
        # [
        #   {'jb': job1_import_path, 'params': {'job1_params}},
        #   {'jb': job2_import_path, 'params': {'job2_params}},
        #   ...
        # ]
        connected_jobs = self.custodian_jobs
        custodian_jobs = [
            {'jb': j, 'params': p} for (j, p) in connected_jobs
        ]
        # handler specification is expected as list of the form
        # [
        #   {'hdlr': handler1_import_path, 'params': {'handler1_params}},
        #   {'hdlr': handler2_import_path, 'params': {'handler2_params}},
        #   ...
        # ]
        connected_handlers = self.custodian_handlers.items()
        custodian_handlers = [
            {'hdlr': h, 'params': p} for (h, p) in connected_handlers
        ]
        # validator specification is expected as list of the form
        # [
        #   {'vldr': validator1_import_path, 'params': {'validator1_params}},
        #   {'vldr': validator2_import_path, 'params': {'validator2_params}},
        #   ...
        # ]
        connected_validators = self.custodian_validators
        custodian_validators = [
            {'vldr': v, 'params': p} for (v, p) in connected_validators
        ]
        # custodian settings are expected to be of type dict
        custodian_settings = self.custodian_settings
        # finally combine the re-arranged contents to build the input
        # dictionary resulting in the yaml-file of the expected format
        custodian_spec_contents = {
            'jobs': custodian_jobs,
            'handlers': custodian_handlers,
            'validators': connected_validators,
            'custodian_params': custodian_settings,
        }
        # apply dirty hack to avoid aliases being used by yaml, see
        # https://stackoverflow.com/a/30682604
        yaml.Dumper.ignore_aliases = lambda *args: True
        # generate custodian input file
        cstdn_spec_file_contents = yaml.dump(custodian_spec_contents,
                                             explicit_start=False,
                                             default_flow_style=False,
                                             allow_unicode=True)
        with open(path_to_file.absolute(), 'w') as cstdn_spec_file:
            cstdn_spec_file.write(cstdn_spec_file_contents)
