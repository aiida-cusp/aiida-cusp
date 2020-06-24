# -*- coding: utf-8 -*-


"""
Base class serving as parent for other VASP calculator implementations
"""


import pathlib

from aiida.engine import CalcJob
from aiida.orm import RemoteData, Code, Int, Bool, Dict, List
from aiida.orm.nodes.data.base import to_aiida_type
from aiida.common import (CalcInfo, CodeInfo, CodeRunMode)

from aiida_cusp.utils.defaults import (PluginDefaults, VaspDefaults,
                                       CustodianDefaults)
from aiida_cusp.utils.custodian import CustodianSettings


# TODO: This is a temporary fix since the to_aiida_type serizalizer function
#       obviously is not defined for the aiida.orm.List type...
def dl_serialize(value):
    # passing a list of handler names is equivalent to passing
    # a dictionary of handler names with empty dicts as values to indicate
    # default values shall be used
    # Thus, we directly transform the list to the corresponding dict to
    # avoid further issues downstream
    if isinstance(value, (list, tuple)):
        out = {v: {} for v in value}
    elif isinstance(value, dict):
        out = value
    return Dict(dict=out)


class CalculationBase(CalcJob):
    """
    Base class implementing the basic inputs and features commond to all
    kind of VASP calculations. Includes a list of available inputs common
    to both basic VASP calculations as well as NEB calculations.
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
        spec.input_namespace('custodian', required=False)
        spec.input(
            'custodian.code',
            valid_type=Code,
            required=False,
            help=("Code to use for the custodian executable")
        )
        # definition of vasp error handlers connected to the calculation
        spec.input(
            'custodian.handlers',
            valid_type=(Dict, List),
            default=lambda: Dict(dict={}),
            serializer=dl_serialize,
            help=("Error handlers connected to the custodian executable")
        )
        spec.input_namespace('custodian.settings', required=False)
        # since custodian is exlusively used to run a VASP calculation with
        # enabled error correction only the most basic custodian options
        # affecting single runs are exposed here
        spec.input(
            'custodian.settings.max_errors',
            valid_type=Int,
            serializer=to_aiida_type,
            default=lambda: Int(10),
            help=("Maximum number of accepted errors before the calculation "
                  "is terminated")
        )
        spec.input(
            'custodian.settings.polling_time_step',
            valid_type=Int,
            serializer=to_aiida_type,
            default=lambda: Int(10),
            help=("Seconds between two consecutive checks for the calcualtion "
                  "being completed")
        )
        spec.input(
            'custodian.settings.monitor_freq',
            valid_type=Int,
            serializer=to_aiida_type,
            default=lambda: Int(30),
            help=("Number of performed polling steps before the calculation "
                  "is checked for possible errors")
        )
        spec.input(
            'custodian.settings.skip_over_errors',
            valid_type=Bool,
            serializer=to_aiida_type,
            default=lambda: Bool(False),
            help=("If set to `True` failed error handlers will be skipped")
        )
        # required inputs to restart a calculation
        spec.input_namespace('restart', required=False)
        spec.input(
            'restart.folder',
            valid_type=RemoteData,
            required=False,
            help=("Remotely located folder used to restart a calculation")
        )
        spec.input(
            'restart.contcar_to_poscar',
            valid_type=Bool,
            serializer=lambda val: Bool(val),
            default=lambda: Bool(True),
            required=False,
            help=("If set to `False` POSCAR in the restarted calculation will "
                  "not be replaced with CONTCAR form parent calculation")
        )
        # extend the metadata.options namespace with an additional
        # option to specify optional parser settings
        spec.input_namespace('metadata.options.parser_settings',
                             required=False, non_db=True, dynamic=True)

    def prepare_for_submission(self, folder):
        """
        The baseclass will only setup the basic calcinfo arguments but will
        not write **any** files which has to be implemented in the subclassed
        prepare_for_submission() method
        """
        # if no custodian code is defined directly run the VASP calculation,
        # i.e. initialize the CodeInfo for the passed VASP code
        if not self.inputs.custodian.get('code', False):
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
            # define custodian-exe command line arguments
            codeinfo.cmdline_params = ['run', PluginDefaults.CSTDN_SPEC_FNAME]
            # never add the MPI command to custodian since it will call
            # VASP using MPI itself
            codeinfo.withmpi = False
        calcinfo = CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.codes_info = [codeinfo]
        # those list are set defined in the inherited classes
        calcinfo.local_copy_list = []
        calcinfo.remote_copy_list = []
        calcinfo.remote_symlink_list = []
        # retrieve lists are defined on the base class
        calcinfo.retrieve_temporary_list = self.retrieve_temporary_list()
        calcinfo.retrieve_list = self.retrieve_permanent_list()
        # need to set run mode since presubmit() takes all code inputs into
        # account and would complain if both vasp and custodian codes are set
        calcinfo.codes_run_mode = CodeRunMode.SERIAL
        # finally write the neccessary calculation inputs to the calculation's
        # input folder
        calcinfo = self.create_calculation_inputs(folder, calcinfo)
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
        # Custodian requires the vasp-cmd be a list of arguments. Since we
        # also pass the stdout / stderr log-files directly to custodian we're
        # done at this point
        return vasp_cmdline_params

    def remote_filelist(self, remote_data, relpath='.'):
        """
        Recurse remote folder contents and return a list of all files found
        on the remote with the list containing the files names, relative
        paths and the absolute file path on the remote.
        :returns: list of tuples of type (filename, absolut_path_on_remote,
            relative_path (without the filename)
        """
        filelist = []
        import pathlib
        for path in remote_data.listdir(relpath=relpath):
            subpath = relpath + '/' + path
            try:  # call listdir() on the given path and recurse
                files = self.remote_filelist(remote_data, relpath=subpath)
                filelist.extend(files)
            except OSError:  # cannot call listdir() because subpath is file
                # absolute file path on remote including the file name
                abspath = remote_data.get_remote_path() + '/' + subpath
                abspath = str(pathlib.Path(abspath).absolute())
                relpath = str(pathlib.Path(relpath))
                filelist.append((path, abspath, relpath))
        return filelist

    def restart_files_exclude(self):
        """
        Create a list of files that will not be copied from the remote
        restart folder to the current calculation folder.
        """
        # files never copied for restarted calculations
        exclude_files = [
            self.inputs.metadata.options.get('submit_script_filename'),
            PluginDefaults.CSTDN_SPEC_FNAME,
            'job_tmpl.json',
            'calcinfo.json',
        ]
        # do not copy POSCAR if replaced with CONTCAR
        if self.inputs.restart.get('contcar_to_poscar', False):
            exclude_files += [VaspDefaults.FNAMES['poscar']]
        return exclude_files

    def setup_custodian_settings(self, is_neb=False):
        """
        Create custodian settings instance from the given handlers and
        settings.
        """
        # setup the inputs to create the custodian settings from the passed
        # parameters
        settings = dict(self.inputs.custodian.get('settings'))
        handlers = dict(self.inputs.custodian.get('handlers'))
        # get the vasp run command and the stdout / stderr files
        vasp_cmd = self.vasp_run_line()
        stdout = self._default_output_file
        stderr = self._default_error_file
        # setup custodian settings used to write the spec file
        custodian_settings = CustodianSettings(vasp_cmd, stdout, stderr,
                                               settings=settings,
                                               handlers=handlers,
                                               is_neb=is_neb)
        return custodian_settings

    def restart_copy_remote(self, folder, calcinfo):
        """
        Copy and write remote input files for a restarted VASP calcualtion
        """
        # check the remote directory for files and build the remote copy
        # list
        remote_data = self.inputs.restart.get('folder')
        remote_comp_uuid = remote_data.computer.uuid
        exclude_files = self.restart_files_exclude()
        overwrite_poscar = self.inputs.restart.get('contcar_to_poscar')
        for name, abspath, relpath in self.remote_filelist(remote_data):
            if name in exclude_files:
                continue
            # if overwrite poscar is set change target name for CONTCAR-files
            # to POSCAR
            if name == VaspDefaults.FNAMES['contcar'] and overwrite_poscar:
                name = VaspDefaults.FNAMES['poscar']
            file_relpath = relpath + '/' + name
            remote_copy_entry = (remote_comp_uuid, abspath, file_relpath)
            calcinfo.remote_copy_list.append(remote_copy_entry)
            # copying files from remote to remote all parent folders need to
            # exist in the target directory already since the internal copy
            # mechanism is not capable of generating the required directories.
            # however, in the very early stages of the submission and upload
            # process, i.e. before any copylists are executed, AiiDA already
            # copied the contents of the sandbox-folder to the remote working
            # directory. Thus, all required parent folders can be generated by
            # simply replicating the remote-folder structure inside the
            # sandbox :)
            file_parent_folder = pathlib.Path(folder.abspath) / relpath
            if not file_parent_folder.exists():
                file_parent_folder.mkdir(parents=True)

    def retrieve_temporary_list(self):
        """
        Defines the list of files marked for temporary retrieval.

        By default each calculaltion will retrieve **all** available files
        created by the calculation and store them to a temporary folder.
        Which of the files are actually kept is then decided by the
        subsequently running parser.
        """
        # simply retrieve everything in the calculation folder
        retrieve_temporary = [('*', '.', 0)]
        return retrieve_temporary

    def retrieve_permanent_list(self):
        """
        Define the list of files marked for permanent retrieval.

        Here only calculation independent files are marked for retrieval,
        i.e. files like the submit-script, scheduler outputs, etc.
        Retrieval of calculation files is the responsibility of the connected
        parser.
        """
        retrieve_permanent = [
            # submit script and custodian logfiles
            self.inputs.metadata.options.get('submit_script_filename'),
            PluginDefaults.CSTDN_SPEC_FNAME,
            CustodianDefaults.RUN_LOG_FNAME,
            # other logfiles, i.e. scheduler as well as stdout / stderr
            self.inputs.metadata.options.get('scheduler_stdout'),
            self.inputs.metadata.options.get('scheduler_stderr'),
            PluginDefaults.STDOUT_FNAME,
            PluginDefaults.STDERR_FNAME,
        ]
        return retrieve_permanent

    def create_calculation_inputs(self, folder, calcinfo):
        """
        Write the calculation inputs and set the rerieve lists
        (This method has to be implemented by the inherited subclass)
        """
        raise NotImplementedError
