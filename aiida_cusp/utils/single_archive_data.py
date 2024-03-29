# -*- coding: utf-8 -*-


"""
Extension to AiiDA's SinglefileData storing the given file as gzip-compressed
archive instead of simply storing the file as-is
"""


import pathlib
import gzip
import io
import tempfile

from aiida.orm import SinglefileData


class SingleArchiveData(SinglefileData):
    """
    Data class used to store the contents of a file as gzip compressed
    archive in its repository
    """

    # suffix appended to the file name deduced from the given path when stored
    # to the repository
    ARCHIVE_SUFFIX = '.gz'

    def set_file(self, file, filename=None):
        """
        Compress given file and store it to the node's repository.

        This method differs from the original SinglefileData.set_file()
        method in that it only accepts a filepath. The additional filename
        argument is only here to make AiiDA happy and is ignored since we
        only allow file path inputs from which the filename is deduced.

        :param file: path to the file whose contents will be compressed and
            stored to the repository
        :type file: pathlib.Path
        :raises ValueError: if the given path does not point to a file
        """
        # check if the path points to a valid file
        if not file.is_file():
            raise ValueError("given file path '{}' does not point to a file"
                             .format(file.absolute()))
        # get the compressed contents as io.BytesIO and initialize the
        # SinglefileData node using the byte stream
        file, filename = self.get_compressed_file_contents(file)
        super(SingleArchiveData, self).set_file(file=file, filename=filename)

    def get_compressed_file_contents(self, filepath):
        """
        Load the file and return a gzip compressed version of the contents

        :param filepath: path to the file whose contents will be loaded
            and compressed using gzip
        :type filepath: pathlib.Path
        :returns: a tuple containing the compressed file contents and the
            file's name with '.gz' suffix appended
        :rtype: tuple
        """
        # transform to Path() object (nothing happens if it already is)
        filepath = pathlib.Path(filepath).absolute()
        with open(filepath, 'rb') as infile:
            compressed_contents = gzip.compress(infile.read())
        filepath = filepath.with_suffix(filepath.suffix + self.ARCHIVE_SUFFIX)
        # AiiDA excpects a BytesIO object to initialize the node from stream
        return io.BytesIO(compressed_contents), str(filepath.name)

    def get_content(self, decompress=True):
        """
        Load the node and return either the archive (i.e. compressed) or the
        file (i.e. the decompressed) contents stored in the node.

        :param decompress: Indicate wether comressed or uncompressed contents
            are returned
        :type decompress: `bool`
        """
        # cannot use internal get_content() method as this only reads
        # strings from the repo
        with self.open(mode='rb') as archive:
            archive_contents = archive.read()
        if decompress:
            return gzip.decompress(archive_contents)
        else:
            return archive_contents

    def write_file(self, filepath, decompress=True):
        """
        Write the node's contents to a file

        :params filepath: path to the output file to which the stored
            contents will be written
        :type filepath: str or pathlib.Path
        :params decompress: write the decompressed or the archive contents
            to the file
        :type decompress: bool
        """
        filepath = pathlib.Path(filepath)
        if filepath.is_dir():
            raise ValueError("invalid filename (not a file)")
        with open(filepath, 'wb') as outfile:
            outfile.write(self.get_content(decompress=decompress))

    @property
    def filepath(self):
        """
        Return the path of the object in the repository.

        Basically replicates the procedure in the internal open method without
        the final call to the open()
        """
        # FIXME: Due to the recent change in aiida v2 introducing the new file
        #        repository classical files went out of existence. However,
        #        pymatgen cannot handle streams but relies on the physical
        #        files to instantiate output classes. Moreover, the file may
        #        also be opened multiple times not only during instantiation.
        #        In order to bring both worlds together a temporary file is
        #        created from the contents stored in the repo which is then
        #        deleted when garbage collected.

        # since there is no call to __init__ when loading from the database
        # we need to set the `_filehandle` property dynamically
        if not hasattr(self, '_filehandle'):
            self._filehandle = tempfile.NamedTemporaryFile(
                mode='wb', suffix=self.ARCHIVE_SUFFIX)
            self._filehandle.write(self.get_content(decompress=False))
            self._filehandle.flush()
        return self._filehandle.name

    def __del__(self):
        # properly close the filehandle once the object went out of scope
        # and is garbage collected
        if hasattr(self, '_filehandle'):
            self._filehandle.close()
