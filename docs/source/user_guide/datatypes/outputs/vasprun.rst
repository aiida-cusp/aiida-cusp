.. _user-guide-datatypes-outputs-vasprun:

vasprun (``cusp.vasprun``)
--------------------------

Data types of class :class:`~aiida_cusp.data.outputs.VaspVasprunData` are used to store the data contained in the VASP calculation output files of type *vasprun.xml*.
As those files may grow large a gzip-compressed copy of the file is stored to the AiiDA repository instead of the plain file.
In order to simplify the access to the file's contents several methods are implemented by the class to access the stored file contents are implemented.

.. _user-guide-datatypes-outputs-vasprun-methods:

Implemented Methods and Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aiida_cusp.data.VaspVasprunData.get_vasprun

.. automethod:: aiida_cusp.data.VaspVasprunData.get_content

.. automethod:: aiida_cusp.data.VaspVasprunData.write_file

.. autoattribute:: aiida_cusp.data.VaspVasprunData.filepath
