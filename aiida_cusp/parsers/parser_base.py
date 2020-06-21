# -*- coding: utf-8 -*-


"""
The parser base class
"""


import pathlib
from aiida.common import exceptions

from aiida.parsers.parser import Parser


class ParserBase(Parser):
    """
    The ParseBase class provides the general methods like the check for
    missing folders and the setup of the retrieved file lists that may be
    used by the derived parser classes
    """

    def __init__(self, node):
        """
        Setup the parser settings and check if expected folders are present.
        Build list of parseable files found at the connected output folder
        """
        super(ParserBase, self).__init__(node)
        self.settings = self.parser_settings(node)
        self.temp_link_key = "retrieved_temporary_folder"
        self.files_to_parse = None

    def parse(self, **kwargs):
        # check temporary folder is present
        exit_code, self.tmpfolder = self.check_retrieved_temp_folder(**kwargs)
        if exit_code:
            return exit_code
        return 0  # when we reach this return everything went fine

    def check_retrieved_temp_folder(self, **kwargs):
        """
        As all calculation output files are expected to be retrieved in the
        retrieved_temporary_folder only checks for the presence of this
        folder.
        """
        temp_folder_path = kwargs.get(self.temp_link_key, None)
        if not temp_folder_path:
            exitcode = self.exit_codes.ERRNO_TEMPORARY_RETRIEVE_FOLDER
        else:
            exitcode = 0
        return exitcode, temp_folder_path

    def parser_settings(self, node):
        """
        Return the possibly available optional parser settings defined by the
        calling calculation plugin.
        """
        # get and return everything found under the
        # 'metadata.options.parser_settings' namespace
        return node.get_option('parser_settings') or {}

    def register_output_nodes(self, output_nodes):
        """
        Add the parsed results stored in the output_nodes list as output
        nodes to the calculation
        """
        # check for duplicate linknames although this should never happen
        # because we check for duplicate files before parsing, but you'll
        # never know ...
        try:
            for linkname, node in output_nodes:
                self.out(linkname, node)
            return 0
        except exceptions.ModificationNotAllowed:
            return self.exit_codes.ERRNO_DUPLICATE_LINKNAME
