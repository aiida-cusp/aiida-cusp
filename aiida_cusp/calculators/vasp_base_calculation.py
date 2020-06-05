# -*- coding: utf-8 -*-
"""
Base class serving as parent for other VASP calculator implementations
"""


from aiida.engine import CalcJob
from aiida.orm import RemoteData

from aiida_cusp.utils.defaults import PluginDefaults


class VaspBaseCalculation(CalcJob):
    """
    Base class implementing the basic inputs and features commond to all
    kind of VASP calculations. Includes all available inputs available to
    regular VASP calculations as well as NEB calculations.
    """

    # default filenames used for the stderr/stdout logging of the calculation
    _default_error_file = PluginDefaults.STDERR_FNAME
    _default_output_file = PluginDefaults.STDOUT_FNAME

    @classmethod
    def define(cls, spec):
        """
        Defined the required inputs for the calculation process.
        """
        super(VaspBaseCalculation, cls).define(spec)
        # set withmpi to `True` by default since VASP is usually meant to be
        # run in parallel
        spec.input(
            'metadata.options.withmpi',
            valid_type=bool,
            default=True,
            help=("Set this option to `False` to run the calculation"
                  "without MPI support")
        )
        spec.input(
            'restart.folder',
            valid_type=RemoteData,
            required=False,
            help=("Remotely located folder used to restart a calculation")
        )
        spec.input(
            'restart.from_scratch',
            valid_type=bool,
            default=False,
            required=False,
            help=("If set to `True` calculation is restarted from scratch "
                  "(i.e. POSCAR will not be replaced by CONTCAR)")
        )

    def prepare_for_submission(self, folder):
        # do all the regular setups
        # if 'parent_folder' in self.inputs:  # create a restarted calculation
        #   self.create_inputs_for_restart(folder)
        # else:  # create a regular calculation
        #   self.create_inputs_for_regular(folder)
        pass

    def create_inputs_for_restart(self, folder):
        """
        Methods to create the input files for a restarted calculation.
        (This method has to be implemented by the parent class)
        """
        raise NotImplementedError

    def create_inputs_for_regular(self, folder):
        """
        Methods to create the inputs for a regular calculation.
        (This method has to be implemented by the parent class)
        """
        raise NotImplementedError
