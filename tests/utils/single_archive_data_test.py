# -*- coding: utf-8 -*-


"""
Test suite for the SingleArchiveData class
"""


import pytest

import pathlib
import gzip


def test_store_and_load_archive_data(tmpdir):
    from aiida_cusp.utils.single_archive_data import SingleArchiveData
    from aiida.orm import load_node
    testfile = pathlib.Path(tmpdir / 'testfile.txt')
    testcontent = "Test file contents".encode()
    # write contents to the testfile
    with open(testfile, 'wb') as filehandle:
        filehandle.write(testcontent)
    # store and re-load SingleArchiveData and compare the contents
    # in compressed format
    single_archive = SingleArchiveData(file=testfile)
    uuid = single_archive.store().uuid
    loaded_single_archive = load_node(uuid)
    assert single_archive.get_content() == loaded_single_archive.get_content()


def test_single_archive_node_contents(tmpdir):
    from aiida_cusp.utils.single_archive_data import SingleArchiveData
    testfile = pathlib.Path(tmpdir / 'testfile.txt')
    testcontent = "Test file contents".encode()
    testcontent_compressed = gzip.compress(testcontent)
    # write contents to the testfile
    with open(testfile, 'wb') as filehandle:
        filehandle.write(testcontent)
    # init SingleArchiveData from the testfile and check contents are stored
    # in compressed format
    single_archive = SingleArchiveData(file=testfile)
    with open(single_archive.filepath, 'rb') as filehandle:
        node_contents = filehandle.read()
    assert node_contents == testcontent_compressed


@pytest.mark.parametrize('decompress', [True, False])
def test_get_content_method(tmpdir, decompress):
    from aiida_cusp.utils.single_archive_data import SingleArchiveData
    testfile = pathlib.Path(tmpdir / 'testfile.txt')
    testcontent = "Test file contents".encode()
    testcontent_compressed = gzip.compress(testcontent)
    with open(testfile, 'wb') as filehandle:
        filehandle.write(testcontent)
    # init SingleArchiveData from the testfile and check contents are stored
    single_archive = SingleArchiveData(file=testfile)
    contents = single_archive.get_content(decompress=decompress)
    if decompress:
        assert contents == testcontent
    else:
        assert contents == testcontent_compressed


def test_get_repository_file_path(tmpdir):
    from aiida_cusp.utils.single_archive_data import SingleArchiveData
    testfile = pathlib.Path(tmpdir / 'testfile.txt')
    testcontent = "Test file contents".encode()
    testcontent_compressed = gzip.compress(testcontent)
    with open(testfile, 'wb') as filehandle:
        filehandle.write(testcontent)
    single_archive = SingleArchiveData(file=testfile)
    node_path = single_archive.filepath
    with open(node_path, 'rb') as filehandle:
        content_at_path = filehandle.read()
    assert content_at_path == testcontent_compressed


@pytest.mark.parametrize('decompress', [True, False])
def test_write_file_method(tmpdir, decompress):
    from aiida_cusp.utils.single_archive_data import SingleArchiveData
    # init the SingleArchiveData node
    testfile = pathlib.Path(tmpdir / 'testfile.txt')
    testcontent = "Test file contents".encode()
    testcontent_compressed = gzip.compress(testcontent)
    with open(testfile, 'wb') as filehandle:
        filehandle.write(testcontent)
    single_archive = SingleArchiveData(file=testfile)
    # write the file using the write-file method and read back
    outfile = pathlib.Path(tmpdir) / 'outfile.txt'
    assert outfile.exists() is False
    single_archive.write_file(outfile, decompress=decompress)
    assert outfile.exists() is True
    with open(outfile, 'rb') as fh:
        written_contents = fh.read()
    if decompress:
        assert written_contents == testcontent
    else:
        assert written_contents == testcontent_compressed
