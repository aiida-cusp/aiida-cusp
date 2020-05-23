# -*- coding: utf-8 -*-


"""
Potcar
"""


from aiida.orm import SinglefileData, Dict


# TODO: Figure out if there is sane way provided by the AiiDA-Framework that
#       can be used to extend the datatype constructure with additional
#       arguments (I know there exist set_value() methods but are those
#       available for all datatypes?)

class VaspPotcarFile(SinglefileData):
    """
    Datatype representing an actual POTCAR file objects stored to
    the AiiDA database.
    """
    pass


class VaspPotcarData(Dict):
    """
    Pseudopotential input datatype for VASP calculations.

    Contrary to the related VaspPotcarFile class this object does **not**
    contain any proprietary potential information and only stores the
    potential's hash value and the unique potential identifiers (name,
    functional and version)
    """
    pass
