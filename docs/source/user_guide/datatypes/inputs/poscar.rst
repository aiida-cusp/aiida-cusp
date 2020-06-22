.. _user-guide-datatypes-inputs-poscar:

POSCAR (``cusp.poscar``)
------------------------

Contrary to a plain structure data type the VaspPoscarData class offers multiple additional attributes like constraints or  atomic velocities

Initializing  the class
^^^^^^^^^^^^^^^^^^^^^^^

In general the constructor of the :class:`~aiida_cusp.data.VaspPoscarData` class is of the following form:

.. code-block:: python

   VaspPoscarData(structure=None, constraints=None, velocities=None, temperature=None)

**Arguments:**

* **structure** (:class:`~aiida.orm.StructureData`, :class:`~pymatgen.core.Structure` or :class:`~pymatgen.io.vasp.inputs.Poscar`) --
  The structure data used to generate the POSCAR data from.
* **constraints** (:class:`list`, optional) --
  Nx3 list (N the number of atoms) of :class:`bool` introducing selective dynamics by adding constraints on the coordinates for every atom contained in the structure.
  (i.e. :class:`False`: coordinate is not allowed to change, :class:`True` coordinate is allowed to change)
* **velocities** (:class:`list`, optional) --
  Nx3 list (N the number of atoms) of :class:`float` setting the velocities for every atom on the structure
* **temperature** (:class:`float`, optional) --
  Instead of passing an explicit list of velocities initialize the atomic velocities from a Maxwell-Boltzmann distribution at the given temperature

**Example plain structure:** ::

  Hello

**Example with constraints:** ::

  Hello


Recovering the stored structure data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to further analyze or re-use structures the :class:`~aiida_cusp.data.VaspPoscarData` class offers several methods to retrieve the stored structure.
In particular, three different methods are available to recover the stored structure data in different formats:

:func:`~aiida_cusp.data.VaspPoscarData.get_structure()`

  Returns the stored structure data as :class:`pymatgen.core.Structure`

:func:`~aiida_cusp.data.VaspPoscarData.get_atoms()`

  Returns the stored structure data as :class:`ase.Atoms`

:func:`~aiida_cusp.data.VaspPoscarData.get_aiida_structure()`

  Returns the stored structure data as :class:`aiida_core.orm.StructureData`
