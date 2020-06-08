# -*- coding: utf-8 -*-
"""
Base class serving as parent for other VASP calculator implementations
"""


from aiida.engine import CalcJob
from aiida.orm import RemoteData, Code
from aiida.common import (CalcInfo, CodeInfo, CodeRunMode)

from aiida_cusp.utils.defaults import PluginDefaults


class CalculationBase(CalcJob):
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
        super(CalculationBase, cls).define(spec)
        # set withmpi to `True` by default since VASP is usually meant to be
        # run in parallel
        spec.input(
            'metadata.options.withmpi',
            valid_type=bool,
            default=True,
            help=("Set this option to `False` to run the calculation"
                  "without MPI support")
        )
        # Setup settings and code used to run the VASP code through the
        # custodian error handler (if custodian remains undefined a simple
        # VASP calculation is run)
        spec.input(
            'custodian.code',
            valid_type=Code,
            required=False,
            help=("Code to use for the custodian executable")
        )
        spec.input_namespace('custodian.settings', required=False, non_db=True)
        spec.input(
            'custodian.settings.max_errors_per_job',
            valid_type=int,
            help=("Maximum number of accepted errors before the calculation "
                  "is terminated")
        )
        spec.input(
            'custodian.settings.max_errors',
            valid_type=int,
            help=("Maximum number of accepted errors before the calculation "
                  "is terminated")
        )
        spec.input(
            'custodian.settings.polling_time_step',
            valid_type=int,
            help=("Seconds between two consecutive checks for the calcualtion "
                  "being completed")
        )
        spec.input(
            'custodian.settings.monitor_freq',
            valid_type=int,
            help=("Number of performed polling steps before the calculation "
                  "is checked for possible errors")
        )
        spec.input(
            'custodian.settings.skip_over_errors',
            valid_type=bool,
            help=("If set to `True` failed error handlers will be skipped")
        )
        # do we really want to make this option available? Because, the
        # scratch dir is already set by AiiDA, i.e. the code
        spec.input(
            'custodian.settings.scratch_dir',
            valid_type=str,
            help=("Temporary directory used to execute the custodian job")
        )
        # certainly not needed because file compression is done after the
        # calculation using the AiiDA repository framework
        spec.input(
            'custodian.settings.gzipped_output',
            valid_type=bool,
            help=("")
        )
        # not needed
        spec.input(
            'custodian.settings.checkpoint',
            valid_type=int,
            help=("")
        )
        # not needed
        spec.input(
            'custodian.settings.terminate_on_nonzero_returncode',
            valid_type=int,
            help=("")
        )
#        spec.input(
#            'custodian.handlers',
#            valid_type=(dict, list),
#            default={},
#            non_db=True,
#            help=("Error handlers connected to the custodian executable")
#        )
        # TODO: Is from_scratch flag really neccessary?
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
            non_db=True,
            help=("If set to `True` calculation is restarted from scratch "
                  "(i.e. POSCAR will not be replaced by CONTCAR)")
        )

    def prepare_for_submission(self, folder):
        # if no custodian code is defined directly run the VASP calculation,
        # i.e. initialize the CodeInfo for the passed VASP code
        if 'code' not in self.inputs.custodian:
            codeinfo = CodeInfo()
            codeinfo.code_uuid = self.inputs.code.uuid
            codeinfo.stdout_name = self._default_output_file
            codeinfo.stderr_name = self._default_error_file
        # otherwise wrap in Custodian calculation and initialize CodeInfo for
        # the passed Custodian code (This is sufficient as AiiDA will scan all
        # Code-inputs to generate the required prepend / append lines)
        else:
            codeinfo = CodeInfo()
            codeinfo.code_uuid = self.inputs.custodian.code.uuid
            codeinfo.cmdline_params = ['run', PluginDefaults.CSTDN_SPEC_FNAME]
            # do not add the MPI command to custodian since it will call
            # VASP using MPI
            codeinfo.withmpi = False
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.remote_symlink_list = []
        calcinfo.retrieve_temporary_list = []
        # need to set run mode since presubmit() takes all code inputs into
        # account and would complain if both vasp and custodian codes are set
        calcinfo.codes_run_mode = CodeRunMode.SERIAL
        # finally setup the regular VASP input files wither for a regular or
        # a restarted run
        if 'parent_folder' in self.inputs:  # create a restarted calculation
            self.create_inputs_for_restart_run(folder)
        else:  # create a regular calculation
            self.create_inputs_for_regular_run(folder)
        return calcinfo

    def vasp_calc_mpi_args(self):
        """
        Obtain the mpirun commands and the provided extra mpi parameters

        This function is basically a copy of the procedure internally used
        by AiiDA in it's CalcJob.presubmit() method to build the list of
        MPI and extra MPI parameters.
        """
        computer = self.inputs.code.computer
        scheduler = computer.get_scheduler()
        resources = self.inputs.metadata.options.resources
        default_cpus_machine = computer.get_default_mpiprocs_per_machine()
        if default_cpus_machine is not None:
            resources['default_mpiprocs_per_machine'] = default_cpus_machine
        job_resource = scheduler.create_job_resource(**resources)
        tot_num_mpiprocs = job_resource.get_tot_num_mpiprocs()
        mpi_arg_dict = {'tot_num_mpiprocs': tot_num_mpiprocs}
        for key, value in job_resource.items():
            mpi_arg_dict[key] = value
        mpirun_command = computer.get_mpirun_command()
        mpi_base_args = [arg.format(**mpi_arg_dict) for arg in mpirun_command]
        mpi_extra_args = self.inputs.metadata.options.mpirun_extra_params
        return mpi_base_args, mpi_extra_args

    def vasp_run_line(self):
        """
        Get the VASP run line used by the custodian script to start the
        VASP calculation

        Populates the CalcInfo object with all required parameters such
        that the generated CalcInfo instance can be passed to the schedulers
        _get_run_line() method to obtain the runline.
        """
        # build the list of command line arguments forming the final
        # runline command
        vasp_exec = [self.inputs.code.get_execname()]
        if self.inputs.metadata.options.withmpi:
            mpicmd, mpiextra = self.vasp_calc_mpi_args()
            vasp_cmdline_params = mpicmd + mpiextra + vasp_exec
        else:
            vasp_cmdline_params = vasp_exec
        return vasp_cmdline_params
        # Custodian requires the vasp-cmd as list of arguments. Since we also
        # pass the stdout / stderr files to custodian as files for the logging
        # we're done here
        # # assemble the corresponding CodeInfo
        # codeinfo = CodeInfo()
        # # redirect will be handled by the custodian executable
        # #codeinfo.stdout_name = self._default_output_file
        # #codeinfo.stderr_name = self._default_error_file
        # codeinfo.cmdline_params = vasp_cmdline_params
        # codeinfo.join_files = False  # do not combine stderr / stdout
        # # use connected scheduler to obtain the explicit run line
        # scheduler = self.inputs.code.computer.get_scheduler()
        # run_line = scheduler._get_run_line([codeinfo], CodeRunMode.SERIAL)
        # return run_line

    def create_inputs_for_restart_run(self, folder):
        """
        Methods to create the input files for a restarted calculation.
        (This method has to be implemented by the parent class)
        """
        raise NotImplementedError

    def create_inputs_for_regular_run(self, folder):
        """
        Methods to create the inputs for a regular calculation.
        (This method has to be implemented by the parent class)
        """
        raise NotImplementedError
