.. _user-guide-calculators:

******************
Calculator Classes
******************

This section contains the documentation for the available calculator classes.
In the following, detailed information on all calculator classes for running VASP calculations, that are implemented by the plugin, is given.

.. note::

   Although this may change in the future, currently, only a single calculation class is implemented in this plugin.
   However, the VASP calculations run by this class is solely controlled by the input parameters you provide for the calculation (similar to running VASP manually)
   Thus, although providing a single calculator only, the plugin is capable of running **all** kind of VASP calculations!
   This, of course, also includes AIMD and NEB calculations (See the calculator class documentation for detailed information)

.. toctree::
   :maxdepth: 1
   :caption: Implemented Calculator Classes:

   calculators/vasp_calculator.rst
