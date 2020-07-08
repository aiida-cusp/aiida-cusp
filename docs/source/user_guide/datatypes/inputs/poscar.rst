.. _user-guide-datatypes-inputs-poscar:

POSCAR (``cusp.poscar``)
------------------------

Input data type for structure inputs passed to VASP calculations.
Contrary to a plain structure data type the :class:`~aiida_cusp.data.VaspPoscarData` class offers multiple additional attributes like constraints or atomic velocities

.. _user-guide-datatypes-inputs-poscar-initializing:

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

  >>> from aiida.plugins import DataFactory
  >>> from pymatgen import Lattice, Structure
  >>> lattice = Lattice.cubic(3.359)
  >>> structure = Structure(lattice, ["Po"], [.0, .0, .0])
  >>> VaspPoscarData = DataFactory('cusp.poscar')
  >>> cusp_poscar = VaspPoscarData(structure=structure)
  >>> print(cusp_poscar.get_poscar())
  Po1
  1.0
  3.359000 0.000000 0.000000
  0.000000 3.359000 0.000000
  0.000000 0.000000 3.359000
  Po
  1
  direct
  0.000000 0.000000 0.000000 Po


**Example with constraints:** ::

  >>> from aiida.plugins import DataFactory
  >>> from pymatgen import Lattice, Structure
  >>> lattice = Lattice.cubic(3.359)
  >>> structure = Structure(lattice, ["Po"], [.0, .0, .0])
  >>> VaspPoscarData = DataFactory('cusp.poscar')
  >>> cusp_poscar = VaspPoscarData(structure=structure, constraints=[[True, False, True]])
  >>> print(cusp_poscar.get_poscar())
  Po1
  1.0
  3.359000 0.000000 0.000000
  0.000000 3.359000 0.000000
  0.000000 0.000000 3.359000
  Po
  1
  Selective dynamics
  direct
  0.000000 0.000000 0.000000 T F T Po

.. _user-guide-datatypes-inputs-poscar-recovering-data:

Recovering the stored structure data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to further analyze or re-use structures the :class:`~aiida_cusp.data.VaspPoscarData` class offers several methods to retrieve the stored structure.
In particular, four different methods are available to recover the stored structure data in different formats:

.. automethod:: aiida_cusp.data.VaspPoscarData.get_poscar
   :noindex:

.. automethod:: aiida_cusp.data.VaspPoscarData.get_structure
   :noindex:

.. automethod:: aiida_cusp.data.VaspPoscarData.get_atoms
   :noindex:

.. automethod:: aiida_cusp.data.VaspPoscarData.get_aiida_structure
   :noindex:
