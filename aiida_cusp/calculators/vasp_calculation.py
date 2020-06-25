# -*- coding: utf-8 -*-


"""
Calculator class performing VASP calculations
"""


from aiida_cusp.utils.defaults import PluginDefaults, VaspDefaults
from aiida_cusp.calculators.vasp_basic_calculation import VaspBasicCalculation
from aiida_cusp.calculators.vasp_neb_calculation import VaspNebCalculation
from aiida_cusp.data import VaspIncarData, VaspKpointData, VaspPotcarData


class VaspCalculation(VaspBasicCalculation, VaspNebCalculation):
    """
    """

    @classmethod
    def define(cls, spec):
        super(VaspCalculation, cls).define(spec)
        # define the inputs common to both regular and neb calculations
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
        # define parser to be used with the calculation
        spec.input(
            'metadata.options.parser_name',
            valid_type=str,
            default='cusp.default',
            help=("Parser used to parse the results of a finished "
                  "calculation (if undefined `cusp.default` is used "
                  "by default)")
        )
        # exit codes for parsing errors
        spec.exit_code(
            300,
            'ERRNO_TEMPORARY_RETRIEVE_FOLDER',
            message=("the temporary retrieved folder is not available")
        )
        spec.exit_code(
            301,
            'ERRNO_UNKNOWN_PARSER_SETTING',
            message=("unknown parser setting")
        )
        spec.exit_code(
            302,
            'ERRNO_PARSING_LIST_EMPTY',
            message=("requested output files not found among the "
                     "retrieved files")
        )
        spec.exit_code(
            303,
            'ERRNO_DUPLICATE_LINKNAME',
            message=("parser tried to register two output nodes using "
                     "identical linknames")
        )

    def create_calculation_inputs(self, folder, calcinfo):
        """
        Write the calculation inputs and setup the retrieve lists based on
        the type of calculation (i.e. Basic or NEB calculation)
        """
        # only verify that structures are present and are either of type
        # poscar or neb_path.
        self.verify_structure_inputs()
        if self.is_neb():
            parent_cls = VaspNebCalculation
        else:
            parent_cls = VaspBasicCalculation
        calcinfo = parent_cls.create_calculation_inputs(self, folder, calcinfo)
        return calcinfo

    def restart_files_exclude(self):
        """
        Extend the default list of excluded files defined by the parent
        CalculationBase class if neccessary.

        As the sandbox folder gets uploaded in an early submission stage
        adding files given as inputs to a restarted calculation assures
        that those files are not overwritten by the possibly available
        corresponding remote file
        """
        # get the list of files excluded by default
        exclude = super(VaspCalculation, self).restart_files_exclude()
        # do not copy INCAR if defined as input
        if self.inputs.get('incar', False):
            exclude += [VaspDefaults.FNAMES['incar']]
        # do not copy KPOINTS if defined as input
        if self.inputs.get('kpoints', False):
            exclude += [VaspDefaults.FNAMES['kpoints']]
        return exclude

    def is_neb(self):
        remote_folder = self.inputs.restart.get('folder', False)
        if remote_folder:  # restart: use inputs from parent calcjob class
            # check inputs of parent calculation class associated with the
            # remote folder for 'neb_path' input, here we need to check if
            # any key starts with neb_path since the stored node only contains
            # the option as flattened version
            inputs = remote_folder.creator.inputs
            return any([key.startswith('neb_path') for key in inputs]) or False
        else:  # no restart: check the inputs of this calcjob
            # checking this calculation we can simply use dictionary syntax
            # due to the not yet flattened inputs
            return any(self.inputs.neb_path) or False

    def verify_structure_inputs(self):
        restart = self.inputs.restart.get('folder', False)
        if not restart:  # only check for structure if not a restart
            poscar = self.inputs.get('poscar', False)
            neb_path = self.inputs.get('neb_path', False)
            if poscar and neb_path:
                raise Exception("'poscar' and 'neb_path' cannot be set "
                                "at the same time")
            if not poscar and not neb_path:
                raise Exception("Missing non-optional structure input")
