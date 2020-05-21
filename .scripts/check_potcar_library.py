#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Helpful utility to check and extend the list of available quirks if a new
collection of potentials is published.

Runs the PotcarParser on all POTCAR files found in the defined POTCAR-folder.
After parsing, contents are checked for validity and - if found invalid - all
the required information to implement a new quirk for the offending potential
is printed to the screen.
"""


import pathlib

from pymatgen.core import periodic_table

from aiida_cusp.utils.potcar import PotcarParser
from aiida_cusp.utils.defaults import VaspDefaults


def contents_are_valid(potential_parser):
    """
    Defines criteria deeming the potential contents as valid or invalid.
    """
    valid = []
    # check for valid element
    elements = [e.name for e in periodic_table.Element]
    if potential_parser.element is None:
        valid.append(False)
        valid.append(False)
    else:
        # check if the parsed element is a valid element name
        elem_valid = potential_parser.element in elements
        valid.append(elem_valid)
        # captures errors like in the US Bi potentials where the potential
        # folder and title indicate Bi potential but VRHFIN is set to Pb
        elem_match = potential_parser.element in potential_parser.title
        valid.append(elem_match)
    # check for a valid version string
    if potential_parser.version is None:
        valid.append(False)
    else:
        # check for malformed version strings of the form NNABcNN which
        # lead to an invalid version string below 10000101
        vers_valid = potential_parser.version >= 10000101
        valid.append(vers_valid)
    return all(valid)


if __name__ == "__main__":
    # topfolder pointing to the potential library
    path_to_potentials = pathlib.Path('/home/andreas/my_python_stuff/'
                                      'plugin_dev/testing/potcar')
    # find all potentials and check the validity
    potcar_filepaths = path_to_potentials.rglob('POTCAR')
    for potcar_filepath in potcar_filepaths:
        # determine potential name and functional name from filepath
        name = str(potcar_filepath.parent.name)
        func = str(potcar_filepath.parent.parent.name)
        func = VaspDefaults.FUNCTIONAL_MAP[func]
        parsed = PotcarParser(potcar_filepath, name=name, functional=func)
        if not contents_are_valid(parsed):
            title = "_".join(parsed.title.strip().split())
            quirk_identifier = "{}".format("__".join([func, name, title]))
            outstr = "{}: {} {} ({})".format(parsed.path.absolute(),
                                             parsed.element, parsed.version,
                                             quirk_identifier)
            print(outstr)
