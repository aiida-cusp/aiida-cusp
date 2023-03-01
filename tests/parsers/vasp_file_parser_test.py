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
def test_normalize_filename(vasp_file_parser, filename, expected_normalized):
    normalized = vasp_file_parser.normalized_filename(filename)
    assert normalized == expected_normalized


@pytest.mark.parametrize('suffix', ["", ".mysuffix"])
@pytest.mark.parametrize('file_or_path,expected_linkname',
[   # noqa: E128
    ('vasprun.xml', 'vasprun_xml'),
    ('W288292.tmp', 'w288292_tmp'),
    ('/some/folder/File', 'file'),
    ('67/NebFile', 'node_67__nebfile'),
    ('00/NebFile', 'node_00__nebfile'),
    ('99/NebFile', 'node_99__nebfile'),
    ('000/NebFile', 'nebfile'),  # only 00-99 are valid neb subfolders
    ('0/NebFile', 'nebfile'),
    ('00a/NebFile', 'nebfile'),
    ('a00/NebFile', 'nebfile'),
    ('a00a/NebFile', 'nebfile'),
])
def test_generate_linkname_from_path(vasp_file_parser, file_or_path,
                                     expected_linkname, suffix):
    import pathlib
    # construct some arbitrary absolute path to the file
    filepath = pathlib.Path().absolute() / file_or_path
    filestem = filepath.name
    filepath = filepath.parent / (filestem + suffix)
    linkname = vasp_file_parser.linkname(filepath, filestem, suffix)
    if suffix:
        expected_linkname = f"{suffix[1:]}__{expected_linkname}"
    assert linkname == expected_linkname


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
def test_build_parsing_list_orig(vasp_file_parser, name_or_wildcard, tmpdir,
                                 expected_list, subfolder):
    """
    This function tests the build process of the parsers parsing list
    for a plain VASP calculation which does not have any custodian jobs
    defined with it (i.e. no suffixes!)
    """
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
    actual_parselist = vasp_file_parser.files_to_parse
    assert exit_code is None
    assert len(set(vasp_file_parser.files_to_parse)) == \
           len(vasp_file_parser.files_to_parse)
    # check generated list matches with expected parsing list
    expected_parselist = []
    for filename in expected_list:
        fpath = (pathtmpdir / subfolder / filename).resolve()
        fname = fpath.name
        fsuff = ""  # suffix is empty since no custodian job
        expected_parselist.append((fpath, fname, fsuff))
    assert set(vasp_file_parser.files_to_parse) == set(expected_parselist)


@pytest.mark.parametrize('subfolder', ['', 'has/sub/folder'])
@pytest.mark.parametrize('suffixes', [(''), ('.one'), ('.one', '.two')])
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
def test_build_parsing_list_cstdn(vasp_code, name_or_wildcard, tmpdir,
                                  expected_list, subfolder, suffixes):
    """
    This function tests the build process of the parsers parsing list
    for a VASP calculation which also has custodian jobs / suffixes
    defined
    """
    import pathlib
    from aiida.plugins import CalculationFactory
    from aiida_cusp.parsers.vasp_file_parser import VaspFileParser
    from custodian.vasp.jobs import VaspJob
    # fictitious list of file retrieved from a calculation
    filelist = ['INCAR', 'POSCAR', 'CONTCAR', 'vasprun.xml', 'OUTCAR',
                'W3287382.tmp']
    pathtmpdir = pathlib.Path(tmpdir).resolve()
    for fstem in filelist:
        for suffix in suffixes:
            fname = f"{fstem}{suffix}"
            fpath = pathtmpdir / subfolder / fname
            if not fpath.parent.exists():
                fpath.parent.mkdir(parents=True)
            fpath.touch()
    # create custodian jobs with defined suffixes
    jobs = [VaspJob(None, suffix=s) for s in suffixes if s is not None]
    # setup the parser using the defined jobs and assing the defined
    # files which shall be parsed by the parser
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    calc_inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
        'custodian': {'jobs': jobs},
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc_node = VaspCalculation(inputs=calc_inputs).node
    vasp_file_parser = VaspFileParser(vasp_calc_node)
    pathtmpdir = pathlib.Path(tmpdir).resolve()
    vasp_file_parser.tmpfolder = str(pathtmpdir)
    if name_or_wildcard is not None:
        vasp_file_parser.settings['parse_files'] = name_or_wildcard
    # create the expected parsing list from the list of expected files
    expected_parselist = []
    for fstem in expected_list:
        for suffix in suffixes:
            fname = f"{fstem}{suffix}"
            fpath = (pathtmpdir / subfolder / fname).resolve()
            expected_parselist.append((fpath, fstem, suffix))
    # finally, run the parsing list build process
    _ = vasp_file_parser.verify_and_set_parser_settings()
    exit_code = vasp_file_parser.build_parsing_list()
    actual_parselist = vasp_file_parser.files_to_parse
    # analyse the retrieved results
    assert exit_code is None
    assert len(actual_parselist) == len(expected_parselist)
    assert set(actual_parselist) == set(expected_parselist)


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
@pytest.mark.parametrize('suffix', ['', '.cstdnjobsuffix'])
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
def test_parsing_for_calcs(vasp_code, tmpdir, outfile, poscar, base_linkname,
                           entrypoint, neb_subfolder, suffix):
    import pathlib
    from custodian.vasp.jobs import VaspJob
    from aiida.plugins import DataFactory, CalculationFactory
    from aiida_cusp.utils.defaults import PluginDefaults
    from aiida_cusp.parsers.vasp_file_parser import VaspFileParser
    # setup the type for calculation for which the parser is run
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
                'parser_settings': {'parse_files': [outfile]},
            },
        },
    }
    # extend options with custodian job if a suffix is given
    if suffix:
        inputs['custodian'] = {'jobs': [VaspJob(None, suffix=suffix)]}
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc_node = VaspCalculation(inputs=inputs).node
    # next we create the files that we want to parse from the calculation
    tmpdirpath = pathlib.Path(tmpdir).absolute()
    filepath = tmpdirpath / neb_subfolder / (outfile + suffix)
    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True)
    if outfile != 'CONTCAR':
        filepath.touch()
    else:  # can't cheat on the CONTCAR when parsing with pymatgen
        poscar.write_file(filepath)
    assert filepath.is_file() is True
    # once the files are in place we can now setup the parser class associated
    # with the just created calculation node and try to parse the files
    vasp_file_parser = VaspFileParser(vasp_calc_node)
    errno = vasp_file_parser.parse(retrieved_temporary_folder=str(tmpdirpath))
    assert errno is None
    # setup the expected datatype and linkname
    ExpectedDatatype = DataFactory(entrypoint)
    if neb_subfolder:
        linkname = "{}{}__{}".format(PluginDefaults.NEB_NODE_PREFIX,
                                     neb_subfolder, base_linkname)
    else:
        linkname = base_linkname
    linkname = f"{suffix[1:]}__{linkname}" if suffix else linkname
    # build complete expected output linkname by adding the parser output
    # namespace prefix to the base linkname
    full_linkname = "{}.{}".format(PluginDefaults.PARSER_OUTPUT_NAMESPACE,
                                   linkname)
    # finally run the tests if all linknames are correct and the stored
    # types are the expected ones
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


@pytest.mark.parametrize('suffix', ['', '.mysuffix'])
@pytest.mark.parametrize('filepath', ['somefile', '00/somefile',
                         '45/somefile', '99/somefile'])
def test_output_node_namespaces(vasp_code, suffix, filepath, tmpdir):
    import pathlib
    from aiida.plugins import CalculationFactory
    from aiida_cusp.parsers.vasp_file_parser import VaspFileParser
    from aiida_cusp.utils.defaults import PluginDefaults
    from custodian.vasp.jobs import VaspJob
    # if suffix is set we generate a VaspJob for it
    jobs = []
    if suffix:
        jobs = [VaspJob(None, suffix=suffix)]
    # setup files in the temporary directory
    fpath = pathlib.Path(tmpdir) / (filepath + suffix)
    if not fpath.parent.exists():
        fpath.parent.mkdir(parents=True)
    fpath.touch()  # define code
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    # setup calculator and instantiate parser class
    inputs = {
        'code': vasp_code,
        'metadata': {
            'options': {
                'resources': {'num_machines': 1},
                'parser_settings': {'parse_files': ['somefile']},
            },
        },
        'custodian': {'jobs': jobs},
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc = VaspCalculation(inputs=inputs)
    parser = VaspFileParser(vasp_calc.node)
    exit_code = parser.parse(retrieved_temporary_folder=tmpdir)
    assert exit_code is None
    # make sure we did parse something
    assert len(list(parser.outputs.items())) > 0
    # test outputs can actually be linked (this would fail if the namespace
    # is not available)
    for linkname, node in parser.outputs.items():
        vasp_calc.out(linkname, node)


def test_list_of_essential_files():
    """
    Assert that the expected_files() method returns `None`
    """
    from aiida_cusp.parsers.vasp_file_parser import VaspFileParser
    assert VaspFileParser.expected_files() is None


@pytest.mark.parametrize('parsing_list,suffixes,expected_triplets',
[   # noqa: E128
    ([], [""], []),
    (['A'], [""], [('A', 'A', '')]),
    (['A', 'B'], [""], [('A', 'A', ''), ('B', 'B', '')]),
    (['A'], ['.s1'], [('A.s1', 'A', '.s1')]),
    (['A', 'B'], ['.s1'], [('A.s1', 'A', '.s1'), ('B.s1', 'B', '.s1')]),
    # if a file is defined without suffix, we try to match that file with
    # any possible suffix
    (['A'], ['.s1', '.s2'], [('A.s1', 'A', '.s1'), ('A.s2', 'A', '.s2')]),
    # if a file happens to be defined with a suffix that is used by a job
    # it will not be extended with any other suffix
    (['A.s1'], ['.s1', '.s2'], [('A.s1', 'A', '.s1')]),
    (['A.s2'], ['.s1', '.s2'], [('A.s2', 'A', '.s2')]),
    # however if the suffix is not used by any job, then the file+suffix
    # is treated as the file name
    #
    (['A.s3'], ['.s1', '.s2'], [('A.s3.s1', 'A.s3', '.s1'),
                                ('A.s3.s2', 'A.s3', '.s2')]),
    # filenames containing wildcards are treated like normal names and we
    # do not mess with the defined wildcards
    (['A*'], ['.s1'], [('A*.s1', 'A*', '.s1')]),
    (['A.s2*'], ['.s1', '.s2'], [('A.s2*.s1', 'A.s2*', '.s1'),
                                 ('A.s2*.s2', 'A.s2*', '.s2')]),
    (['A*.s2'], ['.s1', '.s2'], [('A*.s2', 'A*', '.s2')]),
    (['A*.s3'], ['.s1', '.s2'], [('A*.s3.s1', 'A*.s3', '.s1'),
                                 ('A*.s3.s2', 'A*.s3', '.s2')]),
])
def test_build_parsing_triplets(vasp_file_parser, parsing_list, suffixes,
                                expected_triplets):
    vasp_file_parser.parsing_list = parsing_list
    vasp_file_parser.get_custodian_suffixes = lambda: suffixes
    parsing_triplets = vasp_file_parser.build_parsing_triplets()
    assert sorted(parsing_triplets) == sorted(expected_triplets)


@pytest.mark.parametrize('suffixA', [None, '', '.job1'])
@pytest.mark.parametrize('suffixB', [None, '', '.job2'])
@pytest.mark.parametrize('suffixC', [None, '', '.job3'])
def test_get_custodian_suffixes(vasp_code, suffixA, suffixB, suffixC):
    """
    Check the get_custodian_suffixes function with one to three
    jobs connected that may or may not define a suffix
    """
    from aiida.plugins import CalculationFactory
    from aiida_cusp.parsers.vasp_file_parser import VaspFileParser
    from custodian.vasp.jobs import VaspJob
    # setup the jobs
    suffixes = [suffixA, suffixB, suffixC]
    jobs = [VaspJob(None, suffix=s) for s in suffixes if s is not None]
    # setup the parser
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    calc_inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
        'custodian': {'jobs': jobs},
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc_node = VaspCalculation(inputs=calc_inputs).node
    vasp_file_parser = VaspFileParser(vasp_calc_node)
    # get suffixes
    expected_suffixes = [suffix for suffix in suffixes if suffix is not None]
    extracted_suffixes = vasp_file_parser.get_custodian_suffixes()
    if not jobs:
        assert extracted_suffixes == [""]
    else:
        assert extracted_suffixes == expected_suffixes


def test_get_custodian_suffixes_if_undefined(vasp_code):
    """
    Check that the get_custodian_suffixes() methods does not fail if
    no custodian job is defined among the calculation inputs. Similar
    to no defined jobs, this should return an empty suffix
    """
    from aiida.plugins import CalculationFactory
    from aiida_cusp.parsers.vasp_file_parser import VaspFileParser
    from custodian.vasp.jobs import VaspJob
    # setup the parser but do not define any custodian settings at all
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    calc_inputs = {
        'code': vasp_code,
        'metadata': {'options': {'resources': {'num_machines': 1}}},
        # no custodian settings defined here!
    }
    VaspCalculation = CalculationFactory('cusp.vasp')
    vasp_calc_node = VaspCalculation(inputs=calc_inputs).node
    vasp_file_parser = VaspFileParser(vasp_calc_node)
    # without any custodian settings defined, the returned suffixes should
    # be the only the empty suffix (as it would be without any custodian
    # jobs being defined)
    extracted_suffixes = vasp_file_parser.get_custodian_suffixes()
    assert extracted_suffixes == [""]


@pytest.mark.parametrize('fileA', ['A', 'A.s1', 'A.s2'])
@pytest.mark.parametrize('fileB', ['A', 'A.s1', 'A.s2'])
def test_remove_duplicates(vasp_file_parser, fileA, fileB):
    """
    Test removal of duplicate entries from provided lists of parsing_triplets
    """
    # not that unique entries are identified purely on the file name stored
    # in the first tuple entry. Thus, we initialize the list of triplets with
    # tuples of length 1, such that we immediately fail if the methdo tries
    # to access any other entry than the first one
    filelist = [fileA, fileB]
    # build list of expected, unique triplets
    expected_triplets = []
    for file_name in set(filelist):
        expected_triplets.append((file_name,))
    # build triplet list passed to remove_duplicates() method
    triplets = []
    for file_name in filelist:
        triplets.append((file_name,))
    unique_triplets = vasp_file_parser.remove_duplicates(triplets)
    assert len(unique_triplets) == len(list(set(filelist)))
    assert sorted(unique_triplets) == sorted(expected_triplets)


@pytest.mark.parametrize('subfolder', ['', 'has/sub/folder'])
@pytest.mark.parametrize('name_or_wildcard,expected_list',
[   # noqa: E128
    (['*A'], ['FileA', 'FileAA', 'FileAAA']),
    (['*A', '*AA'], ['FileA', 'FileAA', 'FileAAA']),
    (['*A', '*AA', '*AAA'], ['FileA', 'FileAA', 'FileAAA']),
])
def test_build_parsing_list_duplicates(vasp_file_parser, name_or_wildcard,
                                       tmpdir, expected_list, subfolder):
    """
    Assert that duplicate filenames (i.e. files matching in name and suffix)
    are discarded from the parsing list and only added once
    """
    import pathlib
    # setup the imaginary retrieve folder containing a list of arbitrary
    # files that might have been retrieved from the server
    filelist = ['FileA', 'FileAA', 'FileAAA']
    pathtmpdir = pathlib.Path(tmpdir).resolve()
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
    # check generated list matches with expected parsing list
    expected_parselist = [pathtmpdir / subfolder / f for f in expected_list]
    actual_parselist = [entry[0] for entry in vasp_file_parser.files_to_parse]
    assert len(actual_parselist) == len(expected_parselist)
    assert set(actual_parselist) == set(expected_parselist)
