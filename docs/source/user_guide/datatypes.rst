.. _user-guide-datatypes:

*******************
Available Datatypes
*******************

In this chapter the calculation input and output datatypes for VASP calculations as implemented by this plugin are documented.
Here, input datatypes implement a representation of input parameters passed to a VASP calculation (i.e. corresponding to `INCAR`, `KPOINTS`, `POSCAR` and `POTCAR` files) that is compatible with and storable to AiiDA databases.
Contrary, the implemented output datatypes are used to store the generated outputs of VASP calculations to the AiiDA database.
In order to see how the input datatypes can be initialized and how you can interact with both calculation inputs and outputs, please refer to the individual documentation of each datatype given below.

.. note::

   Note that VASP output files that are not listed here explicitly does not mean that the plugin does not know about them or does not know how to store or handle them.
   For such files simply no individual output datatype was implemented and those will be stored to the database using the implemented general :class:`~aiida_cusp.outputs.VaspGenericData` class.

.. _user-guide-datatypes-inputs:

.. toctree::
   :maxdepth: 1
   :caption: Input Datatypes

   datatypes/inputs/incar.rst
   datatypes/inputs/kpoints.rst
   datatypes/inputs/poscar.rst
   datatypes/inputs/potcar.rst

.. _user-guide-datatypes-outputs:

.. toctree::
   :maxdepth: 1
   :caption: Output Datatypes

   datatypes/outputs/contcar.rst
   datatypes/outputs/vasprun.rst
   datatypes/outputs/outcar.rst
   datatypes/outputs/chgcar.rst
   datatypes/outputs/wavecar.rst
   datatypes/outputs/generic.rst
