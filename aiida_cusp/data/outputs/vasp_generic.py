# -*- coding: utf-8 -*-


"""
Generic datatype used for all VASP output files for which no
specific output type is implemented.
"""


from aiida_cusp.utils.single_archive_data import SingleArchiveData


class VaspGenericData(SingleArchiveData):
    """
    AiiDA compatible node representing an arbitrary VASP output data
    object for which no own output datatype was implemented.
    """
    pass
