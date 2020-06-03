# -*- coding: utf-8 -*-
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
        'potcar': 'POTCAR',
        'incar': 'INCAR',
        'poscar': 'POSCAR',
        'contcar': 'CONTCAR',
        'potcar': 'POTCAR',
        'kpoints': 'KPOINTS',
    }
