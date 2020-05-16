# -*- coding: utf-8 -*-


"""
Test suite for POTCAR related utilities
"""


import pytest
import string

from pymatgen.core import periodic_table

from aiida_cusp.utils import PotcarParser


# ever growing list of sample cases testing the regular expression used
# to remove certain chars from the contents. every case that lead to a bug
# should be added here!
@pytest.mark.parametrize('sample_input,expected_string',
[   # noqa: E128
    ("^", ""),
    ("^^", ""),
    ("^^^", ""),
    ("^^^^", ""),
    ("^sample", "sample"),
    ("sample^", "sample"),
    ("^^^sample", "sample"),
    ("sample^^^", "sample"),
    ("s^a^m^p^l^e", "sample"),
    ("sa^^m^^^p^le", "sample"),
])
def test_remove_regex(sample_input, expected_string):
    remove_regex = PotcarParser._RE_REMOVE_CHARS
    cleared_string = remove_regex.sub(r"", sample_input)
    assert cleared_string == expected_string


# ever growing list of sample cases testing the regular expression used
# to condense certain consecutive chars (i.e. whitespaces) in inputs. every
# case that lead to a bug should be added here!
@pytest.mark.parametrize('sample_input,expected_string',
[   # noqa: E128
    # simple empty space
    (" ", " "),
    ("  ", " "),
    ("   ", " "),
    ("    ", " "),
    (" sample", " sample"),
    ("   sample", " sample"),
    ("sample ", "sample "),
    ("sample   ", "sample "),
    ("s  a   m p l    e", "s a m p l e"),
    # tabspace
    ("\t", " "),
    ("\t\t", " "),
    ("\t\t\t", " "),
    ("\t\t\t\t", " "),
    ("\tsample", " sample"),
    ("\t\t\tsample", " sample"),
    ("sample\t", "sample "),
    ("sample\t\t\t", "sample "),
    ("s\t\ta\t\t\tm\tp\tl\t\t\t\te", "s a m p l e"),
    # mixed empty and tabspaces
    ("s\t \ta\t  \t\tm\tp\t  l \t \t\t \te", "s a m p l e"),
])
def test_reduced_regex(sample_input, expected_string):
    remove_regex = PotcarParser._RE_CONDENSE_CHARS
    reduced_string = remove_regex.sub(r" ", sample_input)
    assert reduced_string == expected_string


# ever growing list of sample case testing the header machting regular
# expression. expected match should be everything encompassed by %HSTRT%
# and %HEND%. every case that lead to a bug should be added here!
@pytest.mark.parametrize('sample_input,expected_match',
[   # noqa: E128
    # check matching is working independent of surrounding contents
    ("before head %HSTRT% header %HEND%", " header "),
    ("%HSTRT% header %HEND% after head", " header "),
    ("before head %HSTRT% header %HEND% after head", " header "),
    ("before header\n%HSTRT% header %HEND%\nafter header", " header "),
    ("%HSTRT%\nhe\nad\ner\n%HEND%", "\nhe\nad\ner\n"),
    ("before header%HSTRT%header%HEND%after header", "header"),
    # actually check that the regex is able to match **everything**
    ("%HSTRT%" + string.printable + "%HEND%", string.printable),
])
def test_header_regex(sample_input, expected_match):
    header_regex = PotcarParser._RE_HEADER
    # replace placeholder with actual start / stop identifiers used by VASP
    head_start_ident = "parameters from PSCTR are:"
    head_end_ident = "END of PSCTR-controll parameters"
    sample_input = sample_input.replace("%HSTRT%", head_start_ident)
    sample_input = sample_input.replace("%HEND%", head_end_ident)
    matched_header = header_regex.search(sample_input).group(1)
    assert matched_header == expected_match


# define different possible ocurrences of the VRHFIN line inside the
# potential file header and test matching again all element strings available
# from the pymatgen.core.periodic_table module. (%E% will be replaced by the
# element name during the test)
@pytest.mark.parametrize('sample_input',
[   # noqa: E128
    (string.printable + "VRHFIN=%E%:" + string.printable),
    (string.printable + " VRHFIN=%E%:" + string.printable),
    (string.printable + "   VRHFIN=%E%:" + string.printable),
    (string.printable + "VRHFIN=%E% :" + string.printable),
    (string.printable + "VRHFIN=%E%   :" + string.printable),
    (string.printable + "VRHFIN =%E%:" + string.printable),
    (string.printable + "VRHFIN    =%E%:" + string.printable),
    (string.printable + "VRHFIN = %E%:" + string.printable),
    (string.printable + "VRHFIN =   %E%:" + string.printable),
    (string.printable + "VRHFIN =%E% :" + string.printable),
    (string.printable + "VRHFIN =%E%   :" + string.printable),
    (string.printable + "VRHFIN =  %E%  :" + string.printable),
])
def test_element_regex(sample_input):
    element_regex = PotcarParser._RE_ELEMENT
    element_list = [e.name for e in periodic_table.Element]
    for wanted_element in element_list:
        vrhfin_line = sample_input.replace("%E%", wanted_element)
        parsed_element = element_regex.search(vrhfin_line).group(1)
        assert parsed_element == wanted_element


# the regex for date matching is not supposed to match a valid date but rather
# match for strings that **look like** a valid date used by VASP, however, it
# should certainly not match anything that looks like a electron configuration,
# i.e. s2p6, ...
@pytest.mark.parametrize('sample_input,expected_match',
[   # noqa: E128
    # every three letter structure surrounded by at least a single digit
    # is valid
    (string.printable + " 99Zyx99 " + string.printable, "99Zyx99"),
    (string.printable + " 99Zyx9999 " + string.printable, "99Zyx9999"),
    (string.printable + " 9Zyx9999 " + string.printable, "9Zyx9999"),
    (string.printable + " 9Zyx9 " + string.printable, "9Zyx9"),
    (string.printable + " 99999Zyx99999 " + string.printable, "99999Zyx99999"),
    # everything else should produce not match to avoid false positive matches
    # for electron configurations
    (string.printable + " Zyx9 " + string.printable, None),
    (string.printable + " 9Zyx " + string.printable, None),
    (string.printable + " 9Zy9 " + string.printable, None),
    (string.printable + " Zy9 " + string.printable, None),
    (string.printable + " 9Zb " + string.printable, None),
    (string.printable + " 9Z9 " + string.printable, None),
    (string.printable + " Z9 " + string.printable, None),
    (string.printable + " z9y9 " + string.printable, None),
    (string.printable + " z99y999 " + string.printable, None),
    (string.printable + " z9y9x9 " + string.printable, None),
])
def test_date_regex(sample_input, expected_match):
    date_regex = PotcarParser._RE_DATE
    parsed_date = date_regex.search(sample_input)
    if expected_match is None:
        assert parsed_date is None
    else:
        assert parsed_date.group(1) == expected_match


# regression testing for the PotcarParser when parsing the contents of a
# *real* potential file
def test_potcar_parser_class(interactive_potcar_file):
    # fictitious potential file header
    potential_head = (
        "Functional  99Mar9999 10.0000000000000000\n"
        "parameters from PSCTR are:\n"
        "  VRHFIN =Ee: d10 p1\n"
        "  LEXCH  = PE\n"
        "  EATOM  =  1000.0000 eV,  100.0000 Ry\n"
        "\n"
        "  TITEL  = PAW_PBE Cu 05Jan2001\n"
        "  LULTRA =        F    use ultrasoft PP ?\n"
        "  IUNSCR =        1    unscreen: 0-lin 1-nonlin 2-no\n"
        "END of PSCTR-controll parameters\n"
        "numerical potential contents following the header"
    )
    interactive_potcar_file.open("POTCAR")
    interactive_potcar_file.write(potential_head)
    path_to_potcar = interactive_potcar_file.filepath
    parsed = PotcarParser(path_to_potcar)
    assert parsed.element == "Ee"
    assert parsed.version == 99990399


# test application of implemented quirks
@pytest.mark.parametrize('quirk,expected_attributes',
[   # noqa: E128
    ('PAW_PBE Xe 07Sep2000', {
        'element': 'Xe',
    })
    ('PAW Xe 07Sep2000', {
        'element': 'Xe',
    })
    ('PAW_PBE Zr_sv 04Jan2005', {
        'element': 'Zr',
    })
    ('US Bi', {
        'element': 'Bi',
    })
    ('PAW Bi_pv 29Jan08', {
        'version': 20080129,
    })
    ('PAW Ga_d_GW 10Nov06', {
        'version': 20061110,
    })
    ('PAW_PBE Bi_pv 29Jan08', {
        'version': 20080129,
    })
    ('PAW_PBE Bi_pv 29Jan08 GW ready', {
        'version': 20080129,
    })
    ('PAW_PBE Ga_sv_GW 03Mar08', {
        'version': 20080303,
    })
])
def test_quirks_are_applied(interactive_potcar_file, quirk,
                            expected_attributes):
    # construct potential with appropriate title line to trigger the
    # quirk execution
    potential_contents = "\n".join([
        "{} VRHFIN =Xy: s100p100d100".format(quirk),
        "9.999999999999999999999",
        "parameters from PSCTR are:",
        "VRHFIN =Xy: s100p100d100",
        "TITEL  = {}".format(quirk),
        "END of PSCTR-controll parameters",
        "numerical potential contents following the header",
    ])
    interactive_potcar_file.open("POTCAR")
    interactive_potcar_file.write(potential_contents)
    path_to_potcar = interactive_potcar_file.filepath
    parsed_potential = PotcarParser(path_to_potcar)
    for (attr_name, expected_attr_val) in expected_attributes.items():
        assert getattr(parsed_potential, attr_name) == expected_attr_val
