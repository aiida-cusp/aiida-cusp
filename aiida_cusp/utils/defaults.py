# -*- coding: utf-8 -*-


from aiida_cusp.utils.decorators import classproperty


# FIXME: Decide what to do with the screened exchange (WFULLxxxx.tmp) and the
#        diagonal elements of the screened exchange (Wxxxx.tmp) output files
#        written for BSE calculations


class VaspDefaults(object):
    """
    Collection of default values for VASP
    """
    # map functionals contained in archive file names to internal string
    @classproperty
    def FUNCTIONAL_MAP(cls):
        return dict({
            # LDA type potentials
            'potuspp_lda': 'lda_us',
            'potpaw_lda': 'lda',
            'potpaw_lda.52': 'lda_52',
            'potpaw_lda.54': 'lda_54',
            # PBE type potentials
            'potpaw_pbe': 'pbe',
            'potpaw_pbe.52': 'pbe_52',
            'potpaw_pbe.54': 'pbe_54',
            # PW91 type potentials
            'potuspp_gga': 'pw91_us',
            'potpaw_gga': 'pw91',
        })

    @classproperty
    def FNAMES(cls):
        # filenames for VASP input and output files
        return dict({
            # inputs
            'potcar': 'POTCAR',
            'incar': 'INCAR',
            'poscar': 'POSCAR',
            'kpoints': 'KPOINTS',
            # outputs
            'contcar': 'CONTCAR',
            'chg': 'CHG',
            'chgcar': 'CHGCAR',
            'doscar': 'DOSCAR',
            'eigenval': 'EIGENVAL',
            'elfcar': 'ELFCAR',
            'ibzkpt': 'IBZKPT',
            'locpot': 'LOCPOT',
            'oszicar': 'OSZICAR',
            'outcar': 'OUTCAR',
            'parchg': 'PARCHG',
            'pcdat': 'PCDAT',
            'procar': 'PROCAR',
            'proout': 'PROOUT',
            'report': 'REPORT',
            'tmpcar': 'TMPCAR',
            'vasprun': 'vasprun.xml',
            'wavecar': 'WAVECAR',
            'waveder': 'WAVEDER',
            'xdatcar': 'XDATCAR',
            'bsefatband': 'BSEFATBAND',
            # outpts of bse-calculations
            # 'W*.tmp',
            # 'WFULL*.tmp',
        })


class PluginDefaults(object):
    # filenames for logging of stdin and stderr during AiiDA VASP calculations
    @classproperty
    def STDERR_FNAME(cls):
        return 'aiida.err'

    @classproperty
    def STDOUT_FNAME(cls):
        return 'aiida.out'

    # default name used for the input file to the cstdn executable
    @classproperty
    def CSTDN_SPEC_FNAME(cls):
        return 'cstdn_spec.yaml'

    # default identifier prefix for neb-path node inputs
    @classproperty
    def NEB_NODE_PREFIX(cls):
        return 'node_'

    # expected format for neb-path node identifiers
    @classproperty
    def NEB_NODE_REGEX(cls):
        import re
        identifier = r"^{}[0-9]{{2}}$".format(cls.NEB_NODE_PREFIX)
        return re.compile(identifier)

    # default output namespace through which parsed calculation results
    # are added to the calculation
    @classproperty
    def PARSER_OUTPUT_NAMESPACE(cls):
        return "parsed_results"


class CustodianDefaults(object):
    """
    Collection of default values for the custodian calculator comprising
    default job options, handlers and corresponding handler options.
    """
    # default name of the custodian logfile
    @classproperty
    def RUN_LOG_FNAME(cls):
        return "run.log"

    # path prefix for handler imports
    @classproperty
    def HANDLER_IMPORT_PATH(cls):
        return 'custodian.vasp.handlers'

    # import paths for the custodian jobs running VASP and VASP Neb calcs
    @classproperty
    def VASP_NEB_JOB_IMPORT_PATH(cls):
        return 'custodian.vasp.jobs.VaspNEBJob'

    @classproperty
    def VASP_JOB_IMPORT_PATH(cls):
        return 'custodian.vasp.jobs.VaspJob'

    # default settings controlling regular VASP jobs run through custodian
    @classproperty
    def VASP_JOB_SETTINGS(cls):
        return {
            'vasp_cmd': None,
            'output_file': PluginDefaults.STDOUT_FNAME,
            'stderr_file': PluginDefaults.STDERR_FNAME,
            'suffix': "",
            'final': True,
            'backup': True,
            'auto_npar': False,
            'auto_gamma': False,
            'settings_override': None,
            'gamma_vasp_cmd': None,
            'copy_magmom': False,
            'auto_continue': False,
        }

    # default settings controlling NEB VASP jobs run through custodian
    @classproperty
    def VASP_NEB_JOB_SETTINGS(cls):
        return {
            'vasp_cmd': None,
            'output_file': PluginDefaults.STDOUT_FNAME,
            'stderr_file': PluginDefaults.STDERR_FNAME,
            'suffix': "",
            'final': True,
            'backup': True,
            'auto_npar': False,
            'auto_gamma': False,
            'half_kpts': False,
            'settings_override': None,
            'gamma_vasp_cmd': None,
            'auto_continue': False,
        }

    # default settings controlling the custodian executable
    @classproperty
    def CUSTODIAN_SETTINGS(cls):
        return {
            'max_errors_per_job': None,
            'max_errors': 10,
            'polling_time_step': 10,
            'monitor_freq': 30,
            'skip_over_errors': False,
            'scratch_dir': None,
            'gzipped_output': False,
            'checkpoint': False,
            'terminate_func': None,
            'terminate_on_nonzero_returncode': False,
        }

    # custodian settings that may be altered by the user (settings not
    # defined here won't be accepted when passed as input to the
    # calculation's custodian.settings option!)
    @classproperty
    def MODIFIABLE_SETTINGS(cls):
        return ['max_errors', 'polling_time_step', 'monitor_freq',
                'skip_over_errors']

    # dictionary of the used default settings for all VASP error handlers
    # that may be used with this plugin
    @classproperty
    def ERROR_HANDLER_SETTINGS(cls):
        return dict({
            'AliasingErrorHandler': {
                'output_filename': PluginDefaults.STDOUT_FNAME,
            },
            'DriftErrorHandler': {
                'max_drift': None,
                'to_average': 3,
                'enaug_multiply': 2,
            },
            'FrozenJobErrorHandler': {
                'output_filename': PluginDefaults.STDOUT_FNAME,
                'timeout': 21600,
            },
            'IncorrectSmearingHandler':{}, 
            'LargeSigmaHandler': {},
            'LrfCommutatorHandler': {
                'output_filename': PluginDefaults.STDERR_FNAME,
            },
            'MeshSymmetryErrorHandler': {
                'output_filename': PluginDefaults.STDOUT_FNAME,
                'output_vasprun': VaspDefaults.FNAMES['vasprun'],
            },
            'NonConvergingErrorHandler': {
                'output_filename': VaspDefaults.FNAMES['oszicar'],
                'nionic_steps': 10,
            },
            'PositiveEnergyErrorHandler': {
                'output_filename': VaspDefaults.FNAMES['oszicar'],
            },
            'PotimErrorHandler': {
                'input_filename': VaspDefaults.FNAMES['poscar'],
                'output_filename': VaspDefaults.FNAMES['oszicar'],
                'dE_threshold': 1.0,
            },
            'StdErrHandler': {
                'output_filename': PluginDefaults.STDERR_FNAME,
            },
            'UnconvergedErrorHandler': {
                'output_filename': VaspDefaults.FNAMES['vasprun'],
            },
            'VaspErrorHandler': {
                'output_filename': PluginDefaults.STDOUT_FNAME,
                'natoms_large_cell': 100,
                'errors_subset_to_catch': None,
            },
            'WalltimeHandler': {
                'wall_time': None,
                'buffer_time': 300,
                'electronic_step_stop': False,
            },
        })  # ERROR_HANDLER_SETTINGS


class VasprunParsingDefaults:
    """
    Default settings used to parse vasprun.xml files
    """

    # Defaults passed to the pymatgen.io.vasp.outputs.Vasprun parser
    @classproperty
    def PARSER_ARGS(cls):
        return dict({
            'ionic_step_skip': None,
            'ionic_step_offset': 0,
            'parse_dos': False,
            'parse_eigen': False,
            'parse_projected_eigen': False,
            'occu_tol': 1.0E-8,
            'exception_on_bad_xml': False,
        })
