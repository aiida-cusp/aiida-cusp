# -*- coding: utf-8 -*-


"""
Test suite for the SingleArchiveData class
"""


import pytest

import pathlib
import gzip


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
    assert node_contents[0:2] == b'\x1f\x8b'
    # omit comparing mtime bytes which may cause spurious errors
    assert node_contents[8:] == testcontent_compressed[8:]


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
        assert contents[0:2] == b'\x1f\x8b'
        # omit comparing mtime bytes which may cause spurious errors
        assert contents[8:] == testcontent_compressed[8:]


def test_get_repository_file_path(tmpdir):
    from aiida_cusp.utils.single_archive_data import SingleArchiveData
    testfile = pathlib.Path(tmpdir / 'testfile.txt')
    testcontent = "Test file contents".encode()
    # set mtime
    testcontent_compressed = gzip.compress(testcontent)
    with open(testfile, 'wb') as filehandle:
        filehandle.write(testcontent)
    single_archive = SingleArchiveData(file=testfile)
    node_path = single_archive.filepath
    with open(node_path, 'rb') as filehandle:
        content_at_path = filehandle.read()
    assert content_at_path[0:2] == b'\x1f\x8b'
    # omit comparing mtime bytes which may cause spurious errors
    assert content_at_path[8:] == testcontent_compressed[8:]


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
        assert written_contents[0:2] == b'\x1f\x8b'
        # omit comparing mtime bytes which may cause spurious errors
        assert written_contents[8:] == testcontent_compressed[8:]


def test_dynamic_filepath_property(tmpdir):
    """
    Checks for a bug with the filepath property being reported as not
    available on a loaded SingleFileArchive Data objects that were
    loaded from the database (__init__ is never called of a node is
    loaded from the database)
    """
    from aiida_cusp.utils.single_archive_data import SingleArchiveData
    emptyfile = pathlib.Path(tmpdir / 'testfile.txt')
    emptyfile.touch()
    data_node = SingleArchiveData(file=emptyfile)
    assert hasattr(data_node, '_filehandle') is False
    # make sure this does not fail and returns a string
    path = data_node.filepath
    assert isinstance(path, str)
    # assert that _filehandle attribute was created after we call
    # filepath property
    assert hasattr(data_node, '_filehandle') is True
