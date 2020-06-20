# -*- coding: utf-8 -*-


"""
Datatype and methods to initialize and interact with VASP specific
vasprun.xml output data
"""


# TODO: Possibly add some of the interesting vasprun.xml values (i.e.
#       final energy, is the run converged, etc..) to the class
#       as class-attributes to avoid the necessity of always loading the
#       vasprun file contents stored by the node


from pymatgen.io.vasp.outputs import Vasprun

from aiida_cusp.utils.single_archive_data import SingleArchiveData
from aiida_cusp.utils.defaults import VasprunParsingDefaults


class VaspVasprunData(SingleArchiveData):
    """
    AiiDA compatible node representing a VASP vasprun.xml output data object
    as gzip-compressed node in the repository.
    """

    def get_vasprun(self, **kwargs):
        """
        Return a :class:`pymatgen.io.vasp.outputs.Vasprun` instance
        initialized from vasprun.xml data stored by the node

        Given arguments are directly passed on to pymatgen's Vasprun
        constructor. By default, a minimal setup is used to parse the
        vasprun.xml contents, i.e.

            ionic_step_skip: None,
            ionic_step_offset: 0,
            parse_dos: False,
            parse_eigen: False,
            parse_projected_eigen: False
            occu_tol: 1.0E-8
            exception_on_bad_xml: True

        However, note that the default parameters may be overridden at any
        time by passing the desired values when calling this function.

        :param ionic_step_skip: read structures and energies only for every
            'ionic_step_skip'th ionic step
        :type ionic_step_skip: int
        :param ionic_step_offset: ignore energies and structures at ionic
            steps smaller than 'ionic_step_offset'
        :type ionic_step_offset: int
        :param parse_dos: parse density of states from the vasprun.xml
        :type parse_dos: bool
        :param parse_eigen: parse eigenvalues from the vasprun.xml
        :type parse_eigen: bool
        :param parse_projected_eigen: parse projected eigenvalues from the
            vasprun.xml
        :type parse_projected_eigen: bool
        :param occu_tol: minimum occupation tolerances for determining the
            valence and conduction band minima
        :type occu_tol: float
        :param except_on_bad_xml: throw an exception if the parsed
            vasprun.xml is malformed
        :type except_on_bad_xml: bool
        :returns: Vasprun instance initialized from the node's stored
            vasprun.xml data
        :rtype: :class:`~pymatgen.io.vasp.outputs.Vasprun`
        """
        parser_settings = self.parser_settings(**kwargs)
        # no need to decompress the file: pymatgen's Vasprun can handle
        # gzip-compressed archives :)
        parsed_vasprun = Vasprun(self.filepath, **parser_settings)
        return parsed_vasprun

    def parser_settings(self, **kwargs):
        """
        Update default parser settings with user defined inputs
        """
        parser_default_settings = VasprunParsingDefaults.PARSER_ARGS
        # update default values from user input
        for key in parser_default_settings.keys():
            if key in kwargs.keys():
                parser_default_settings[key] = kwargs.pop(key)
        if kwargs:
            remaining = ", ".join(kwargs.keys())
            raise TypeError("get_vasprun() got an unexpected keyword "
                            "argument(s) '{}'".format(remaining))
        # never attempt to parse the POTCAR since we load the vasprun.xml
        # from its own repository folder where it lives isolated from other
        # data, thus there certainly will be no POTCAR data file available
        parser_default_settings.update({'parse_potcar_file': False})
        return parser_default_settings
