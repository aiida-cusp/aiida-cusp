.. _user-guide-datatypes-outputs-wavecar:

WAVECAR (``cusp.wavecar``)
--------------------------

Output data type storing the data contained in the VASP calculation output files of type *WAVECAR*.
In order to save disk space all contents of this data type are stored as gzip-compressed files to the AiiDA repository.
Note that this data type is only a convenient addition to make the *WAVECAR* contents easily shareable between calculations.
In particular, no specific methods for interacting with the class' contents are provided.
