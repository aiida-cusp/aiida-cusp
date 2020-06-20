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
    pass
