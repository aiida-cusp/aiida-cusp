# -*- coding: utf-8 -*-
class VaspDefaults(object):
    """
    Collection of default values for VASP
    """
    # map functionals contained in archive file names to internal string
    FUNCTIONAL_MAP = {
        # LDA type potentials
        'potUSPP_LDA': 'lda_us',
        'potpaw_LDA': 'lda',
        'potpaw_LDA.52': 'lda_52',
        'potpaw_LDA.54': 'lda_54',
        # PBE type potentials
        'potpaw_PBE': 'pbe',
        'potpaw_PBE.52': 'pbe_52',
        'potpaw_PBE.54': 'pbe_54',
        # PW91 type potentials
        'potUSPP_GGA': 'pw91_us',
        'potpaw_GGA': 'pw91',
    }
