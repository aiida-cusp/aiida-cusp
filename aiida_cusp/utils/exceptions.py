# -*- coding: utf-8 -*-


"""
Custom exceptions
"""


class PotcarParserError(Exception):
    """Exception raised by the PotcarParser class."""
    pass


class PotcarPathError(Exception):
    """Exception raised by the PotcarPathParser class."""
    pass


class IncarWrapperError(Exception):
    """Exception raised by the Incar wrapper class."""
    pass


class KpointWrapperError(Exception):
    """Exception raised by the KpointWrapper class."""
    pass


class PoscarWrapperError(Exception):
    """Exception raised by the PoscarWrapper class."""
    pass


class VaspPotcarFileError(Exception):
    """Exception raised by the VaspPotcarFile class."""
    pass


class VaspPotcarDataError(Exception):
    """Exception raised by the VaspPotcarData class."""
    pass


class MultiplePotcarError(Exception):
    """Exception raised if POTCAR file is already stored in the database."""
    pass
