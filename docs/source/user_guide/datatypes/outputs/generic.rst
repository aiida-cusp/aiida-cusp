.. _user-guide-datatypes-outputs-generic:

Generic (``cusp.generic``)
--------------------------

Output data type used to store data from VASP calculation output files for which no individual output data type is available.
However, the node is inherited from the same base class as all other output nodes and the contents are stored as gzip-compressed file to the repository.
For the :class:`~aiida_cusp.data.VaspGenericData` no specific methods for interacting with the class' contents are provided.
