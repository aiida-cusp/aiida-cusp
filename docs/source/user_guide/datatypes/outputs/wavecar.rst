.. _user-guide-datatypes-outputs-wavecar:

WAVECAR (``cusp.wavecar``)
--------------------------

Data types of class :class:`~aiida_cusp.data.outputs.VaspWavecarData` are used to store the data contained in the VASP calculation output files of type *WAVECAR*.
As those files may grow large a gzip-compressed copy of the file is stored to the AiiDA repository instead of the plain file.
Note that this data types is only implemented for convenience to simplify the sharing of *WAVECAR* contents between calculations.
However, you may use the class as you wish but be advised that only the basic methods for accessing the file's contents are implemented as it can be seen in the following.

.. _user-guide-datatypes-outputs-wavecar-methods:

Implemented Methods and Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aiida_cusp.data.VaspWavecarData.get_content

.. automethod:: aiida_cusp.data.VaspWavecarData.write_file

.. autoattribute:: aiida_cusp.data.VaspWavecarData.filepath
