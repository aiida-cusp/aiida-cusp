# -*- coding: utf-8 -*-


"""
Datatype and methods to initialize and interact with VASP specific
CHGCAR output data
"""


from aiida_cusp.utils.single_archive_data import SingleArchiveData
from aiida_cusp.utils.defaults import VaspDefaults


class VaspChgcarData(SingleArchiveData):
    """
    AiiDA compatible node representing a VASP CHGCAR output data object
    as gzip-compressed node in the repository.

    Added as separate output node for easier access when used as calculation
    input for restarted VASP calculations.
    """
    pass
