# -*- coding: utf-8 -*-


"""
Utility for translating plugin input parameters for Custodian and setting
up the input scripts for the Custodian executable.
"""


import yaml

from aiida_cusp.utils.exceptions import CustodianSettingsError
from aiida_cusp.utils.defaults import CustodianDefaults


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
        self.custodian_jobs = jobs
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
        valid_settings = CustodianDefaults.MODIFIABLE_SETTINGS
        for parameter in list(settings.keys()):
            # fail if the parameter is not a valid custodian setting at all
            if parameter not in cstdn_settings.keys():
                valid = ", ".join(valid_settings)
                raise CustodianSettingsError("got an invalid custodian "
                                             "setting '{}' (valid settings: "
                                             "{})".format(parameter, valid))
            # fail if the parameter is valid setting but not modifiable
            if parameter not in CustodianDefaults.MODIFIABLE_SETTINGS:
                raise CustodianSettingsError("cannot set value for protected "
                                             "custodian setting '{}'"
                                             .format(parameter))
            # otherwise: update the defaults from the user input
            cstdn_settings[parameter] = settings.pop(parameter)
        return cstdn_settings

    def setup_custodian_handlers(self, handlers):
        """
        Define error handlers used by custodian.

        Accepts a list of handler names which will initialize the handlers
        with their corresponding default values. If `handlers` is given as
        dictionary keys are assumed to be of type handler name and the
        corresponding item to be of type `dict` containing the non-default
        parameters for the corresponding handler.

        :param handlers: list of handler names or a dictionary of handlers
            and their corresponding non-default parameters
        :type handlers: `dict` or `list`
        :returns: dictionary of handler module paths and the corresponding
            handler setings for all handlers defined in the input `handlers`
        :rtype: `dict`
        :raises CustodianSettingsError: if input parameter handlers is not
            of the correct type (i.e. list, tuple or dict)
        :raises CustodianSettingsError: if invalid parameter settings are
            found for a handler
        :raises CustodianSettingsError: if an invalid handler name is found
        """
        # normalize input to a dictionary of the form {handler_name: params}
        # where params = {} results in default parameters being used
        if isinstance(handlers, (list, tuple)):
            handlers_dict = {hdlr_name: {} for hdlr_name in handlers}
        elif isinstance(handlers, dict):
            handlers_dict = dict(handlers)
        else:
            raise CustodianSettingsError("Invalid input type for 'handler', "
                                         "expected '{}' or '{}' but got "
                                         "'{}'".format(type(list), type(dict),
                                                       type(handlers)))
        handlers_and_settings = dict(CustodianDefaults.ERROR_HANDLER_SETTINGS)
        handler_import_and_params = {}
        for handler_name, handler_params in handlers_and_settings.items():
            try:
                user_handler_params = handlers_dict.pop(handler_name)
                for parameter, value in user_handler_params.items():
                    if parameter in handler_params.keys():
                        handler_params[parameter] = value
                    else:
                        valid = ", ".join(list(handler_params.keys()))
                        error_msg = ("Invalid parameter '{}' for handler "
                                     "'{}' (Valid parameters: {})"
                                     .format(parameter, handler_name, valid))
                        raise CustodianSettingsError(error_msg)
                # if found add the handler import path with it's corresponding
                # parameters to the input handler dictionary
                import_path = ".".join([CustodianDefaults.HANDLER_IMPORT_PATH,
                                        handler_name])
                handler_import_and_params[import_path] = handler_params

            except KeyError:  # proceed with next handler if not found
                continue
        # raise if any handlers are remaining
        self.validate_handlers(handlers_dict)
        return handler_import_and_params

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

        if len(self.custodian_jobs) == 0:
            custodian_jobs = [{"jb": vasp_job_type,
                               "params": vasp_job_settings}]
        else:
            for name, job in self.custodian_jobs.items():
                job["vasp_cmd"] = self.vasp_cmd
                job["output_file"] = self.stdout
                job["stderr_file"] = self.stderr
            custodian_jobs = [dict(jb=vasp_job_type, params=job)
                              for name, job in self.custodian_jobs.items()]

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
