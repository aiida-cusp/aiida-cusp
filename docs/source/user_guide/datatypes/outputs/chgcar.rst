.. _user-guide-datatypes-outputs-chgcar:

CHGCAR (``cusp.chgcar``)
------------------------

Data types of class :class:`~aiida_cusp.data.VaspChgcarData` are used to store the data contained in the VASP calculation output files of type *CHGCAR*.
As those files may grow large a gzip-compressed copy of the file is stored to the AiiDA repository instead of the plain file.
Note that this data types is only implemented for convenience to simplify the sharing of *CHGCAR* contents between calculations.
However, you may use the class as you wish but be advised that only the basic methods for accessing the file's contents are implemented as it can be seen in the following.

.. _user-guide-datatypes-outputs-chgcar-methods:

Implemented Methods and Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aiida_cusp.data.VaspChgcarData.get_content
   :noindex:

.. automethod:: aiida_cusp.data.VaspChgcarData.write_file
   :noindex:

.. autoattribute:: aiida_cusp.data.VaspChgcarData.filepath
   :noindex:
