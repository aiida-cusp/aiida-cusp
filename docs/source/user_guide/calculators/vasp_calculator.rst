Vasp Calculator (``cusp.vasp``)
===============================

The plugin offers a single calculator object, the :class:`~aiida_cusp.calculators.VaspCalculator`, published under the ``cusp.vasp`` entry point
This calculation class allows you to perform simple VASP calculations as well as more complex VASP NEB calculations.
Which calculation is run is decided by the calculation objected based on the given structural inputs (i.e. ``poscar`` or ``neb_path``).
Similar to VASP itself the behavior of the calculation is entirely controllable by the defined input parameters defined for `KPOINTS`, `INCAR` ..
In the following the accepted inputs required to setup a calculation are discussed.

.. note::

   Although the calculators remove a big deal of repetitive work keep in mind that they are, by construction, kept stupid.
   In particular, their only purpose is to run a calculation and finally retrieve the generated outputs without adding any black parsing magic.
   This offers a great flexibility of the calculator itself and leaves enough magic for the workflows



