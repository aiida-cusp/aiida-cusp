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
                             VaspWavecarData, VaspChgcarData, VaspGenericData)
from aiida_cusp.utils.defaults import PluginDefaults, VaspDefaults
from aiida_cusp.utils.custodian import custodian_job_suffixes


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
        for (fpath, fstem, suffix) in self.files_to_parse:
            parser = self.parsing_hook(fstem)
            try:
                self.logger.debug(f"[{__name__}] parse(): running parsing  "
                                  f"hook '{parser}' on file '{fpath}'")
                parsed = getattr(self, parser)(fpath, fstem, suffix)
            except AttributeError:
                self.logger.debug(f"[{__name__}] parse(): found no parsing "
                                  f"hook for file '{fpath}' falling back to "
                                  f"generic parsing hook")
                parsed = self.parse_generic(fpath, fstem, suffix)
            parsed_results.append(parsed)
        exit_code = self.register_output_nodes(parsed_results)
        return exit_code

    def normalized_filename(self, filename):
        """
        Return a normalized version of the filename, i.e. lower case and
        replace all non-alphanumeric characters with underscores, as such
        character are not allowed in output linknames
        """
        return re.sub(r"[^a-z0-9_]", "_", filename.lower())

    def parsing_hook(self, filename):
        return "parse_{}".format(self.normalized_filename(filename))

    def linkname(self, filepath, filename, filesuffix):
        """
        Generate the output linkname under which the file at the given
        location will be available based on the filename and a possibly
        connected file suffix (i.e. from custodian jobs)
        """
        neb_folder = re.match(r"^[0-9]{2}$", str(filepath.parent.name))
        # instead of dots we separate nested levels of the output namespace
        # by adding double underscores as separators which are later
        # translated into the proper nesting by AiiDA
        #
        # always treat the first character of the suffix as the delimiter
        # and do not add it to the linkname
        suffix_namespace = f"{filesuffix[1:]}__" if filesuffix else ""
        if neb_folder:
            neb_prefix_name = PluginDefaults.NEB_NODE_PREFIX
            neb_folder_name = neb_folder.group()
            neb_namespace = f"{neb_prefix_name}{neb_folder_name}__"
        else:
            neb_namespace = ""
        filename = self.normalized_filename(filename)
        # create linkname by concatenating all namespaces with the filename
        return f"{suffix_namespace}{neb_namespace}{filename}"

    def build_parsing_list(self):
        """
        Setup a list of files to be parsed based on the parsing list supplied
        by the parser's parse_file option
        """
        path_to_tmpfolder = pathlib.Path(self.tmpfolder).absolute()
        # list of the form [..., (file_name, file_stem, suffix), ...)]
        parsing_triplets = self.build_parsing_triplets()
        self.logger.debug(f"[{__name__}] build_parsing_list(): "
                          f"created parsing triplets: {parsing_triplets}")
        self.files_to_parse = []
        for name, stem, suffix in parsing_triplets:
            matching_files = path_to_tmpfolder.rglob(name)
            for matched_file_path in matching_files:
                filepath = matched_file_path.resolve()
                fullname = filepath.name
                filestem = fullname[:-len(suffix)] if suffix else fullname
                if not filepath.is_file():
                    self.logger.info(f"skipping over folder {filepath}")
                    continue
                if VaspDefaults.FNAMES['potcar'] in fullname:
                    self.logger.warning(f"encountered retrieved POTCAR file "
                                        f"at {filepath} while processing the "
                                        f"files marked for parsing. REFUSING "
                                        f"TO PARSE THIS FILE!")
                    continue
                if any(f[0] == filepath for f in self.files_to_parse):
                    self.logger.warning(f"found duplicate file {fullname} "
                                        f"at {filepath} which was already "
                                        f"added to the parsing list! THIS "
                                        f"FILE WILL BE IGNORED!")
                    continue
                self.logger.debug(f"[{__name__}] build_parsing_list(): "
                                  f"extracted properties for file "
                                  f"{matched_file_path}\n"
                                  f"  filepath = {filepath}\n"
                                  f"  fullname = {fullname}\n"
                                  f"  filestem = {filestem}\n"
                                  f"  suffix   = {suffix}")
                self.files_to_parse.append((filepath, filestem, suffix))
        self.logger.debug(f"[{__name__}] build_parsing_list(): "
                          f"created parse lust {self.files_to_parse}")
        # return error there were no files found to parse
        if not self.files_to_parse and self.fail_on_empty_list:
            exit_code = self.exit_codes.ERRNO_PARSING_LIST_EMPTY
        else:
            exit_code = None
        self.logger.debug(f"[{__name__}] build_parsing_list(): "
                          f"exit code = {exit_code}")
        return exit_code

    def build_parsing_triplets(self):
        """
        Combine the defined list of files to be parsed with the given
        suffixes provided by connected custodian jobs
        """
        suffixes = self.get_custodian_suffixes()
        parsing_triplets = []
        for name_or_wildcard in self.parsing_list:
            triplets = []
            for suffix in suffixes:
                # match files for all defined suffixes, i.e. extend each
                # filename with every possible suffix and add it to the
                # parsing triplets list
                file_name = f"{name_or_wildcard}{suffix}"
                file_stem = name_or_wildcard
                triplets.append((file_name, file_stem, suffix))
                # however, if a filename was defined including the suffix,
                # i.e. a suffix that was actually used by a job, we'll only
                # match for that very specific file (ignoring other suffixes)
                if suffix and name_or_wildcard.endswith(suffix):
                    file_name = name_or_wildcard
                    file_stem = name_or_wildcard[:-len(suffix)]
                    triplets = [(file_name, file_stem, suffix)]
                    break
            parsing_triplets.extend(triplets)
        return self.remove_duplicates(parsing_triplets)

    def get_custodian_suffixes(self):
        """
        Find and return any suffix possibly defined by a Custodian
        job that was connected to the calling calculation
        """
        from aiida.common.exceptions import NotExistentAttributeError
        # altough the namespace is present on the process node it is not
        # transferred to the calcjobnode if no values were defined
        try:
            custodian_jobs = dict(self.node.inputs.custodian.get('jobs', {}))
        except NotExistentAttributeError as exception:
            self.logger.debug(f"[{__name__}] get_custodian_suffixes(): "
                              f"unable to detect any custodian settings "
                              f"among the CalcJobNode inputs, recieved "
                              f"'{type(exception)}'. continue with "
                              f"empty joblist")
            custodian_jobs = {}
        used_suffixes = custodian_job_suffixes(custodian_jobs)
        self.logger.debug(f"[{__name__}] build_parsing_triplets(): "
                          f"connected custodian jobs: {custodian_jobs} "
                          f"introduced suffixes: {used_suffixes}")
        return used_suffixes

    def remove_duplicates(self, parsing_triplets):
        """
        Go through all triplets and remove any duplicate filenames to
        avoid parsing the same file multiple times
        """
        seen_file_names = []
        unique_triplets = []
        for triplet in parsing_triplets:
            # filter the list based on the actual filename which will be
            # used for globbing later
            if triplet[0] not in seen_file_names:
                unique_triplets.append(triplet)
                seen_file_names.append(triplet[0])
        return unique_triplets

    def verify_and_set_parser_settings(self):
        """
        Fail the parsing process if the parsin list if empty meaning no
        files will be parsed from the retrieved folder
        """
        parse_default = ['CONTCAR', 'vasprun.xml', 'OUTCAR']
        self.logger.debug(f"[{__name__}] verify_and_set_parser_settings(): "
                          f"default files to be parsed {parse_default}")
        settings = dict(self.settings)
        self.logger.debug(f"[{__name__}] verify_and_set_parser_settings(): "
                          f"using parser settings {settings}")
        self.fail_on_empty_list = settings.pop('fail_on_missing_files', False)
        self.parsing_list = settings.pop('parse_files', parse_default)
        if settings:
            exit_code = self.exit_codes.ERRNO_UNKNOWN_PARSER_SETTING
        else:
            exit_code = None
        self.logger.debug(f"[{__name__}] verify_and_set_parser_settings(): "
                          f"exit code = {exit_code}")
        return exit_code

    def parse_vasprun_xml(self, filepath, filename, filesuffix):
        """
        Parsing hook triggered files of type vasprun.xml
        """
        node = VaspVasprunData(file=filepath)
        linkname = self.linkname(filepath, filename, filesuffix)
        return (linkname, node)

    def parse_outcar(self, filepath, filename, filesuffix):
        """
        Parsing hook triggered files of type OUTCAR
        """
        node = VaspOutcarData(file=filepath)
        linkname = self.linkname(filepath, filename, filesuffix)
        return (linkname, node)

    def parse_contcar(self, filepath, filename, filesuffix):
        """
        Parsing hook triggered for files of type CONTCAR
        """
        contcar = Poscar.from_file(filepath, check_for_POTCAR=True,
                                   read_velocities=True)
        node = VaspContcarData(structure=contcar)
        linkname = self.linkname(filepath, filename, filesuffix)
        return (linkname, node)

    def parse_chgcar(self, filepath, filename, filesuffix):
        """
        Parsing hook triggered for files of type CHGCAR
        """
        node = VaspChgcarData(file=filepath)
        linkname = self.linkname(filepath, filename, filesuffix)
        return (linkname, node)

    def parse_wavecar(self, filepath, filename, filesuffix):
        """
        Parsing hook triggered for files of type WAVECAR
        """
        node = VaspWavecarData(file=filepath)
        linkname = self.linkname(filepath, filename, filesuffix)
        return (linkname, node)

    def parse_generic(self, filepath, filename, filesuffix):
        """
        Generic parsing hook trigger for all files not featuring a specific
        parsing hook
        """
        node = VaspGenericData(file=filepath)
        linkname = self.linkname(filepath, filename, filesuffix)
        return (linkname, node)
