# -*- coding: utf-8 -*-


"""
Datatype and methods to initialize and interact with VASP specific INCAR
input data
"""


from aiida.orm import Dict
from pymatgen.io.vasp.inputs import Incar

from aiida_cusp.utils.exceptions import IncarWrapperError


class VaspIncarData(Dict):
    """
    VaspIncarData(incar=None)

    AiiDA compatible node representing a VASP incar data object based on the
    :class:`~pymatgen.io.vasp.inputs.Incar` datatype.

    :param incar: input parameters used to construct the
        :class:`~pymatgen.io.vasp.inputs.Incar` object or a incar object
        itself (Note: may also be set to `None` to initialize an empty incar
        object and use the VASP default parameters)
    :type incar: dict or :class:`~pymatgen.io.vasp.inputs.Incar`
    """
    def __init__(self, *args, **kwargs):
        # if incar is set: assume initialization from user space. Cannot
        # use None here since it is a valid value for incar
        incar = kwargs.pop('incar', False)
        if not incar:
            super(VaspIncarData, self).__init__(*args, **kwargs)
        else:  # redirect to wrapper if incar is set
            incar = IncarWrapper(incar=incar)
            super(VaspIncarData, self).__init__(dict=incar.as_dict())

    def get_incar(self):
        """
        get_incar()

        Create and return a :class:`~pymatgen.io.vasp.inputs.Incar` instance
        initialized from the node's stored incar data contents.

        :return: a pymatgen Incar data instance
        :rtype: :class:`pymatgen.io.vasp.inputs.Incar`
        """
        return Incar.from_dict(self.get_dict())

    def write_file(self, filename):
        """
        write_file(filename)

        Write the stored incar data to VASP input file.

        Output of the contents to the file is redirected to the
        :meth:`pymatgen.io.vasp.inputs.Incar.write_file` method and the created
        output file will be formatted as VASP input file (INCAR)

        :param filename: destination for writing the output file
        :type filename: str
        :return: None
        """
        incar = self.get_incar()
        incar.write_file(filename)


class IncarWrapper(object):
    """
    Utility class for initializing :class:`pymatgen.io.vasp.inputs.Incar`
    data objects

    Accepts either a :class:`~pymatgen.io.vasp.inputs.Incar` instance or
    a dictionary containing valid VASP Incar parameters which will be passed
    through to the :class:`~pymatgen.io.vasp.inputs.Incar` constructor. Note:
    If `incar` is set to `None` and empty incar file will be initialized.

    :param incar: input parameters used to construct the
        :class:`~pymatgen.io.vasp.inputs.Incar` object or a incar object
        itself.
    :type incar: dict or :class:`~pymatgen.io.vasp.inputs.Incar`
    """

    def __new__(cls, incar=None):
        # check if already pymatgen Incar instance
        if isinstance(incar, Incar):
            return incar
        elif isinstance(incar, dict):  # initialize from user input
            incar_params_upper = cls.keys_to_upper_case(incar)
            incar_data = Incar(params=incar_params_upper)
        elif incar is None:
            incar_data = Incar(params=None)
        else:
            raise IncarWrapperError("Unknown type '{}' for incar parameters"
                                    .format(type(incar)))
        return incar_data

    @classmethod
    def keys_to_upper_case(cls, rawdict):
        """
        Transform all incar parameter keys to upper case

        :param rawdict: input dictionary containing incar parameter key
            value pairs with keys possibly of mixed case
        :type rawdict: dict
        """
        return {key.upper(): value for (key, value) in rawdict.items()}
