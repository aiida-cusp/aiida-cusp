# -*- coding: utf-8 -*-


# FIXME: Decide what to do with the screened exchange (WFULLxxxx.tmp) and the
#        diagonal elements of the screened exchange (Wxxxx.tmp) output files
#        written for BSE calculations


class VaspDefaults(object):
    """
    Collection of default values for VASP
    """
    # map functionals contained in archive file names to internal string
    FUNCTIONAL_MAP = {
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
    }
    # filenames for VASP input and output files
    FNAMES = {
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
        # outputs of bse-calculations
        # 'Wxxxx.tmp',
        # 'WFULLxxxx.tmp',
    }


class PluginDefaults(object):
    # filenames for logging of stdin and stderr during AiiDA VASP calculations
    STDERR_FNAME = 'aiida.err'
    STDOUT_FNAME = 'aiida.out'
    # default name used for the input file to the cstdn executable
    CSTDN_SPEC_FNAME = 'cstdn_spec.yaml'
