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
from aiida_cusp.utils.custodian import (CustodianSettings, handler_serializer,
                                        job_serializer)


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
            valid_type=Dict,
            serializer=handler_serializer,
            required=False,
            help=("Error handlers connected to the custodian executable")
        )
        spec.input(
            'custodian.jobs',
            valid_type=Dict,
            serializer=job_serializer,
            required=False,
            help=("VaspJobs connected to the custodian executable")
        )
        spec.input(
            'custodian.settings',
            valid_type=Dict,
            serializer=to_aiida_type,
            required=False,
            help=("Calculation settings passed to the custodian executable")
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
            serializer=to_aiida_type,
            required=False,
            help=("If set to `False` POSCAR in the restarted calculation will "
                  "not be replaced with CONTCAR form parent calculation")
        )
        # define the list of calculation output files to be retrieved from
        # the server by the daemon
        spec.input(
            'metadata.options.retrieve_files',
            required=False,
            non_db=True,
            valid_type=list,
            default=PluginDefaults.DEFAULT_RETRIEVE_LIST,
        )
        # extend the metadata.options namespace with an additional
        # option to specify optional parser settings
        spec.input_namespace(
            'metadata.options.parser_settings',
            required=False,
            non_db=True,
            dynamic=True
        )
        # this is the output node available to all connected parser for
        # storing their generated results (whatever these may be)
        spec.output_namespace(
            PluginDefaults.PARSER_OUTPUT_NAMESPACE,
            required=False,
            dynamic=True
        )
        # add dynamic sub-namespaces parsed_results.node_00 to
        # parsed_results.node_99 to provide possibly requird output ports for
        # neb results
        for index in range(100):  # iterate over all possible neb image indices
            neb_node_namespace = "{}.node_{:0>2d}".format(
                                 PluginDefaults.PARSER_OUTPUT_NAMESPACE, index)
            spec.output_namespace(neb_node_namespace, required=False,
                                  dynamic=True)

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
        # (Return _aiidasubmit.sh to remain compatible with AiiDA versions
        # prior to 1.2.1 where this option was introduced)
        exclude_files = [
            self.inputs.metadata.options.get('submit_script_filename',
                                             '_aiidasubmit.sh'),
            PluginDefaults.CSTDN_SPEC_FNAME,
            'job_tmpl.json',
            'calcinfo.json',
        ]
        # do not copy POSCAR if replaced with CONTCAR
        if self.inputs.restart.get('contcar_to_poscar', True):
            exclude_files += [VaspDefaults.FNAMES['poscar']]
        return exclude_files

    def setup_custodian_settings(self, is_neb=False):
        """
        Create custodian settings instance from the given handlers and
        settings.
        """
        # setup the inputs to create the custodian settings from the passed
        # parameters
        settings = dict(self.inputs.custodian.get('settings', {}))
        handlers = dict(self.inputs.custodian.get('handlers', {}))
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
        overwrite_poscar = self.inputs.restart.get('contcar_to_poscar', True)
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

    def files_to_retrieve(self):
        """
        Return the list of files to be retrieved from a calculation

        This list contains the files to be retrieved defined by the user
        as input to the calculation, complemented with all additional files
        that are expected by the connected parser class
        """
        # get list of files to retrieve from parser_options.
        # if no options are given proceed with default list
        retrieve = list(self.inputs.metadata.options.get('retrieve_files'))
        # get list of expected files, indicated as non-optional by the
        # connected parser class
        expected = self.expected_files()
        # complement both lists if `expected` is not None
        if expected is not None:
            retrieve = list(set(retrieve + expected))
        return retrieve

    def retrieve_temporary_list(self):
        """
        Defines the list of files marked for temporary retrieval.

        By default each calculaltion will retrieve **all** available files
        created by the calculation and store them to a temporary folder.
        Which of the files are actually kept is then decided by the
        subsequently running parser.
        """
        retrieve = self.files_to_retrieve()
        retrieve_temporary = []
        # match files located both inside the working directory **and** in
        # possibl esubfolders of that directory (i.e NEB calculations)
        for fname in retrieve:
            # FIXME: Once, support for older aiida-core versions is dropped
            #        the nesting specifier `2` can be replaced with `None`
            #        which was introduced with aiida-core 2.1.0
            retrieve_temporary.append((f"{fname}", ".", 2))
            retrieve_temporary.append((f"*/{fname}", ".", 2))
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
            # submit script and custodian logfiles (return _aiidasubmit.sh
            # by default to be compatible with AiiDA versions < 1.2.1 where
            # this option was introduced)
            self.inputs.metadata.options.get('submit_script_filename',
                                             '_aiidasubmit.sh'),
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

    def expected_files(self):
        """
        Returns the list of expected files from the connected parser
        class if defined
        (This method has to be implemented by the inherited subclass)
        """
        raise NotImplementedError
