# -*- coding: utf-8 -*-


"""
Test suite for POTCAR related utilities
"""


from aiida_cusp.utils import PotcarParser


def test_header_parsing(interactive_potcar_file):
    # fictiious potential file header
    potential_head = (
        "Functional Ee 99Mar9999 10.0000000000000000\n"
        "parameters from PSCTR are:\n"
        "  VRHFIN =Ee: d10 p1\n"
        "  LEXCH  = PE\n"
        "  EATOM  =  1000.0000 eV,  100.0000 Ry\n"
        "\n"
        "  TITEL  = PAW_PBE Cu 05Jan2001\n"
        "  LULTRA =        F    use ultrasoft PP ?\n"
        "  IUNSCR =        1    unscreen: 0-lin 1-nonlin 2-no\n"
        "END of PSCTR-controll parameters"
    )
    interactive_potcar_file.open("POTCAR")
    interactive_potcar_file.write(potential_head)
    path_to_potcar = interactive_potcar_file.filepath
    parsed = PotcarParser(path_to_potcar)
    assert parsed.element == "Ee"
    assert parsed.version == 99990399


def test_remove_regex():
    remove_regex = PotcarParser._RE_REMOVE_CHARS
    test_cases = ["^", "\t"]
    for test_case in test_cases:
        removed = remove_regex.sub(r"", test_case)
        assert removed == ""


def test_reduce_regex():
    reduce_regex = PotcarParser._RE_CONDENSE_CHARS
    test_cases = ["  ", "   ", "    "]
    for test_case in test_cases:
        reduced = reduce_regex.sub(r" ", test_case)
        assert reduced == " "


def test_header_regex():
    header_regex = PotcarParser._RE_HEADER
    test_case = (
        "Title line\n"
        "0.0000000000000000\n"
        "parameters from PSCTR are:\n"
        "random header contents\n"
        "END of PSCTR-controll parameters\n"
    )
    matched_header = header_regex.search(test_case).group(1)
    assert matched_header == "\nrandom header contents\n"


def test_element_regex():
    import random
    from pymatgen.core import periodic_table
    regex_element = PotcarParser._RE_ELEMENT
    test_case = "VRHFIN{}={}{}{}:continued"
    # test regex against all elements stored in pymatgen
    for item in periodic_table.Element:
        element = item.name
        # add some thrill by including some random whitespaces
        w1 = random.randint(0, 20) * " "
        w2 = random.randint(0, 20) * " "
        w3 = random.randint(0, 20) * " "
        test_string = test_case.format(w1, w2, element, w3)
        element_match = regex_element.search(test_string).group(1)
        assert element_match == element


def test_date_regex():
    regex_date = PotcarParser._RE_DATE
    # these cases should produce a match
    test_case = "9Abc99"
    date_match = regex_date.search(test_case).group(1)
    assert date_match == test_case
    test_case = "99Abc9999"
    date_match = regex_date.search(test_case).group(1)
    assert date_match == test_case
    # these cases should produce not match
    test_case = "Abc99"
    assert regex_date.search(test_case) is None
    test_case = "99Abc"
    assert regex_date.search(test_case) is None
    test_case = "Abc"
    assert regex_date.search(test_case) is None
