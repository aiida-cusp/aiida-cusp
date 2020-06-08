# -*- coding: utf-8 -*-
"""
Calculator class performing VASP NEB calculations
"""


from aiida.engine import CalcJob
from aiida_cusp.calculators import CalculationBase
from aiida_cusp.data import (VaspIncarData, VaspPoscarData, VaspKpointData,
                             VaspPotcarData)


class VaspNebCalculation(CalculationBase):
    """
    Calculator class for VASP NEB calculations.

    This calculator implements the required features for setting up and
    running a VASP NEB calculation through the AiiDA framewirk. Contrary
    to the calculator for regular runs (refer to the VaspCalculation class)
    instead of a single structure this calculator class supports the input
    of multiple POSCAR instances defining the NEB path.
    """

    @classmethod
    def define(cls, spec):
        super(VaspNebCalculation, cls).define(spec)
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
            'kpoints',
            valid_type=VaspKpointData,
            required=False,
            help=("KPOINTS parameters for a VASP calculation")
        )
        # use a dynamical namespace for the poscar inputs to allow input
        # of multiple structures comprising the NEB path
        spec.input_namespace(
            'neb_path',
            valid_type=VaspPoscarData,
            dynamic=True,
            required=False,
            help=("Series of multiple VASP POSCAR objects "
                  "defining a NEB path for NEB calculations ")
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

#    def prepare_for_submission(self, folder):
#        """
#        Prepare the calculation and write the required inputs to the
#        calculation folder.
#        """
#        pass
