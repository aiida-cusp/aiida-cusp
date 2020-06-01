# -*- coding: utf-8 -*-
"""
Datatype and methods to initialize and interact with VASP specific POSCAR
input data
"""


from aiida.orm import Dict, StructureData
from pymatgen.io.vasp.inputs import Poscar
from pymatgen.core import Structure


# FIXME: Only the basic inputs for the pymatgen Poscar class are made available
#        in the Wrapper class (i.e. constraints, velocities and the setup of
#        initial velocities from a Maxwell-Boltzmann distribution using a
#        given temperature. If neccessary other inputs like the predictor-
#        corrector stuff may also be made available.


class PoscarWrapperError(Exception):
    """Exception raised by the PoscarWrapper class."""
    pass


class VaspPoscarData(Dict):
    def __init__(self, *args, **kwargs):
        # if structure is set: assume initialization from user space
        structure = kwargs.pop('structure', None)
        constraints = kwargs.pop('constraints', None)
        velocities = kwargs.pop('velocities', None)
        temperature = kwargs.pop('temperature', None)
        if structure is None:
            super(VaspPoscarData, self).__init__(*args, **kwargs)
        else:  # redirect to wrapper if structure is set
            poscar = PoscarWrapper(structure=structure,
                                   constraints=constraints,
                                   velocities=velocities,
                                   temperature=temperature)
            super(VaspPoscarData, self).__init__(dict=poscar.as_dict())


class PoscarWrapper(object):
    """
    Utility class for initializing :class:`pymatgen.io.vasp.inputs.Poscar`
    data objects.

    Requires at least a structure object to initialize the VASP Poscar input
    file and allows to set additional parameters like initial velocities or
    predictor-corrector coordinates. If the input structure is of type
    :class:`~pymatgen.io.vasp.inputs.Poscar` all other input parameters will
    be ignored.

    :param structure: Structure data used to initialize the VASP Poscar input
        file.
    :type structure: :class:`~aiida.orm.StructureData`, :class:`~pymatgen.\
        core.Structure` or :class:`~pymatgen.io.vasp.inputs.Poscar`
    :param constraints: Nx3 list containing boolean values defining
        constraints on the coordinates of all atoms present in the structure
        with values set to `False` indicating fixed coordinates.
    :type constraints: `list`
    :type true_names: `bool`
    :param velocities: Nx3 list of floats defining the velocities of the atoms
        contained in the structure
    :type velocities: `list`
    :param temperature: initialize atom velocities from a Maxwell-Boltzmann
        distribution at the given temperature
    :type temperature: `float`
    :return: a pymatgen Poscar instance
    :rtype: :class:`~pymatgen.io.vasp.inputs.Poscar`
    """
    def __new__(cls, structure=None, constraints=None, velocities=None,
                temperature=None):
        # check if structure is already Poscar and return immediately
        if isinstance(structure, Poscar):
            return structure
        else:  # otherwise initialize new Poscar object from user inputs
            cls.input_structure = structure
            cls.input_constraints = constraints
            cls.input_velocities = velocities
            cls.input_temperature = temperature
            return cls.validate_and_initialize()

    @classmethod
    def validate_and_initialize(cls):
        """
        Initialize new Poscar instance from given user inputs
        """
        # complete the parameters list accepted by the pymatgen Poscar
        # object (Checking for correct types is delegated to the pymatgen
        # Poscar constructor!)
        valid_poscar_kwargs = {
            'structure': cls.structure_from_input(),
            'comment': None,  # do not add any comments
            'selective_dynamics': cls.input_constraints,
            'true_names': True,  # always assume true species names
            'velocities': cls.input_velocities,
            'predictor_corrector': None,  # leave predictor-corrector unset
            'predictor_corrector_preamble': None,
            'sort_structure': True,  # always sort structure
        }
        # initilize the Poscar istance
        poscar_object = Poscar(**valid_poscar_kwargs)
        # if temperature is given initialize the atomic velocities accordingly
        if cls.input_temperature is not None:
            poscar_object.set_temperature(cls.input_temperature)
        return poscar_object

    @classmethod
    def structure_from_input(cls):
        """
        Obtain a :class:`~pymatgen.core.structure.Structure` instance from the
        given input structure
        """
        if isinstance(cls.input_structure, Structure):
            return cls.input_structure
        elif isinstance(cls.input_structure, StructureData):
            return cls.input_structure.get_pymatgen_structure()
        else:
            raise PoscarWrapperError("Unsupported structure type '{}'"
                                     .format(type(cls.input_structure)))
