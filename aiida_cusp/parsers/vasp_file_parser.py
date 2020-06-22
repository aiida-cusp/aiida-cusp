# -*- coding: utf-8 -*-


"""
Default parser class used with the cusp pluing for parsing the results
of AiiDA managed VASP calculations
"""


import re
import pathlib
from pymatgen.io.vasp.inputs import Poscar

from aiida_cusp.parsers.parser_base import ParserBase
from aiida_cusp.data import (VaspVasprunData, VaspOutcarData, VaspContcarData,
                             VaspWavecarData, VaspChgcarData)
from aiida_cusp.utils.single_archive_data import SingleArchiveData
from aiida_cusp.utils.defaults import PluginDefaults, VaspDefaults


class VaspFileParser(ParserBase):
    """
    The VaspFileParser parsing class represents a basic parser class.
    In order to make it as flexible as possible this default parser only
    checks for the given files an adds them as SingleArchiveNodes to the
    calling calculation, giving you the full VASP experience (i.e.
    files-in --> file-out.  In particular, no special parsing actions parsing
    special values or attributes of the calculation are employed at the
    parsing level to ensure the default parser class is compatible
    with all types of VASP calculations.

    All discovered files present in the retrieve list defined by the parser
    settings will be added to the calculation with the filename as linkname
    with .suffix replaced by _suffix, i.e. the vasprun.xml would be stored
    under the vasprun_xml linkname) If files are found to be located in a
    subfolder (this is only the case for instance in NEB calculations) an
    additional namespace with linkname 'node_{foldername}' under which the
    files will be added.

    Accepted options set by the metadata.options.parser_settings:

    parse_files (list) -- A list of files that will be parsed from the
        retrieved folder and added as nodes to the calculation output. Note
        that wilcards like 'W*.tmp' or even '*' are allowed! If not list is
        defined, by default, only the OUTCAR, CONTCAR and vasprun.xml files
        are added.
    """

    def parse(self, **kwargs):
        # check folders and set file list
        exit_code = super(VaspFileParser, self).parse(**kwargs)
        if exit_code:
            return exit_code
        # setup and verify the given parser settings
        exit_code = self.verify_and_set_parser_settings()
        if exit_code:
            return exit_code
        # generate the list of files to be parsed
        exit_code = self.build_parsing_list()
        if exit_code:
            return exit_code
        # finally parse all files on the parsing list
        parsed_results = []
        for filepath in self.files_to_parse:
            parser = self.parsing_hook(filepath)
            try:
                parsed = getattr(self, parser)(filepath)
            except AttributeError:
                parsed = self.parse_generic(filepath)
            parsed_results.append(parsed)
        # finish parsing by adding parsed results as output nodes
        exit_code = self.register_output_nodes(parsed_results)
        return exit_code

    def normalized_filename(self, filepath):
        """
        Return a normalized version of the filename, i.e. lower case and
        .suffix replace with _suffix
        """
        return str(filepath.name.lower()).replace(".", "_")

    def parsing_hook(self, filepath):
        return "parse_{}".format(self.normalized_filename(filepath))

    def linkname(self, filepath):
        """
        Generate the output linkname under which the file at the given
        location will be available
        """
        neb_folder = re.match(r"^[0-9]{2}$", str(filepath.parent.name))
        if neb_folder:
            namespace = "{}{}.".format(PluginDefaults.NEB_NODE_PREFIX,
                                       neb_folder.group())
        else:
            namespace = ""
        return "{}{}".format(namespace, self.normalized_filename(filepath))

    def build_parsing_list(self):
        """
        Setup a list of files to be parsed based on the parsing list supplied
        by the parser's parse_file option
        """
        path_to_tmpfolder = pathlib.Path(self.tmpfolder).absolute()
        self.files_to_parse = []
        for name_or_wildcard in self.parsing_list:
            filelist = list(path_to_tmpfolder.rglob(name_or_wildcard))
            # only parse files and remove possibly matching folders but
            # NEVER EVER parse a POTCAR file
            self.files_to_parse += [
                f for f in filelist if f.is_file()
                and f.name != VaspDefaults.FNAMES['potcar']
            ]
        # do not parse the same file multiple times
        self.files_to_parse = list(set(self.files_to_parse))
        if not self.files_to_parse and self.fail_on_empty_list:
            exit_code = self.exit_codes.ERRNO_PARSING_LIST_EMPTY
        else:
            exit_code = 0
        return exit_code

    def verify_and_set_parser_settings(self):
        """
        Fail the parsing process if the parsin list if empty meaning no
        files will be parsed from the retrieved folder
        """
        parse_default = ['CONTCAR', 'vasprun.xml', 'OUTCAR']
        settings = dict(self.settings)
        self.fail_on_empty_list = settings.pop('fail_on_missing_files', False)
        self.parsing_list = settings.pop('parse_files', parse_default)
        if settings:
            return self.exit_codes.ERRNO_UNKNOWN_PARSER_SETTING
        else:
            return 0

    def parse_vasprun_xml(self, filepath):
        """
        Parsing hook triggered files of type vasprun.xml
        """
        node = VaspVasprunData(file=filepath)
        linkname = self.linkname(filepath)
        return (linkname, node)

    def parse_outcar(self, filepath):
        """
        Parsing hook triggered files of type OUTCAR
        """
        node = VaspOutcarData(file=filepath)
        linkname = self.linkname(filepath)
        return (linkname, node)

    def parse_contcar(self, filepath):
        """
        Parsing hook triggered for files of type CONTCAR
        """
        contcar = Poscar.from_file(filepath, check_for_POTCAR=True,
                                   read_velocities=True)
        node = VaspContcarData(structure=contcar)
        linkname = self.linkname(filepath)
        return (linkname, node)

    def parse_chgcar(self, filepath):
        """
        Parsing hook triggered for files of type CHGCAR
        """
        node = VaspChgcarData(file=filepath)
        linkname = self.linkname(filepath)
        return (linkname, node)

    def parse_wavecar(self, filepath):
        """
        Parsing hook triggered for files of type WAVECAR
        """
        node = VaspWavecarData(file=filepath)
        linkname = self.linkname(filepath)
        return (linkname, node)

    def parse_generic(self, filepath):
        """
        Generic parsing hook trigger for all files not featuring a specific
        parsing hook
        """
        node = SingleArchiveData(file=filepath)
        linkname = self.linkname(filepath)
        return (linkname, node)
