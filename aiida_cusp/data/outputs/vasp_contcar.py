# -*- coding: utf-8 -*-


"""
Datatype and methods to initialize and interact with VASP specific
CONTCAR output data
"""


from aiida_cusp.data.inputs.vasp_poscar import VaspPoscarData


class VaspContcarData(VaspPoscarData):
    """
    AiiDA compatible node representing a VASP CONTCAR output data object

    Added as separate output node for easier access when used as calculation
    input for restarted VASP calculations.
    """

    def get_contcar(self):
        """
        Create and return a :class:`pymatgen.io.vasp.inputs.Poscar` instance
        initialized from the node's stored output structure data content.

        :return: a pymatgen Poscar instance
        :rtype: :class:`pymatgen.io.vasp.inputs.Poscar`
        """
        # be consistent and simply relabel the method, pretty sure
        # VaspContcarData.get_poscar() gets annoying quickly :)
        return super(VaspContcarData, self).get_poscar()
