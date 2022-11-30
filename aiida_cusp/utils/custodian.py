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
    :param stdout_fname: name of the file used to log messages send to stdout
    :type stdout_fname: `str`
    :param stderr_fname: name of the file used to log messages send to stderr
    :type stderr_fname: `str`
    :param settings: settings for the Custodian job
    :type settings: `dict`
    :param handlers: a set of error-correction handlers used to correct any
        errors occuring during the VASP calculation
    :type handlers: `list` or `dict`
    """

    def __init__(self, vasp_cmd, stdout_fname, stderr_fname, settings={},
                 handlers={}, jobs={}, is_neb=False):
        # store shared variables
        self.vasp_cmd = vasp_cmd
        self.stderr = stderr_fname
        self.stdout = stdout_fname
        self._is_neb = is_neb
        # setup VASP error handlers connected to the calculation
        self.custodian_handlers = self.setup_custodian_handlers(handlers)
        # setup VASP and Custodian program settings
        self.custodian_settings = self.setup_custodian_settings(settings)
        self.vaspjob_settings = self.setup_vaspjob_settings(settings)
        # check for any unused parameters in `settings`
        self.validate_settings(settings)

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
        cstdn_settings = dict(CustodianDefaults.CUSTODIAN_SETTINGS)
        valid_settings = CustodianDefaults.CUSTODIAN_SETTINGS
        for parameter in list(settings.keys()):
            # fail if the parameter is not a valid custodian setting at all
            if parameter not in cstdn_settings.keys():
                valid = ", ".join(valid_settings)
                raise CustodianSettingsError("got an invalid custodian "
                                             "setting '{}' (valid settings: "
                                             "{})".format(parameter, valid))
            # fail if the parameter is valid setting but not modifiable
            if parameter not in CustodianDefaults.CUSTODIAN_SETTINGS:
                raise CustodianSettingsError("cannot set value for protected "
                                             "custodian setting '{}'"
                                             .format(parameter))
            # otherwise: update the defaults from the user input
            cstdn_settings[parameter] = settings.pop(parameter)
        return cstdn_settings

    def setup_custodian_handlers(self, handlers):
        """
        Define error handlers used by custodian.

        Accepts a dictionary of deserialized custodian handler classes.
        Thereby, each dictionary key corresponds to the name of a used
        handler.

        :param handlers: dictionary of handlers and their corresponding
            user-defined parameters
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
        :param jobs:
        :type jobs: dict
        :returns:
        :rtype: dict
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
            assert job_args['vasp_cmd'] is None
            job_args['vasp_cmd'] = self.vasp_cmd
            # build list with import path and assiged parameters
            job_import_and_params.append((job_import_path, job_args))
        return job_import_and_params

    def jobargs_from_string(self, jobtype_name_as_string):
        """
        Take the jobtype, i.e. 'VaspJob' or 'VaspNEBJob', as string and
        return the corresponding fixed and default arguments

        :param jobtype_name_as_string: the name of the jobtype to be
            returned
        :type jobtype_name_as_string: string
        :returns: tuple with fixed and default parameters for the jobtype
            as defined by the plugin's defaults
        :rtype: tuple
        """
        if jobtype_name_as_string == 'VaspJob':
            default_args = CustodianDefaults.VASP_JOB_SETTINGS
            fixed_args = CustodianDefaults.VASP_JOB_FIXED_SETTINGS
        elif jobtype_name_as_string == 'VaspNEBJob':
            default_args = CustodianDefaults.VASP_NEB_JOB_SETTINGS
            fixed_args = CustodianDefaults.VASP_NEB_JOB_FIXED_SETTINGS
        return (default_args, fixed_args)

    def setup_vaspjob_settings(self, settings):
        """
        Define settings for the VASP program.

        Removes all VASP program specific input parameters from the passed
        `settings` and complements missing parameters with given defaults

        :param settings: dictionary containing the settings for the VASP job
        :type settings: `dict`
        :param is_neb: set to `True` if the VASP job is of type NEB
        :type is_neb: `bool`
        """
        if self._is_neb:
            job_settings = dict(CustodianDefaults.VASP_NEB_JOB_SETTINGS)
        else:
            job_settings = dict(CustodianDefaults.VASP_JOB_SETTINGS)
        # since job_settings is set to the default values at this point it
        # contains **all** available parameters
        for parameter in job_settings.keys():
            try:
                job_settings[parameter] = settings.pop(parameter)
            except KeyError:
                continue
        # finally setup the non-optional parameters and return the completed
        # settings dictionary
        job_settings['vasp_cmd'] = self.vasp_cmd
        job_settings['output_file'] = self.stdout
        job_settings['stderr_file'] = self.stderr
        return job_settings

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
        # replace vasp_cmd with $vasp_cmd to properly expand given arguments
        # when spec file is read by custodian
        vasp_job_settings = dict(self.vaspjob_settings)
        vasp_job_settings['$vasp_cmd'] = vasp_job_settings.pop('vasp_cmd')
        # setup a single vasp-job but distinguish between regular and neb
        # calculations due to the different folder structures
        if self._is_neb:
            vasp_job_type = CustodianDefaults.VASP_NEB_JOB_IMPORT_PATH
        else:
            vasp_job_type = CustodianDefaults.VASP_JOB_IMPORT_PATH
        custodian_jobs = [{'jb': vasp_job_type, 'params': vasp_job_settings}]
        # handler specification is expected as list of the form
        # [
        #   {'hdlr': handler1_import_path, 'params': {'handler1_params}},
        #   {'hdlr': handler1_import_path, 'params': {'handler1_params}},
        #   ...
        # ]
        connected_handlers = self.custodian_handlers.items()
        custodian_handlers = [
            {'hdlr': h, 'params': p} for (h, p) in connected_handlers
        ]
        # custodian settings are expected to be of type dict
        custodian_settings = self.custodian_settings
        # finally combine the re-arranged contents to build the input
        # dictionary resulting in the yaml-file of the expected format
        custodian_spec_contents = {
            'jobs': custodian_jobs,
            'handlers': custodian_handlers,
            'custodian_params': custodian_settings,
        }
        # generate custodian input file
        cstdn_spec_file_contents = yaml.dump(custodian_spec_contents,
                                             explicit_start=False,
                                             default_flow_style=False,
                                             allow_unicode=True)
        with open(path_to_file.absolute(), 'w') as cstdn_spec_file:
            cstdn_spec_file.write(cstdn_spec_file_contents)
