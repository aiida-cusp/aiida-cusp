# -*- coding: utf-8 -*-


"""
Utility module implementing several methods for parsing and interacting
with VASP potential files.
"""


import re
import hashlib
import warnings


# FIXME: version matching will fail for LDA potentials As_NC2 and Ga_NC2
#        because of a malformed title line. No need to fix until someone
#        really needs it
# FIXME: possibly switch from title line identifiers to a more robust
#        identifier for the quirk mapping
# FIXME: move custom exceptions to a central module


class PotcarParsingError(Exception):
    """Exception raised by the PotcarParser class."""
    pass


class PotcarParser(object):
    """
    Parsing library for VASP POTCAR files

    :param path_to_potcar_file: path to a VASP POTCAR file
    :type path_to_potcar_file: pathlib.Path
    """

    # only search for files named POTCAR
    _POTCAR_FILENAME = "POTCAR"

    # quirks to correct for common errors in potential files. every entry
    # comprises the title line of the affected potential and one or more
    # parameter updates
    _QUIRKS = {
        'PAW_PBE Xe 07Sep2000': [
            lambda self: setattr(self, 'element', 'Xe'),
        ],
        'PAW Xe 07Sep2000': [
            lambda self: setattr(self, 'element', 'Xe'),
        ],
        'PAW_PBE Zr_sv 04Jan2005': [
            lambda self: setattr(self, 'element', 'Zr'),
        ],
        'US Bi': [
            lambda self: setattr(self, 'element', 'Bi'),
        ],
        'PAW Bi_pv 29Jan08': [
            lambda self: setattr(self, 'version', 20080129),
        ],
        'PAW Ga_d_GW 10Nov06': [
            lambda self: setattr(self, 'version', 20061110),
        ],
        'PAW_PBE Bi_pv 29Jan08': [
            lambda self: setattr(self, 'version', 20080129),
        ],
        'PAW_PBE Bi_pv 29Jan08 GW ready': [
            lambda self: setattr(self, 'version', 20080129),
        ],
        'PAW_PBE Ga_sv_GW 03Mar08': [
            lambda self: setattr(self, 'version', 20080303),
        ],
    }

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

    # map functionals contained in archive file names to internal string
    _FUNCTIONAL_MAP = {
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

    # regular expressions used for parsing
    # match ^ and consecutive whitespaces (reduce potcar content)
    _RE_REDUCE_CONTENT = re.compile(r"[\^ \t]+")
    # header
    _RE_HEADER = re.compile(r"(?i)(^[\s\S]+)(?:end of psctr)")
    # element
    _RE_ELEMENT = re.compile(r"(?i)(?<=VRHFIN)(?:\s*=\s*)([a-z]+)(?=\s*\:)")
    # creation date
    _RE_DATE = re.compile(r"(?i)([0-9]+[a-z]{3,}[0-9]+)")

    def __init__(self, path_to_potcar_file):
        self.path = path_to_potcar_file
        self.contents = self.load_reduced_contents()
        self.hash = self.hash_contents()
        self.head = self.potential_header()
        self.element = self.potential_element()
        self.version = self.potential_version()
        self.apply_quirks()
# TODO: Should be determined from the path. Decide if this should be done
#       within this parsing library or somewhere else
#       self.name =
#       self.functional =

    def apply_quirks(self):
        """
        Update invalid and erroneous parameters running the stored quirks
        """
        titleline = re.search(r"^([\s\S]*?)(?=\n)", self.head).group(1).strip()
        for apply_quirk in self._QUIRKS.get(titleline, [lambda _:_]):
            apply_quirk(self)

    def load_reduced_contents(self):
        """
        Load POTCAR file contents and return a reduced version without
        consecutive whitespaces and occasionally occuring '^' chars

        :return: returns the reduced contents of the potcar file
        :rtype: str
        """
        with open(self.path, 'rU') as potcar:
            content = potcar.read()
        reduced_content = self._RE_REDUCE_CONTENT.sub(r" ", content)
        return reduced_content

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

    def potential_header(self):
        """
        Extract header section from potential contents

        :return: string containing the potential header
        :rtype: str
        :raises PotcarParsingError: if regex returns with no match
        """
        regex_match = self._RE_HEADER.search(self.contents)
        if regex_match:
            return regex_match.group(1)
        else:
            raise PotcarParsingError("Error parsing the header for file "
                                     "'{}'. Regex match returned '{}'! "
                                     .format(self.path, regex_match))

    def potential_element(self):
        """
        Extract the element stored with the potential

        :return: string containing the element name
        :rtype: str
        :raises PotcarParsingError: if regex returns with no match
        """
        regex_match = self._RE_ELEMENT.search(self.contents)
        if regex_match:
            return regex_match.group(1)
        else:
            raise PotcarParsingError("Error parsing the element for file "
                                     "'{}'. Regex match returned '{}'!"
                                     .format(self.path, regex_match))

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
            # likely a H_AE Coulomb potential if element is H ...
            if self.element == 'H':
                warnings.warn("Unable to parse creation date for file '{}' "
                              "but element is 'H'. Assuming Coulomb potential "
                              "('H_AE') and setting version to '99999999'"
                              .format(self.path))
                return 99999999
            # ... fail otherwise
            else:
                raise PotcarParsingError("Error parsing creation date for "
                                         "file '{}'. Regex match returned "
                                         "'{}'!"
                                         .format(self.path, regex_match))
