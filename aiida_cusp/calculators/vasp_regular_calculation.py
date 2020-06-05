# -*- coding: utf-8 -*-
"""
Calculator class performing regular VASP calculations
"""


from aiida.engine import CalcJob

from aiida_cusp.calculators import VaspBaseCalculation
from aiida_cusp.data import (VaspIncarData, VaspPoscarData, VaspKpointData,
                             VaspPotcarData)


class VaspCalculation(VaspBaseCalculation):
    """
    Calculator class for regular VASP calculations.

    This calculator implements the required features for setting up and
    running a regular VASP calculations (i.e. all calculations that are
    **not** if the kind NEB calculation, refer to the VaspNebCalculation
    class for this kind of calculation) through the AiiDA framework.
    """

    @classmethod
    def define(cls, spec):
        super(VaspCalculation, cls).define(spec)
        # define parser to be used with the calculation
        # FIXME: Enable this once parsers are implemented
        # spec.input('metadata.options.parser_name',
        #            valid_type=str,
        #            default=None,
        #            help=("Parser used to parse the results of a finished "
        #                  "calculation")
        # )
        # define the available inputs required to run VASP calculations (all
        # inputs marked as optional so that a restart can be performed solely
        # based on the outputs stored in a remote folder location)
        spec.input(
            'incar',
            valid_type=VaspIncarData,
            required=False,
            help=("INCAR parameters for a VASP calculation")
        )
        spec.input(
            'poscar',
            valid_type=VaspPoscarData,
            required=False,
            help=("POSCAR parameters containing the calculation's "
                  "input structure data")
        )
        spec.input(
            'kpoints',
            valid_type=VaspKpointData,
            required=False,
            help=("KPOINTS parameters for a VASP calculation")
        )
        spec.input_namespace(
            'potcar',
            valid_type=VaspPotcarData,
            dynamic=True,
            required=False,
            help=("Pseudo-potentials for each element "
                  "present in the input structure (POSCAR) "
                  "used for the VASP calculation")
        )

    def prepare_for_submission(self, folder):
        """
        Prepare the calculation and write the require inputs to the
        calculation folder.
        """
        pass
