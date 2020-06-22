.. _user-guide-datatypes-outputs-outcar:

OUTCAR (``cusp.outcar``)
------------------------

Output data type storing the data contained in the VASP calculation output files of type *OUTCAR*.
In order to save disk space all contents of this data type are stored as gzip-compressed files to the AiiDA repository.
Contents of this file may be restored by the provided methods of the class documented in the following.

.. _user-guide-datatypes-outputs-outcar-methods:

Implemented Methods and Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aiida_cusp.data.VaspOutcarData.get_outcar
