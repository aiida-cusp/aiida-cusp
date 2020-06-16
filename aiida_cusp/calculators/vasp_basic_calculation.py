# -*- coding: utf-8 -*-


"""
Calculator class performing regular VASP calculations
"""


import pathlib

from aiida.engine import CalcJob

from aiida_cusp.utils.defaults import VaspDefaults, PluginDefaults
from aiida_cusp.calculators import CalculationBase
from aiida_cusp.data import (VaspIncarData, VaspPoscarData, VaspKpointData,
                             VaspPotcarData)


# TODO: Replace plain exceptions with calculator specific exceptions


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
        # FIXME: Enable this once Regular parsers are implemented
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
        spec.input_namespace(
            'potcar',
            valid_type=VaspPotcarData,
            dynamic=True,
            required=False,
            help=("Pseudo-potentials for each element present in the input "
                  "structure (POSCAR) used for the VASP calculation")
        )
        spec.input(
            'poscar',
            valid_type=VaspPoscarData,
            required=False,
            help=("POSCAR parameters containing the calculation's input "
                  "structure data")
        )

    def create_inputs_for_regular_run(self, folder, calcinfo):
        """
        Write input files for a regular VASP calculation
        """
        self.verify_regular_inputs()
        self.write_incar(folder)
        self.write_poscar(folder)
        self.write_potcar(folder)
        self.write_kpoints(folder)
        # write custodian spec file (only writes if custodian.code is set)
        self.write_custodian_spec(folder)

    def create_inputs_for_restart_run(self, folder, calcinfo):
        """
        Copy and write input fils for a restarted VASP calculation
        """
        # verify and copy remote contents
        self.verify_restart_inputs()
        self.restart_copy_remote(folder, calcinfo)
        # finally write updated INCAR and KPOINTS to the sandbox folder if
        # defined as inputs to the restarted calculation
        # TODO: This could be easily extended to also write a new POSCAR
        #       and / or POTCAR but I do not see the point in doing this
        #       for a restarted calculation
        if self.inputs.get('incar', False):
            self.write_incar(folder)
        if self.inputs.get('kpoints', False):
            self.write_kpoints(folder)
        # write custodian spec file (only writes if custodian.code is set)
        self.write_custodian_spec(folder)

    def restart_files_exclude(self):
        """
        Extend the default list of excluded files defined by the parent class
        if neccessary.
        """
        exclude = super(VaspBasicCalculation, self).restart_files_exclude()
        # additionally excluded files if defined as inputs for the restarted
        # calculation
        if self.inputs.get('incar', False):
            exclude += [VaspDefaults.FNAMES['incar']]
        if self.inputs.get('kpoints', False):
            exclude += [VaspDefaults.FNAMES['kpoints']]
        # do not copy POSCAR if replaced with CONTCAR
        if self.inputs.restart.get('contcar_to_poscar'):
            exclude += [VaspDefaults.FNAMES['poscar']]
        return exclude

    def verify_regular_inputs(self):
        """
        Verify the inputs for a regular VASP calculation
        """
        # for a new calclation all input files are required
        missing_inputs = []
        if not self.inputs.get('incar', False):
            missing_inputs += ['incar']
        if not self.inputs.get('kpoints', False):
            missing_inputs += ['kpoints']
        if not self.inputs.get('poscar', False):
            missing_inputs += ['poscar']
        if not self.inputs.get('potcar', False):
            missing_inputs += ['potcar']
        if missing_inputs:
            raise Exception("cannot setup the calculation because the "
                            "following, non-optional inputs are missing: {}"
                            .format(", ".join(missing_inputs)))

    def verify_restart_inputs(self):
        """
        Verify the inputs for a restarted VASP calculation
        """
        forbidden_inputs = []
        if self.inputs.get('poscar', False):
            forbidden_inputs += ['poscar']
        if self.inputs.get('potcar', False):
            forbidden_inputs += ['potcar']
        if forbidden_inputs:
            raise Exception("the following defined inputs are not allowed "
                            "in a restarted calculation: {}"
                            .format(", ".join(forbidden_inputs)))

    def write_incar(self, folder):
        """
        Write INCAR file to calculation folder.
        """
        incar_fname = folder.get_abs_path(VaspDefaults.FNAMES['incar'])
        self.inputs.incar.write_file(incar_fname)

    def write_kpoints(self, folder):
        """
        Write KPOINTS file to calculation folder.
        """
        kpoints_fname = folder.get_abs_path(VaspDefaults.FNAMES['kpoints'])
        self.inputs.kpoints.write_file(kpoints_fname)

    def write_poscar(self, folder):
        """
        Write POSCAR file to calculation folder.
        """
        poscar_fname = folder.get_abs_path(VaspDefaults.FNAMES['poscar'])
        self.inputs.poscar.write_file(poscar_fname)

    def write_potcar(self, folder):
        """
        Write POTCAR file to calculation folder.
        """
        poscar = self.inputs.poscar
        potcar = self.inputs.potcar
        complete_potcar = VaspPotcarData.potcar_from_linklist(poscar,
                                                              potcar)
        potcar_fname = folder.get_abs_path(VaspDefaults.FNAMES['potcar'])
        complete_potcar.write_file(potcar_fname)

    def write_custodian_spec(self, folder):
        """
        Write the custodian input file to the calculation folder if a
        custodian code is defined.
        """
        cstdn_code = self.inputs.custodian.get('code', False)
        if cstdn_code:
            custodian_settings = self.setup_custodian_settings(is_neb=False)
            spec_fname = folder.get_abs_path(PluginDefaults.CSTDN_SPEC_FNAME)
            custodian_settings.write_custodian_spec(pathlib.Path(spec_fname))
