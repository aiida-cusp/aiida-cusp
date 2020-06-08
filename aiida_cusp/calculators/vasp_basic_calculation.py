# -*- coding: utf-8 -*-
"""
Calculator class performing regular VASP calculations
"""


from aiida.engine import CalcJob

from aiida_cusp.utils.defaults import VaspDefaults
from aiida_cusp.calculators import CalculationBase
from aiida_cusp.data import (VaspIncarData, VaspPoscarData, VaspKpointData,
                             VaspPotcarData)


class VaspBasicCalculation(CalculationBase):
    """
    Calculator class for basic VASP calculations.

    This calculator implements the required features for setting up and
    running basic VASP calculations (i.e. all calculations that are
    **not** of the kind NEB calculation, refer to the VaspNebCalculation
    class for this kind of calculation) through the AiiDA framework.
    """

    @classmethod
    def define(cls, spec):
        super(VaspBasicCalculation, cls).define(spec)
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

#    def prepare_for_submission(self, folder):
#        """
#        Prepare the calculation and write the require inputs to the
#        calculation folder.
#        """
#        pass

    def create_inputs_for_regular_run(self, folder):
        """
        Write input files for a regular VASP calculation
        """
        self.write_incar(folder)
        self.write_poscar(folder)
        self.write_potcar(folder)
        self.write_kpoints(folder)

    def write_incar(self, folder):
        """
        Write INCAR file to calculation folder.
        """
        if 'incar' not in self.inputs:
            raise
        else:
            incar_fname = folder.get_abs_path(VaspDefaults.FNAMES['incar'])
            self.inputs.incar.write_file(incar_fname)

    def write_kpoints(self, folder):
        """
        Write KPOINTS file to calculation folder.
        """
        if 'kpoints' not in self.inputs:
            raise
        else:
            kpoints_fname = folder.get_abs_path(VaspDefaults.FNAMES['kpoints'])
            self.inputs.kpoints.write_file(kpoints_fname)

    def write_poscar(self, folder):
        """
        Write POSCAR file to calculation folder.
        """
        if 'poscar' not in self.inputs:
            raise
        else:
            poscar_fname = folder.get_abs_path(VaspDefaults.FNAMES['poscar'])
            self.inputs.poscar.write_file(poscar_fname)

    def write_potcar(self, folder):
        """
        Write POTCAR file to calculation folder.
        """
        if 'potcar' not in self.inputs:
            raise
        else:
            poscar = self.inputs.poscar
            potcar = self.inputs.potcar
            complete_potcar = VaspPotcarData.potcar_from_linklist(poscar,
                                                                  potcar)
            potcar_fname = folder.get_abs_path(VaspDefaults.FNAMES['potcar'])
            complete_potcar.write_file(potcar_fname)
