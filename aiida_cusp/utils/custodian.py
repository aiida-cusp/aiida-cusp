# -*- coding: utf-8 -*-


"""
Utility for translating plugin input parameters for Custodian and setting
up the input scripts for the Custodian executable.
"""


from aiida_cusp.utils.exceptions import CustodianSettingsError


class CustodianSettings(object):
    """
    Class to store Custodian settings and generate the required input files

    :param vasp_cmd:
    :type vasp_cmd:
    :param stdout:
    :type stdout:
    :param stderr:
    :type stderr:
    :param settings:
    :type settings:
    :param handlers:
    :type handlers:
    """

    # path used as import-path for the Custodian handler classes
    _CSTDN_HANDLER_IMPORT_PATH = 'custodian.vasp.handlers'

    def __init__(self, **kwargs):
        # check and set values for non-optional paramers
        self.check_non_optional_parameters(kwargs)
        # get other optional parameters
        self.cstdn_settings = kwargs.pop('settings', {})
        self.cstdn_handlers = kwargs.pop('handlers', {})

    def check_non_optional(self, kwargs):
        # check for all non-optional parameters
        try:
            self.vasp_cmd = kwargs.pop('vasp_cmd')
        except KeyError:
            raise CustodianSettingsError("No parameter")
        try:
            self.stdout_file = kwargs.pop('stdout')
        except KeyError:
            raise CustodianSettingsError("No parameter")
        try:
            self.stderr_file = kwargs.pop('stderr')
        except KeyError:
            raise CustodianSettingsError("No parameter")
