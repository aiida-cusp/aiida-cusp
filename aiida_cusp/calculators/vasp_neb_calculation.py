# -*- coding: utf-8 -*-


"""
Calculator class performing VASP NEB calculations
"""


import re
import pathlib

from aiida.engine import CalcJob
from aiida_cusp.calculators import CalculationBase
from aiida_cusp.utils.defaults import VaspDefaults, PluginDefaults
from aiida_cusp.data import (VaspIncarData, VaspPoscarData, VaspKpointData,
                             VaspPotcarData)


# TODO: Replace plain exceptions with calculator specific exceptions


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
        # FIXME: Enable this once NEB parsers are implemented
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
        # use a dynamical namespace for the poscar inputs to allow input
        # of multiple structures comprising the NEB path
        spec.input_namespace(
            'neb_path',
            valid_type=VaspPoscarData,
            dynamic=True,
            required=False,
            help=("Series of multiple VASP POSCAR objects defining a NEB "
                  "path for NEB calculations ")
        )

    def create_inputs_for_regular_run(self, folder, calcinfo):
        """
        Write NEB input files for a regular calculation
        """
        self.verify_regular_neb_inputs()
        self.write_incar(folder)
        self.write_kpoints(folder)
        self.write_neb_path(folder)
        self.write_potcar(folder)
        # write custodian spec file (only writes if custodian.code is set)
        self.write_custodian_spec(folder)

    def create_inputs_for_restart_run(self, folder, calcinfo):
        """
        Copy and write NEB input files for restarted caculation
        """
        # verify and copy remote contents
        self.verify_restart_neb_inputs()
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
        exclude = super(VaspNebCalculation, self).restart_files_exclude()
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

    def verify_regular_neb_inputs(self):
        """
        Verify the inputs for a regular VASP NEB calculation
        """
        # check that non-optional inputs are present
        missing_inputs = []
        if not self.inputs.get('incar', False):
            missing_inputs += ['incar']
        if not self.inputs.get('kpoints', False):
            missing_inputs += ['kpoints']
        if not self.inputs.get('neb_path', False):
            missing_inputs += ['neb_path']
        if not self.inputs.get('potcar', False):
            missing_inputs += ['potcar']
        if missing_inputs:
            raise Exception("cannot setup the calculation because the "
                            "following, non-optional NEB inputs are missing: "
                            "{}".format(", ".join(missing_inputs)))
        # check neb path identifiers are of correct type
        neb_path = self.inputs.get('neb_path')
        for identifier in neb_path.keys():
            expected_identifier_format = PluginDefaults.NEB_NODE_REGEX
            match = expected_identifier_format.match(identifier)
            if match is None:
                prefix = PluginDefaults.NEB_NODE_PREFIX
                raise Exception("Ill NEB path node identifier key format for "
                                "key '{}' (Expected key format "
                                "'{}[0-9][0-9]')".format(identifier, prefix))

    def verify_restart_neb_inputs(self):
        """
        Verify the inputs for a restarted VASP calculation
        """
        forbidden_inputs = []
        if self.inputs.get('neb_path', False):
            forbidden_inputs += ['neb_path']
        if self.inputs.get('potcar', False):
            forbidden_inputs += ['potcar']
        if forbidden_inputs:
            raise Exception("the following defined inputs are not allowed "
                            "in a restarted NEB calculation: {}"
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

    def write_potcar(self, folder):
        """
        Write POTCAR file to calculation folder.
        """
        # arbitrarily use the first node to build the POTCAR file
        first_node_id = "{}00".format(PluginDefaults.NEB_NODE_PREFIX)
        first_node = self.inputs.neb_path.get(first_node_id)
        potcar = self.inputs.potcar
        complete_potcar = VaspPotcarData.potcar_from_linklist(first_node,
                                                              potcar)
        potcar_fname = folder.get_abs_path(VaspDefaults.FNAMES['potcar'])
        complete_potcar.write_file(potcar_fname)

    def write_neb_path(self, folder):
        """
        Write sequence of POSCAR files to expected NEB subfolders
        """
        topfolder = pathlib.Path(folder.get_abs_path('.'))
        poscar_fname = folder.get_abs_path(VaspDefaults.FNAMES['poscar'])
        prefix = PluginDefaults.NEB_NODE_PREFIX
        for identifier, poscar in self.inputs.get('neb_path').items():
            # subfolder for current NEB path node (node_00 --> subfolder 00)
            subfolder_name = re.sub(prefix, '', identifier)
            subfolder = topfolder / subfolder_name
            if not subfolder.exists():
                subfolder.mkdir(parents=False)  # parent folder should be there
            poscar_fname = str(subfolder / VaspDefaults.FNAMES['poscar'])
            poscar.write_file(poscar_fname)

    def write_custodian_spec(self, folder):
        """
        Write the custodian input file to the calculation folder if a
        custodian code is defined.
        """
        cstdn_code = self.inputs.custodian.get('code', False)
        if cstdn_code:
            custodian_settings = self.setup_custodian_settings(is_neb=True)
            spec_fname = folder.get_abs_path(PluginDefaults.CSTDN_SPEC_FNAME)
            custodian_settings.write_custodian_spec(pathlib.Path(spec_fname))
