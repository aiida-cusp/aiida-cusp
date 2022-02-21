# -*- coding: utf-8 -*-


"""
Datatype and methods to initialize and interact with VASP specific KPOINTS
input data
"""


import warnings

from aiida.orm import StructureData, Dict
from pymatgen.core import Structure
from pymatgen.io.vasp.inputs import Kpoints, Poscar

from aiida_cusp.utils.exceptions import KpointWrapperError


class VaspKpointData(Dict):
    """
    VaspKpointData(kpoints=None, structure=None)

    AiiDA compatible node representing a VASP k-point grid based on the
    :class:`~pymatgen.io.vasp.inputs.Kpoints` datatype.

    :param kpoints: k-point grid definitions either given as a dictionary to
        call the internal initialization modes or directly as a pymatgen
        :class:`pymatgen.io.vasp.inputs.Kpoints` object.
    :type kpoints: :class:`pymatgen.io.vasp.inputs.Kpoints` or dict
    :param structure: calculation input structure (optional, only required if
        k-points are initialized from a density)
    :type structure: :class:`~pymatgen.core.structure.Structure`,
        :class:`~pymatgen.io.vasp.inputs.Poscar` or
        :class:`~aiida.orm.StructureData`
    """
    def __init__(self, *args, **kwargs):
        # if kpoints are set: assume initialization from user space
        kpoints = kwargs.pop('kpoints', None)
        structure = kwargs.pop('structure', None)
        if kpoints is None:
            super(VaspKpointData, self).__init__(*args, **kwargs)
        else:  # redirect to wrapper
            kpoints = KpointWrapper(kpoints=kpoints, structure=structure)
            super(VaspKpointData, self).__init__(dict=kpoints.as_dict())

    def get_kpoints(self):
        """
        Create and return a :class:`pymatgen.io.vasp.inputs.Kpoints` instance
        initialized from the node's stored k-point data contents.

        :return: a pymatgen Kpoints instance
        :rtype: :class:`pymatgen.io.vasp.inputs.Kpoints`
        """
        return Kpoints.from_dict(self.get_dict())

    def write_file(self, filename):
        """
        Write the stored k-point grid data to VASP input file.

        File creation is redirected to the
        :meth:`pymatgen.io.vasp.inputs.Kpoints.write_file` method and the
        created output file will be formatted as VASP input file (KPOINTS)

        :param filename: destination for the output file including the
            desired output filename
        :type filename: str
        :return: None
        """
        kpoints = self.get_kpoints()
        kpoints.write_file(filename)

    def get_description(self):
        """
        Return a descriptive string of the stored k-point contents.
        """
        kpoint_dict = self.get_dict()
        grid_style = kpoint_dict['generation_style']
        if (grid_style == 'Automatic'):
            # kpoint format Automatic: [[int(subdivisions)]]
            subdiv = kpoint_dict['kpoints'][0][0]
            return u'Automatic (Subdivisions: {})'.format(subdiv)
        elif (grid_style == 'Line_mode'):
            return u'Line-mode'
        else:  # Monkhorst or Gamma grid
            kpt_grid = kpoint_dict['kpoints'][0]
            kpt_grid_str = 'x'.join(map(str, kpt_grid))
            return u'{} ({})'.format(grid_style, kpt_grid_str)


class KpointWrapper(object):
    """
    KpointWrapper(kpoints=None, structure=None)

    Utility class for initializing :class:`pymatgen.io.vasp.inputs.Kpoints`
    data objects.

    Provides a wrapper for the different initialization modes provided by the
    pymatgen Kpoints object. Different modes can be access by setting the
    'mode' keyword in the kpoints dictionary and by defining the datatypes
    passed by the 'kpoints' keyword (i.e. a list of kpoints will initialize an
    explicit kpoint grid while passing a float to the constructor will call
    a density based initialization mode)

    Example:

    .. code-block:: python

       >>> kpoint_param = {'mode': 'auto', 'kpoints': 100}
       >>> kpts = KpointWrapper(kpoints=kpoint_params)
       >>> print(kpts)
       Automatic Mesh
       0
       Auto
         40

    :param kpoints: input parameters that are used to construct the
        :class:`~pymatgen.io.vasp.inputs.Kpoints` object or a kpoints
        object itself
    :type kpoints: dict or :class:`~pymatgen.io.vasp.inputs.Kpoints`
    :param structure: optional input structure for the calculation required
        for density based kpoint initialization
    :type structure: :class:`~pymatgen.core.structure.Structure`,
        :class:`~pymatgen.io.vasp.inputs.Poscar` or
        :class:`~aiida.orm.StructureData`
    """

    _VALID_INIT_MODES = ["auto", "monkhorst", "gamma", "line"]

    def __new__(cls, kpoints=None, structure=None):
        # check if kpoints object and return immediately
        if isinstance(kpoints, Kpoints):
            return kpoints
        else:  # otherwise initialize from user input
            cls.input_kpoints = kpoints
            cls.input_structure = structure
            return cls.validate_and_initialize()

    @classmethod
    def validate_and_initialize(cls):
        """
        Initialize a new Kpoint object from user inputs
        """
        cls.complete_parameter_list()
        try:
            initialization_function_name = cls.build_init_mode()
            init_kpoints = getattr(cls, initialization_function_name)
        except AttributeError:
            raise KpointWrapperError("Unsupported initialization mode '{}' "
                                     "for given parameters '{}'"
                                     .format(initialization_function_name,
                                             cls.kpoint_params))
        kpoint_object = init_kpoints()
        return kpoint_object

    @classmethod
    def complete_parameter_list(cls):
        """
        Complete the parameter list and perform minimal initial checking
        """
        # only check for non-optional parameters common to all initialization
        # modes (delegate more specialized checks to the actual initialization
        # routines)
        if 'mode' not in cls.input_kpoints:
            raise KpointWrapperError("Missing non-optional parameter 'mode'")
        if 'kpoints' not in cls.input_kpoints:
            raise KpointWrapperError("Missing non-optional parameter "
                                     "'kpoints'")
        # check if set mode has one of the accepted values
        if cls.input_kpoints['mode'] not in cls._VALID_INIT_MODES:
            raise KpointWrapperError("Unknown value '{}' set for parameter "
                                     "'mode' (Allowed values: '{}'"
                                     .format(cls.input_kpoints['mode'],
                                             cls._VALID_INIT_MODES))
        # complement user defined parameter to complete the parameter list
        cls.kpoint_params = {
            'mode': cls.input_kpoints.get('mode'),
            'kpoints': cls.input_kpoints.get('kpoints'),
            'shift': cls.input_kpoints.get('shift', None),
            'sympath': cls.input_kpoints.get('sympath', None),
        }

    @classmethod
    def build_init_mode(cls):
        """
        Figure out the initialization mode using the defined mode and the
        specified type of kpoints
        """
        init_mode_identifiers = [
            str(cls.kpoint_params['mode']),  # defined mode
            str(type(cls.kpoint_params['kpoints']).__name__),  # variable type
        ]
        return "_".join(init_mode_identifiers)

    @classmethod
    def structure_from_input(cls):
        """
        Obtain :class:`~pymatgen.core.structure.Structure` object from the
        given input structure
        """
        if isinstance(cls.input_structure, Structure):
            return cls.input_structure
        elif isinstance(cls.input_structure, StructureData):
            return cls.input_structure.get_pymatgen_structure()
        elif isinstance(cls.input_structure, Poscar):
            return cls.input_structure.structure
        else:
            raise KpointWrapperError("Unsupported structure type '{}'"
                                     .format(type(cls.input_structure)))

    @classmethod
    def auto_int(cls):
        """
        Initialize automatic kpoint grid following the VASP automatic mode

        Example::

           Automatic Mesh
           0
           Auto
             40
        """
        # inform user that some set parameters will be ignored
        if cls.kpoint_params['shift'] is not None:
            warnings.warn("Automatic kpoint mode: Ignoring defined shift")
        if cls.kpoint_params['sympath'] is not None:
            warnings.warn("Automatic kpoint mode: Ignoring defined high "
                          "symmetry path object")
        kpoints = cls.kpoint_params['kpoints']
        # pymatgen returns default shift as tuple (0, 0, 0) thus we need
        # to transform the shift to a list of floats before returning
        kpts = Kpoints.automatic(kpoints)
        kpts.kpts_shift = list(map(float, kpts.kpts_shift))
        return kpts

    @classmethod
    def gamma_list(cls):
        """
        Initialize gamma grid from a list explicitly defining the number
        of kpoint subdivisions along the crystal axis

        Example::

           Automatic Kpoint Scheme
           0
           Gamma
           5 5 5
        """
        if cls.kpoint_params['sympath'] is not None:
            warnings.warn("Explicit gamma grid mode: Ignoring defined high "
                          "symmetry path object")
        kpoints = cls.kpoint_params['kpoints']
        if len(kpoints) != 3:
            raise KpointWrapperError("Expected list of length 3 for explict "
                                     "k-point grid input")
        shift = cls.kpoint_params['shift'] or [.0, .0, .0]
        if len(shift) != 3:
            raise KpointWrapperError("Expected list of length 3 for k-point "
                                     "grid shift")
        return Kpoints.gamma_automatic(kpts=kpoints, shift=shift)

    @classmethod
    def monkhorst_list(cls):
        """
        Initialize Monkhorst grid from a list explicitly defining the number
        of kpoint subdivisions along the crystal axis

        Example:

        .. code-block:: python

           Automatic Kpoint Scheme
           0
           Monkhorst
           4 4 4
        """
        if cls.kpoint_params['sympath'] is not None:
            warnings.warn("Explicit monkhorst grid mode: Ignoring defined "
                          "high symmetry path object")
        kpoints = cls.kpoint_params['kpoints']
        if len(kpoints) != 3:
            raise KpointWrapperError("Expected list of length 3 for explict "
                                     "k-point grid input")
        shift = cls.kpoint_params['shift'] or [.0, .0, .0]
        if len(shift) != 3:
            raise KpointWrapperError("Expected list of length 3 for k-point "
                                     "grid shift")
        return Kpoints.monkhorst_automatic(kpts=kpoints, shift=shift)

    @classmethod
    def gamma_float(cls):
        """
        Initialize gamma grid using a given kpoint density. Enforces the
        usage of gamma grids.

        Example::

           Automatic Kpoint Scheme
           0
           Gamma
           5 5 5
        """
        # check if required input structure was given
        if cls.input_structure is None:
            raise KpointWrapperError("Missing non-optional kpoint density "
                                     "parameter 'structure'")
        if cls.kpoint_params['sympath'] is not None:
            warnings.warn("Gamma density grid mode: Ignoring defined "
                          "high symmetry path object")
        structure = cls.structure_from_input()
        kpoints = cls.kpoint_params['kpoints']
        return Kpoints.automatic_density(structure, kpoints, force_gamma=True)

    @classmethod
    def monkhorst_float(cls):
        """
        Initialize kpoint grid using a given kpoint density. If the number
        of subdivisions is even a Monkhorst grid is constructured whereas
        gamma grids are used for odd kpoint subdivisions

        Example::

           Automatic Kpoint Scheme
           0
           Monkhorst
           4 4 4
        """
        # check if required input structure was given
        if cls.input_structure is None:
            raise KpointWrapperError("Missing non-optional kpoint density "
                                     "parameter 'structure'")
        if cls.kpoint_params['sympath'] is not None:
            warnings.warn("Monkhorst density grid mode: Ignoring defined "
                          "high symmetry path object")
        structure = cls.structure_from_input()
        kpoints = cls.kpoint_params['kpoints']
        return Kpoints.automatic_density(structure, kpoints, force_gamma=False)

    @classmethod
    def line_int(cls):
        """
        Initialize list of kpoints along a high-symmetry path through the
        Brillouin zone. Uses a path defined by the pymatgen HighSymmPath class
        with a defined number of kpoint subdivisions between the path nodes.

        Example::

           Line_mode KPOINTS file
           100
           Line_mode
           Reciprocal
           0.0 0.0 0.0 ! Gamma
           0.0 0.5 0.0 ! X

           0.0 0.5 0.0 ! X

           ...

           0.0 0.5 0.0 ! X

           0.5 0.5 0.0 ! M
           0.5 0.5 0.5 ! R
        """
        if cls.kpoint_params['shift'] is not None:
            warnings.warn("Line kpoint mode: Ignoring defined shift")
        if cls.kpoint_params['sympath'] is None:
            raise KpointWrapperError("Missing non-optional kpoint line mode "
                                     "parameter 'sympath'")
        divisions = cls.kpoint_params['kpoints']
        sympath = cls.kpoint_params['sympath']
        # pymatgen returns default shift as tuple (0, 0, 0) thus we need
        # to transform the shift to a list of floats before returning
        kpts = Kpoints.automatic_linemode(divisions, sympath)
        kpts.kpts_shift = list(map(float, kpts.kpts_shift))
        return kpts
