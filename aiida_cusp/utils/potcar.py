# -*- coding: utf-8 -*-


"""
Utility module implementing several methods for parsing and interacting
with VASP potential files.
"""


import re
import hashlib
import warnings

from aiida_cusp.utils.defaults import VaspDefaults
from aiida_cusp.utils.exceptions import PotcarParserError, PotcarPathError


class PotcarParser(object):
    """
    Minimalistic parsing library for VASP POTCAR files.

    Only tries to parse the basic potential identifiers from the file,
    i.e. the potential version and the associated element. Does not
    perform any checks on the validity of the parsed results but only raises
    if no match was retrieved at all.

    :param path_to_potcar_file: path to a VASP POTCAR file
    :type path_to_potcar_file: pathlib.Path
    :param name: name of the potential (i.e. Li, Li_sv, ...)
    :type name: str
    :param functional: functional of the potential, i.e. one of lda_us,
        lda, lda_52, lda_54, pbe, pbe_52, pbe_54, pw91 or pw91_us
    :type functional: str
    """

    # quirks to correct for common errors in potential files. every entry
    # comprises the title line of the affected potential and one or more
    # parameter updates
    _QUIRKS = {
        # potUSPP_LDA/Bi/POTCAR
        'lda_us__Bi__US_Bi': [
            lambda self: setattr(self, 'element', 'Bi'),
        ],
        # potUSPP_GGA/Bi/POTCAR
        'pw91_us__Bi__US_Bi': [
            lambda self: setattr(self, 'element', 'Bi'),
        ],
        # potUSPP_LDA/Xe/POTCAR
        'lda_us__Xe__US_Xe': [
            lambda self: setattr(self, 'element', 'Xe'),
        ],
        # potpaw_LDA/Xe/POTCAR
        'lda__Xe__PAW_Xe_07Sep2000': [
            lambda self: setattr(self, 'element', 'Xe'),
        ],
        # potpaw_PBE/Xe/POTCAR
        'pbe__Xe__PAW_PBE_Xe_07Sep2000': [
            lambda self: setattr(self, 'element', 'Xe'),
        ],
        # potpaw_GGA/Xe/POTCAR
        'pw91__Xe__PAW_GGA_Xe_07Sep2000': [
            lambda self: setattr(self, 'element', 'Xe'),
        ],
        # potUSPP_GGA/Xe/POTCAR
        'pw91_us__Xe__US_Xe': [
            lambda self: setattr(self, 'element', 'Xe'),
        ],
        # potpaw_PBE.52/Zr_sv/POTCAR
        'pbe_52__Zr_sv__PAW_PBE_Zr_sv_04Jan2005': [
            lambda self: setattr(self, 'element', 'Zr'),
        ],
        # potpaw_LDA/Bi_pv/POTCAR
        'lda__Bi_pv__PAW_Bi_pv_29Jan08': [
            lambda self: setattr(self, 'version', 20080129),
        ],
        # potpaw_LDA/Ga_d_GW.old/POTCAR
        'lda__Ga_d_GW.old__PAW_Ga_d_GW_10Nov06': [
            lambda self: setattr(self, 'version', 20061110),
        ],
        # potpaw_PBE/Bi_pv/POTCAR
        'pbe__Bi_pv__PAW_PBE_Bi_pv_29Jan08_GW_ready': [
            lambda self: setattr(self, 'version', 20080129),
        ],
        # potpaw_PBE/Ga_sv_GW/POTCAR
        'pbe__Ga_sv_GW__PAW_PBE_Ga_sv_GW_03Mar08': [
            lambda self: setattr(self, 'version', 20080303),
        ],
    }  # _QUIRKS

    # table converting month strings to numerical representation (also
    # accounts for some inconsistencies among potential files, i.e. using
    # german 'okt' instead of english 'oct' in some places
    _MONTH_TO_NUM_MAP = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr': 4,
        'may': 5,
        'jun': 6,
        'jul': 7,
        'aug': 8,
        'sep': 9,
        'oct': 10, 'okt': 10,
        'nov': 11,
        'dec': 12, 'dez': 12,
    }

    # regular expressions used for parsing
    # remove and codense to transform contents in well defined state
    _RE_REMOVE_CHARS = re.compile(r"[\^]")  # replace with ""
    _RE_CONDENSE_CHARS = re.compile(r"[ \t]+")  # replace with " "
    # header
    _RE_HEADER = re.compile(r"(?i)(?<=psctr are\:)([\s\S]+)(?=end of psctr)")
    # title
    _RE_TITLE = re.compile(r"^([\s\S]*?)(?=\n)")
    # element
    _RE_ELEMENT = re.compile(r"(?i)(?<=VRHFIN)(?:\s*=\s*)([a-z]+)(?=\s*\:)")
    # creation date
    _RE_DATE = re.compile(r"(?i)([0-9]+[a-z]{3,}[0-9]+)")

    def __init__(self, path_to_potcar_file, name=None, functional=None):
        self.name = name
        self.functional = functional
        self.path = path_to_potcar_file
        self.contents = self.load_reduced_contents()
        self.hash = self.hash_contents()
        self.header = self.potential_header()
        self.title = self.potential_title()
        self.element = self.potential_element()
        self.version = self.potential_version()
        # correct (known) erroneous values
        self.apply_quirks()
        # run a short sanity check on the parsed parameters **after** applying
        # the quirks!
        self.verify_parsed()

    def apply_quirks(self):
        """
        Update invalid and erroneous parameters running the stored quirks
        """
        # build quirk identifier from functional, name and parsed potential
        # file title
        title = "_".join(self.title.strip().split())
        quirk_ident = "__".join([self.functional, self.name, title])
        for apply_quirk in self._QUIRKS.get(quirk_ident, [lambda _:_]):
            apply_quirk(self)

    def verify_parsed(self):
        """
        Check if the parsed contents do make sense.
        """
        if self.header is None:
            raise PotcarParserError("Error parsing the header for file "
                                    "'{}'!".format(self.path))
        if self.element is None:
            raise PotcarParserError("Error parsing the element for file "
                                    "'{}'!".format(self.path))
        if self.version is None:
            raise PotcarParserError("Error parsing creation date for file "
                                    "'{}'!".format(self.path))

    def load_reduced_contents(self):
        """
        Load POTCAR file contents and return a reduced version without
        consecutive whitespaces and occasionally occuring '^' chars

        :return: returns the reduced contents of the potcar file
        :rtype: str
        """
        raw_content = self.load_potential_contents()
        reduced_content = raw_content
        # remove all unwanted chars from the contents
        reduced_content = self._RE_REMOVE_CHARS.sub(r"", reduced_content)
        reduced_content = self._RE_CONDENSE_CHARS.sub(r" ", reduced_content)
        return reduced_content

    def load_potential_contents(self):
        """
        Load POTCAR file contents.

        :returns: the contents of the potcar file
        :rtype: str
        """
        with open(self.path, 'r') as potcar:
            raw_content = potcar.read()
        return raw_content

    def hash_contents(self):
        """
        Hash potential contents using secure hashing.

        Calculates the hash based on the reduced instead of the full potential
        contents to avoid potentials being assumed as different if whitespaces
        differ.

        :return: return sha256 hash for potential contents
        :rtype: str
        """
        return hashlib.sha256(self.contents.encode()).hexdigest()

    def potential_title(self):
        """
        Extract the potential title (i.e. the first line of the file)
        """
        regex_match = self._RE_TITLE.match(self.contents)
        if regex_match:
            return regex_match.group(1)
        else:  # raise because we use the title only internally
            raise PotcarParserError("Error parsing title line for file '{}'."
                                    "Match returned '{}'."
                                    .format(self.path, regex_match))

    def potential_header(self):
        """
        Extract header section from potential contents

        :return: string containing the potential header
        :rtype: str
        :raises PotcarParserError: if regex returns with no match
        """
        regex_match = self._RE_HEADER.search(self.contents)
        if regex_match:
            return regex_match.group(1)
        else:
            return None

    def potential_element(self):
        """
        Extract the element stored with the potential

        :return: string containing the element name
        :rtype: str
        :raises PotcarParserError: if regex returns with no match
        """
        regex_match = self._RE_ELEMENT.search(self.contents)
        if regex_match:
            return regex_match.group(1)
        else:
            return None

    def potential_version(self):
        """
        Extract creation date from the potential header

        :return: integer representation of the potential creation date
        :rtype: int
        """
        regex_match = self._RE_DATE.search(self.contents)
        if regex_match:
            datestr = regex_match.group(1)
            # assign content strings to numerical values
            day, year = list(map(int, re.findall(r"[0-9]+", datestr)))
            month_str = re.search(r"(?i)([a-z]+)", datestr).group(0)
            month = self._MONTH_TO_NUM_MAP[month_str.lower()]
            # build the version string of the form YYYYMMDD (possibly wrong
            # values due to format issues will be corrected later!)
            version = int("{:>04d}{:>02d}{:>02d}".format(year, month, day))
            return version
        else:
            # exceptions for some potential fils which (on purpose?) do not
            # contain any creation dates (i.e. H_AE, US and NC potentials).
            # set version to the lowest possible value (i.e. 10000101) such
            # newer potentials (which then may contain a version) are
            # identifiable as **newer** versions
            # exception for version-less H_AE potentials
            if self.element == 'H':
                warnings.warn("Unable to parse creation date for file '{}' "
                              "but element is 'H'. Assuming Coulomb potential "
                              "('H_AE') and setting version to '10000101'"
                              .format(self.path))
                return 10000101
            # exception for version-less ultra-soft potentials
            if 'US' in self.title:
                warnings.warn("Unable to parse creation date for file '{}' "
                              "but title line contains 'US'. Assuming "
                              "ultra-soft potential and setting version to "
                              "'10000101'".format(self.path))
                return 10000101
            # exception for version-less norm-conserving potentials
            if 'NC' in self.title:
                warnings.warn("Unable to parse creation date for file '{}' "
                              "but title line contains 'NC'. Assuming "
                              "norm-conserving potential and setting version "
                              "to '10000101'".format(self.path))
                return 10000101
            # ... fail otherwise
            else:
                return None


class PotcarPathParser(object):
    """
    Utility class for parsing POTCAR file paths.

    Assumes a POTCAR file path of the form /path/[FUNCTIONAL]/[NAME]/POTCAR
    with [FUNCTIONAL] containing the archive name of the potential libraries
    as shipped by VASP, i.e. one of potuspp_lda, potpaw_lda, potpaw_lda.52,
    potpaw_lda.54, potpaw_pbe, potpaw_pbe.52, potpaw_pbe.54, potuspp_gga or
    potpaw_gga. Tries to determine the potential's functional and name from
    the given path and raises an exception if this fails.

    :param potcar_file_path: file path pointing to a VASP pseudo-potential
    :type potcar_file_path: pathlib.Path
    :raises PotcarPathError: if the path does not point to a POTCAR file or
        if the path does not contain a valid archive name to identify the
        corresponding functional
    """
    def __init__(self, potcar_file_path):
        # first check if the given path is a file and if the file name is
        # POTCAR
        self.validate_path_is_potcar_file(potcar_file_path)
        self.functional = self.parse_functional(potcar_file_path)
        self.name = self.parse_name(potcar_file_path)

    def validate_path_is_potcar_file(self, path):
        """
        Check if the given path points to a file of type POTCAR .

        :param path: file path pointing to a VASP pseudo-potential
        :type path: pathlib.Path
        :raises PotcarPathError: if the parser cannot extract the functional
            from the path or if the path does not point to a potential
        """
        if not path.is_file():
            raise PotcarPathError("Path '{}' does not point to a file"
                                  .format(str(path.absolute())))
        if not path.name == VaspDefaults.FNAMES['potcar']:
            raise PotcarPathError("Potcar file must be named 'POTCAR'")

    def parse_functional(self, path):
        """
        Parse the potential's functional type from the given path.

        Search the given path for functional identifiers corresponding to the
        archive names chosen by the pseudo-potential libraries shipped with
        VASP.

        :param path: file path pointing to a VASP pseudo-potential
        :type path: pathlib.Path
        :returns: plugin internal functional identifier
        :rtype: str
        :raises PotcarPathError: if no valid functional identifier can be
            found in the given path.
        """
        # regex for matching pseudopotential functional folder
        regex = r"(?i)(pot(?:uspp|paw)\_(?:lda|pbe|gga)(?:\.52|\.54)*)"
        functional_match = re.search(regex, str(path))
        if functional_match is None:
            raise PotcarPathError("Unable to parse functional identifier "
                                  "(i.e. potuspp_lda, potpaw_lda, "
                                  "potpaw_lda.52, potpaw_lda.54, potpaw_pbe, "
                                  "potpaw_pbe.52, potpaw_pbe.54, potuspp_gga "
                                  "or potpaw_gga from the given path '{}'"
                                  .format(str(path.absolute())))
        return VaspDefaults.FUNCTIONAL_MAP[functional_match.group(0)]

    def parse_name(self, path):
        """
        Parse the unique functional name from the path.

        Simply returns the name of the parent folder containing the POTCAR
        file.

        :param path: file path pointing to a VASP pseudo-potential
        :type path: pathlib.Path
        :returns: the pseudo-potential's unique name
        :rtype: str
        """
        return str(path.parent.name)
