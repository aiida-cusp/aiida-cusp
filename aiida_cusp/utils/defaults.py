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

    # collection of VASP output files that will be retrieved by default (i.e.
    # when no specific list of to retrieve was passed to the calculation)
    @classproperty
    def DEFAULT_RETRIEVE_LIST(cls):
        default_retrieve_list = [
            VaspDefaults.FNAMES['vasprun'],
            VaspDefaults.FNAMES['outcar'],
            VaspDefaults.FNAMES['contcar'],
        ]
        return default_retrieve_list


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
    # (except for fixed parameters, which will be used for all calculations
    # automatically, other parameter are only used in case no job input
    # was passed to the calculation)
    @classproperty
    def VASP_JOB_SETTINGS(cls):
        return {
            # always need to be replaced with the plugin defaults
            'vasp_cmd': None,
            'output_file': PluginDefaults.STDOUT_FNAME,
            'stderr_file': PluginDefaults.STDERR_FNAME,
            # disallow automatic switch to gamma optimized version
            'auto_gamma': False,
            'gamma_vasp_cmd': None,
            # default parameters that are only used internally if no
            # VaspJob was defined by the user
            'suffix': "",
            'final': True,
            'backup': True,
            'auto_npar': False,
            'settings_override': None,
            'copy_magmom': False,
            'auto_continue': False,
        }

    @classproperty
    def VASP_JOB_FIXED_SETTINGS(cls):
        return ['vasp_cmd', 'output_file', 'stderr_file', 'auto_gamma',
                'gamma_vasp_cmd']

    # default settings controlling NEB VASP jobs run through custodian
    # (except for fixed parameters, which will be used for all calculations
    # automatically, other parameter are only used in case no job input
    # was passed to the calculation)
    @classproperty
    def VASP_NEB_JOB_SETTINGS(cls):
        return {
            # always need to be replaced with the plugin defaults
            'vasp_cmd': None,
            'output_file': PluginDefaults.STDOUT_FNAME,
            'stderr_file': PluginDefaults.STDERR_FNAME,
            # disallow automatic switch to gamma optimized version
            'auto_gamma': False,
            'gamma_vasp_cmd': None,
            # default parameters that are only used internally if no
            # VaspNEBJob was defined by the user
            'suffix': "",
            'final': True,
            'backup': True,
            'auto_npar': False,
            'half_kpts': False,
            'settings_override': None,
            'auto_continue': False,
        }

    @classproperty
    def VASP_NEB_JOB_FIXED_SETTINGS(cls):
        return ['vasp_cmd', 'output_file', 'stderr_file', 'auto_gamma',
                'gamma_vasp_cmd']

    # default settings for controlling the overall custodian executable
    # wrapping and monitoring the calculation job (note that some of the
    # settings are protected parameters which may be set by the user but
    # will be overwritten by the internal default parameters)
    @classproperty
    def CUSTODIAN_SETTINGS(cls):
        return {
            'max_errors': 10,
            'max_errors_per_job': None,
            'polling_time_step': 10,
            'monitor_freq': 30,
            'skip_over_errors': False,
            'terminate_on_nonzero_returncode': False,
            # will always be replaced with the following defaults
            'scratch_dir': None,
            'gzipped_output': False,
            'terminate_func': None,
            # disallow validators for now
            'validators': None,
            # disallow checkpoint
            'checkpoint': False,
        }

    # custodian settings that may be altered by the user (settings not
    # defined here won't be accepted when passed as input to the
    # calculation's custodian.settings option!)
    @classproperty
    def FIXED_CUSTODIAN_SETTINGS(cls):
        return ['scratch_dir', 'gzipped_output', 'terminate_func',
                'validators', 'checkpoint']

    # the following dictionary contains all error handlers defined in the
    # custodian package. dictionary entries defined here will be used during
    # calculation setup to overwrite any user given inputs
    @classproperty
    def ERROR_HANDLER_SETTINGS(cls):
        return dict({
            'AliasingErrorHandler': {
                'output_filename': PluginDefaults.STDOUT_FNAME,
            },
            'FrozenJobErrorHandler': {
                'output_filename': PluginDefaults.STDOUT_FNAME,
            },
            'IncorrectSmearingHandler': {
                'output_filename': VaspDefaults.FNAMES['vasprun'],
            },
            'LrfCommutatorHandler': {
                'output_filename': PluginDefaults.STDERR_FNAME,
            },
            'MeshSymmetryErrorHandler': {
                'output_filename': PluginDefaults.STDOUT_FNAME,
                'output_vasprun': VaspDefaults.FNAMES['vasprun'],
            },
            'NonConvergingErrorHandler': {
                'output_filename': VaspDefaults.FNAMES['oszicar'],
            },
            'PositiveEnergyErrorHandler': {
                'output_filename': VaspDefaults.FNAMES['oszicar'],
            },
            'PotimErrorHandler': {
                'input_filename': VaspDefaults.FNAMES['poscar'],
                'output_filename': VaspDefaults.FNAMES['oszicar'],
            },
            'StdErrHandler': {
                'output_filename': PluginDefaults.STDERR_FNAME,
            },
            'UnconvergedErrorHandler': {
                'output_filename': VaspDefaults.FNAMES['vasprun'],
            },
            'VaspErrorHandler': {
                'output_filename': PluginDefaults.STDOUT_FNAME,
            },
            'WalltimeHandler': {},
            'DriftErrorHandler': {},
            'LargeSigmaHandler': {},
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
