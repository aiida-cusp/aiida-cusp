# -*- coding: utf-8 -*-


"""
Datatype and methods to initialize and interact with VASP specific
OUTCAR output data
"""


from pymatgen.io.vasp.outputs import Outcar

from aiida_cusp.utils.single_archive_data import SingleArchiveData


class VaspOutcarData(SingleArchiveData):
    """
    AiiDA compatible node representing a VASP OUTCAR output data object
    as gzip-compressed node in the repository.
    """

    def get_outcar(self):
        """
        Return a :class:`pymatgen.io.vasp.outputs.Outcar` instance
        initialized from the OUTCAR data stored by the node

        :returns: Outcar instance initialized from the node's stored
            OUTCAR data
        :rtype: :class:`~pymatgen.io.vasp.outputs.Outcar`
        """
        parsed_outcar = Outcar(self.filepath)
        return parsed_outcar
