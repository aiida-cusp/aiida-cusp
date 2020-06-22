.. _user-guide-datatypes-outputs-vasprun:

vasprun (``cusp.vasprun``)
--------------------------

Output data type storing the data contained in the VASP calculation output files of type *vasprun.xml*.
In order to save disk space all contents of this data type are stored as gzip-compressed files to the AiiDA repository.
The contents of this file may be restored by the provided methods of the class documented in the following.


.. _user-guide-datatypes-outputs-vasprun-methods:

Implemented Methods and Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aiida_cusp.data.VaspVasprunData.get_vasprun
