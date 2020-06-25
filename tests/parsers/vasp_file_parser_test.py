# -*- coding: utf-8 -*-


"""
Test module for the VaspFileParser default parser class
"""


import pytest


@pytest.mark.parametrize('filename,expected_normalized',
[   # noqa: E128
    ('vasprun.xml', 'vasprun_xml'),
    ('W92932.tmp', 'w92932_tmp'),
    ('CONTCAR', 'contcar'),
])
@pytest.mark.parametrize('subfolder', ['sub', '05', ''])
def test_normalize_filename(vasp_file_parser, filename, subfolder,
                            expected_normalized):
    import pathlib
    # construct some arbitrary absolute path to the file
    filepath = pathlib.Path().absolute() / subfolder / filename
    normalized = vasp_file_parser.normalized_filename(filepath)
    assert normalized == expected_normalized


@pytest.mark.parametrize('filename,expected_linkname',
[   # noqa: E128
    ('vasprun.xml', 'vasprun_xml'),
    ('W288292.tmp', 'w288292_tmp'),
    ('/some/folder/File', 'file'),
    ('67/NebFile', 'node_67.nebfile'),
    ('00/NebFile', 'node_00.nebfile'),
    ('99/NebFile', 'node_99.nebfile'),
    ('000/NebFile', 'nebfile'),  # only 00-99 are valid neb subfolders
    ('0/NebFile', 'nebfile'),
    ('00a/NebFile', 'nebfile'),
    ('a00/NebFile', 'nebfile'),
    ('a00a/NebFile', 'nebfile'),
])
def test_generate_linkname_from_path(vasp_file_parser, filename,
                                     expected_linkname):
    import pathlib
    # construct some arbitrary absolute path to the file
    filepath = pathlib.Path().absolute() / filename
    linkname = vasp_file_parser.linkname(filepath)
    assert linkname == expected_linkname


# test build_parsing_list for both regular outputs and outputs
# located in subfolders
@pytest.mark.parametrize('subfolder', ['', 'has/sub/folder'])
@pytest.mark.parametrize('name_or_wildcard,expected_list',
[   # noqa: E128
    # parse_files unset: check for default settings
    (None, ['vasprun.xml', 'OUTCAR', 'CONTCAR']),
    # empty list: retriev nothing (should not raise an error)
    ([], []),
    # multiple explicitly named files
    (['INCAR', 'vasprun.xml'], ['INCAR', 'vasprun.xml']),
    # wildcards
    (['*CAR'], ['INCAR', 'POSCAR', 'CONTCAR', 'OUTCAR']),
    (['CONT*'], ['CONTCAR']),
    (['W*'], ['W3287382.tmp']),
    (['*.xml'], ['vasprun.xml']),
    (['INCAR', 'INCAR'], ['INCAR']),
    (['W*', '*xml'], ['W3287382.tmp', 'vasprun.xml']),
    # mixed explicit file definition and wildcard
    (['vasprun.xml', '*.xml'], ['vasprun.xml']),
    # 'pure' wildcard, matches everything
    (['*'], ['INCAR', 'POSCAR', 'CONTCAR', 'vasprun.xml', 'OUTCAR',
     'W3287382.tmp']),
])
def test_build_parsing_list(vasp_file_parser, name_or_wildcard, tmpdir,
                            expected_list, subfolder):
    import pathlib
    # fictitious list of file retrieved from a calculation
    filelist = ['INCAR', 'POSCAR', 'CONTCAR', 'vasprun.xml', 'OUTCAR',
                'W3287382.tmp']
    pathtmpdir = pathlib.Path(tmpdir).absolute()
    filepaths = [pathtmpdir / subfolder / f for f in filelist]
    for filepath in filepaths:
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True)
        filepath.touch()
    # point parser to the temporary directory and setup parse option to
    # parse only the given files
    vasp_file_parser.tmpfolder = str(pathtmpdir)
    if name_or_wildcard is not None:
        vasp_file_parser.settings['parse_files'] = name_or_wildcard
    # create the parsing list and check correct error code and no
    # duplicates
    _ = vasp_file_parser.verify_and_set_parser_settings()
    exit_code = vasp_file_parser.build_parsing_list()
    assert exit_code is None
    assert len(set(vasp_file_parser.files_to_parse)) == \
           len(vasp_file_parser.files_to_parse)
    # check generated list matches with expected parsing list
    expected_parselist = [pathtmpdir / subfolder / f for f in expected_list]
    assert set(vasp_file_parser.files_to_parse) == set(expected_parselist)


@pytest.mark.parametrize('wildcard', ['POTCAR', 'POT*', '*CAR', '*', 'P*',
                         '*R'])
def test_potcar_is_never_parsed(wildcard, vasp_file_parser, tmpdir):
    import pathlib
    # prepare the potcar file
    temporary_folder = pathlib.Path(tmpdir).absolute()
    potcar_file = temporary_folder / 'POTCAR'
    potcar_file.touch()
    assert potcar_file.exists() is True
    # try to parese it using the VaspFileParser
    vasp_file_parser.tmpfolder = str(temporary_folder)
    vasp_file_parser.settings['parse_files'] = [wildcard]
    _ = vasp_file_parser.verify_and_set_parser_settings()
    exit_code = vasp_file_parser.build_parsing_list()
    assert exit_code is None
    assert vasp_file_parser.files_to_parse == []


@pytest.mark.parametrize('file_exists', [True, False])
@pytest.mark.parametrize('fail_on_missing', [True, False])
def test_empty_parsing_list_fails(vasp_file_parser, file_exists,
                                  fail_on_missing, tmpdir):
    import pathlib
    # construct some arbitrary non-existent file
    filepath = pathlib.Path(tmpdir) / 'some_arbitrary_filename.abcd'
    # assure that the chosen file is indeed not present during the test
    if filepath.is_file():
        filepath.unlink()
    # create file and update the parser settings
    if file_exists:
        filepath.touch()
    assert filepath.is_file() is file_exists
    vasp_file_parser.tmpfolder = str(pathlib.Path(tmpdir).absolute())
    vasp_file_parser.settings['fail_on_missing_files'] = fail_on_missing
    # check exit code matches expected results
    _ = vasp_file_parser.verify_and_set_parser_settings()
    exit_code = vasp_file_parser.build_parsing_list()
    # we do not define any files for retrieval and therfore only the default
    # files are attempted to be retrieved. Thus, the following should fail
    # if the file does not exists but also if the files exists because the
    # default files do no exist leading to the list being empty anyway
    if fail_on_missing:
        assert exit_code.status == 302  # parsing list is empty
    else:  # all other cases should lead to zero exit code
        assert exit_code is None


# file list for all known files and a single (PROCAR) file which is going
# to trigger the parse_generic() parsing hook also check for correct
# namespace for files located in neb subfolders
@pytest.mark.parametrize('neb_subfolder', ['', '00', '52', '99'])
@pytest.mark.parametrize('outfile,base_linkname,entrypoint',
[   # noqa: E128
    ('vasprun.xml', 'vasprun_xml', 'cusp.vasprun'),
    ('OUTCAR', 'outcar', 'cusp.outcar'),
    ('CONTCAR', 'contcar', 'cusp.contcar'),
    ('WAVECAR', 'wavecar', 'cusp.wavecar'),
    ('CHGCAR', 'chgcar', 'cusp.chgcar'),
    ('PROCAR', 'procar', 'cusp.generic'),
])
def test_parsing_for_calcs(vasp_file_parser, tmpdir, outfile, poscar,
                           base_linkname, entrypoint, neb_subfolder):
    import pathlib
    from aiida.plugins import DataFactory
    from aiida_cusp.utils.defaults import PluginDefaults
    # update linkname if file is located in neb subfolder
    if neb_subfolder:
        linkname = "{}{}.{}".format(PluginDefaults.NEB_NODE_PREFIX,
                                    neb_subfolder, base_linkname)
    else:
        linkname = base_linkname
    # build complete expected output linkname by adding the parser output
    # namespace prefix to the base linkname
    full_linkname = "{}.{}".format(PluginDefaults.PARSER_OUTPUT_NAMESPACE,
                                   linkname)
    # load expected datatype for output node
    ExpectedDatatype = DataFactory(entrypoint)
    # setup the file
    tmpdirpath = pathlib.Path(tmpdir).absolute()
    filepath = tmpdirpath / neb_subfolder / outfile
    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True)
    if outfile != 'CONTCAR':
        filepath.touch()
    else:  # can't cheat on the CONTCAR when parsing with pymatgen
        poscar.write_file(filepath)
    assert filepath.is_file() is True
    # run the parser on the current temporary directory
    vasp_file_parser.settings['parse_files'] = [outfile]
    errno = vasp_file_parser.parse(retrieved_temporary_folder=str(tmpdirpath))
    assert errno is None
    assert full_linkname in vasp_file_parser.outputs
    ParsedDatatype = vasp_file_parser.outputs.get(full_linkname)
    assert isinstance(ParsedDatatype, ExpectedDatatype) is True


@pytest.mark.parametrize('setting,expected_exit_code',
[   # noqa: E128
    ({'parse_files': ['A', 'B', 'C']}, None),
    ({'fail_on_missing_files': True}, None),
    ({'unknown_option': None}, 301),
])
def test_accepted_parser_settings(vasp_code, setting, expected_exit_code):
    from aiida.plugins import CalculationFactory
    from aiida_cusp.parsers.vasp_file_parser import VaspFileParser
    # define code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculator
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
                'parser_settings': setting,
            }
        },
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc_node = VaspCalculation(inputs=inputs).node
    # init custom options and instantiate the parser class
    parser = VaspFileParser(vasp_calc_node)
    exit_code = parser.verify_and_set_parser_settings()
    if not exit_code:
        assert exit_code is None
        assert parser.settings == setting
    else:
        assert exit_code.status == expected_exit_code
