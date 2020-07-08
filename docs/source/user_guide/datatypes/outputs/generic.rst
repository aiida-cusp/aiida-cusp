.. _user-guide-datatypes-outputs-generic:

Generic (``cusp.generic``)
--------------------------

Data types of class :class:`~aiida_cusp.data.outputs.VaspGenericData` are used to store the data contained in the VASP calculation output files for which no individual data type is available.
However, the node is inherited from the same base class as all other output nodes.
This means a gzip-compressed copy of every file marked as :class:`~aiida_cusp.data.outputs.VaspGenericData` is stored to the repository rather than the plain file contents.
Similar to the data types available for :ref:`WAVECAR<user-guide-datatypes-outputs-wavecar>` and :ref:`CHGCAR<user-guide-datatypes-outputs-chgcar>` this type is not optimized for user interaction.
However, you still may use the type as you like and the stored contents can be easily accessed via the implemented basic methods for file access.

.. _user-guide-datatypes-outputs-generic-methods:

Implemented Methods and Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aiida_cusp.data.VaspGenericData.get_content
   :noindex:

.. automethod:: aiida_cusp.data.VaspGenericData.write_file
   :noindex:

.. autoattribute:: aiida_cusp.data.VaspGenericData.filepath
   :noindex:
