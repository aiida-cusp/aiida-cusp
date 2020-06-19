Calculation Input and Output Datatypes
======================================

In this chapter the implemented input and output datatypes of this plugin are documented.
Note that VASP output files that are not listed here does not mean they are not understood by the plugin.
It just means that there doesn't exist a special implementation for those files.
In that case the files will be simply stored as ordinary :class:`aiida.orm.SinglefileData` objects without further functionality.

.. toctree::
   :maxdepth: 1
   :caption: Input Datatypes

   inputs/incar.rst
   inputs/kpoints.rst
   inputs/poscar.rst
   inputs/potcar.rst

.. toctree::
   :maxdepth: 1
   :caption: Output Datatypes

   outputs/outcar.rst
