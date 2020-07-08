.. _user-guide-datatypes-inputs-kpoints:

KPOINTS (``cusp.kpoints``)
--------------------------

Using the :class:`~aiida_cusp.data.VaspKpointData` the `KPOINT parameters`_ of a calculation can be passed to the VASP calculation object.
This data class is published by the plugin using the ``cusp.kpoints`` entry point and can be loaded via AiiDA's :func:`~aiida.plugins.DataFactory` function.
To simplify the setup of different k-point grids (i.e. `Monkhorst`, `Gamma`, `Automatic`, etc.), the class is closely connected to Pymatgen's :class:`~pymatgen.io.vasp.inputs.Kpoints` class supporting multiple initialization modes.
Which of the implemented initialization mode is used to generate the k-point data is decided by the plugin based on the type and set of parameters passed to the constructor (see the :ref:`following section<user-guide-datatypes-inputs-kpoints-init>`)

.. _user-guide-datatypes-inputs-kpoints-init:

Initializing the class
^^^^^^^^^^^^^^^^^^^^^^

In general the constructor of the :class:`~aiida_cusp.data.VaspKpointData` class accepts k-point settings (defining the k-point grid) and an optional structure input required for density based on k-point grid definition:

.. code-block:: python

   VaspKpointData(kpoints=None, structure=None)

**Arguments:**

* **kpoints** (:class:`dict` or :class:`pymatgen.io.vasp.inputs.Kpoints`) --
  The KPOINT parameters used to run a VASP calculation.
  May be given as :class:`pymatgen.io.vasp.inputs.Kpoints` object which is useful if k-points parameters defined by a pymatgen set should be used.
  Alternatively (i.e. no pre-defined pymatgen set should be used) the desired k-point grid may also be set using a parameter :class:`dict`.
  In that case the grid is generated using the class-internal methods depending on the type of parameters passed by the :class:`dict`
  (See the :ref:`following section<inputs_kpoints_init_modes>` for more details on the possible parameters and corresponding generation modes)
  kpoint parameters
* **structure** (optional, :class:`pymatgen.core.Structure`, :class:`pymatgen.io.vasp.inputs.Poscar` or :class:`aiida_core.data.StructureData`) --
  Optional structure input for initialization modes that are based on a k-point density.
  This is only required if the KPOINT grid is initialized using the internal methods based on a passed kpoint density.
  (See the initialization modes discussed in the :ref:`following section<inputs_kpoints_init_modes>` for more details)

.. _inputs_kpoints_init_modes:

Available initialization modes and their corresponding parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Passing a parameters dictionary to the :class:`~aiida_cusp.data.VaspKpointData` the passed dictionary may only contain the following keys:

* **mode** (:class:`str`) --
  The initialization mode to be used for the KPOINT generation.
  In general the :class:`~aiida_cusp.data.VaspKpointData` class supports the four distinct initialization modes: ``auto``, ``monkhorst``, ``gamma`` and ``line``
* **kpoints** (:class:`int`, :class:`float` or :class:`list`) --
  Defining the actual KPOINT grid

  .. note::

     The expected type passed for the ``kpoints`` depends on the initialization mode defined by the ``mode`` key.

* **shift** (:class:`list`) --
  Shift the kpoint grid by the defined amount

* **sympath** (:class:`~pymatgen.symmetry.bandstructure.HighSymmKpath`) --
  Path along high symmetry lines used in band structure calculations (i.e. only required if mode is set to ``line``)

In the following the different initialization modes and expected parameters are discussed in more detail.

Mode: auto
""""""""""

Setting the mode to ``auto`` the KPOINT grid initialized automatically using a single integer.
This corresponds to setting `Auto` in the KPOINT file.
In this mode the expected input parameters passed in the input dictionary are:

* **mode** (:class:`str`) --
  ``auto``
* **kpoints** (:class:`int`) --
  Integer used to automatically determine the grid's subdivisions
* **shift** (:class:`None`) --
  Unused by this mode
* **sympath** (:class:`None`) --
  Unused by this mode

**Example:** ::

  >>> auto_mode_params = {
  ...    'mode': 'auto',
  ...    'kpoints': 100,
  ... }
  >>> kpoints = VaspKpointData(kpoints=auto_mode_params)
  >>> print(kpoints.get_kpoints())
  Fully automatic kpoint scheme
  0
  Automatic
  100


Mode: monkhorst
"""""""""""""""

Setting the mode to ``monkhorst`` calls the internal KPOINT grid initialization for Monkhorst grids.
In this mode the expected input parameters passed in the input dictionary are:

* **mode** (:class:`str`) --
  ``monkhorst``
* **kpoints** (:class:`list` or :class:`float`) --
  Explicit 3x1 list of :class:`int` defining the grid's subdivisions or a kpoint density of type:class:`float`

  .. note::

     In case the kpoint grid is initialized from density the structure has to be passed to the constructor as well.
     However, the structure is not required for the initialization using an explicit kpoint grid.

* **shift** (:class:`list`) --
  3x1 list of :class:`float` defining the kpoint grid shift applied to the grid

  .. note::

     If the grid is initialized from a density (i.e. kpoints is of type :class:`float`) any defined shift is ignored.

* **sympath** (:class:`None`) --
  Unused by this mode

**Example for explicit kpoint grid:** ::

  >>> monkhorst_mode_params = {
  ...    'mode': 'monkhorst',
  ...    'kpoints': [2, 2, 2],
  ... }
  >>> kpoints = VaspKpointData(kpoints=monkhorst_mode_params)
  >>> print(kpoints.get_kpoints())
  Automatic kpoint scheme
  0
  Monkhorst
  2 2 2

**Example for kpoint density** ::

  >>> from pymatgen import Structure, Lattice
  >>> lattice = Lattice.cubic(1.0)
  >>> structure = Structure(lattice, ['H'], [[.0, .0, .0]])
  >>> monkhorst_mode_params = {
  ...    'mode': 'monkhorst',
  ...    'kpoints': 10.0,
  ... }
  >>> kpoints = VaspKpointData(kpoints=monkhorst_mode_params, structure=structure)
  >>> print(kpoints.get_kpoints())
  pymatgen v2020.4.29 with grid density = 10 / atom
  0
  Monkhorst
  2 2 2

Mode: gamma
"""""""""""

Setting the mode to ``gamma`` calls the internal KPOINT grid initialization for Gamma grids.
This initialization is basically equivalent to the previously discussed Monkhorst initialization mode but generates a Gamma grid
In this mode the expected input parameters passed in the input dictionary are:

* **mode** (:class:`str`) --
  ``gamma``
* **kpoints** (:class:`list` or :class:`float`) --
  Explicit 3x1 list of :class:`int` defining the grid's subdivisions or a kpoint density of type:class:`float`

  .. note::

     In case the kpoint grid is initialized from density the structure has to be passed to the constructor as well.
     However, the structure is not required for the initialization using an explicit kpoint grid.

* **shift** (:class:`list`) --
  3x1 list of :class:`float` defining the kpoint grid shift applied to the grid

  .. note::

     If the grid is initialized from a density (i.e. kpoints is of type :class:`float`) any defined shift is ignored.

* **sympath** (:class:`None`) --
  Unused by this mode

**Example for explicit kpoint grid:** ::

  >>> gamma_mode_params = {
  ...    'mode': 'gamma',
  ...    'kpoints': [2, 2, 2],
  ... }
  >>> kpoints = VaspKpointData(kpoints=gamma_mode_params)
  >>> print(kpoints.get_kpoints())
  Automatic kpoint scheme
  0
  Gamma
  2 2 2

**Example for kpoint density** ::

  >>> from pymatgen import Structure, Lattice
  >>> lattice = Lattice.cubic(1.0)
  >>> structure = Structure(lattice, ['H'], [[.0, .0, .0]])
  >>> gamma_mode_params = {
  ...    'mode': 'gamma',
  ...    'kpoints': 10.0,
  ... }
  >>> kpoints = VaspKpointData(kpoints=gamma_mode_params, structure=structure)
  >>> print(kpoints.get_kpoints())
  pymatgen v2020.4.29 with grid density = 10 / atom
  0
  Gamma
  2 2 2


Mode: line
""""""""""

Kpoint grids for bandstructure calculations can be generated by setting the mode to ``line``
Using line mode the expected input parameters passed in the input dictionary are:

* **mode** (:class:`str`) --
  ``line``
* **kpoints** (:class:`int`) --
  Integer value defining the number of kpoints for each path segment
* **shift** (:class:`None`) --
  Unused by this mode
* **sympath** (:class:`~pymatgen.symmetry.bandstructure.HighSymmKpath`) --
  :class:`~pymatgen.symmetry.bandstructure.HighSymmKpath` object defining a path along high symmetry lines in the Brillouin zone

**Example:** ::

  >>> from pymatgen import Structure, Lattice
  >>> from pymatgen.symmetry.bandstructure import HighSymmKpath
  >>> lattice = Lattice.cubic(1.0)
  >>> structure = Structure(lattice, ['H'], [[.0, .0, .0]])
  >>> sympath = HighSymmKpath(structure, path_type='sc')

  >>> line_mode_params = {
  ...     'mode': 'line',
  ...     'kpoints': 50,
  ...     'sympath': symmetry_path,
  ... }

  >>> kpoints = VaspKpointData(kpoints=line_mode_params)
  >>> print(kpoints.get_kpoints())
  Line_mode KPOINTS file
  50
  Line_mode
  Reciprocal
  0.0 0.0 0.0 ! \Gamma
  0.0 0.5 0.0 ! X

  0.0 0.5 0.0 ! X
  0.5 0.5 0.0 ! M

  0.5 0.5 0.0 ! M
  0.0 0.0 0.0 ! \Gamma

  0.0 0.0 0.0 ! \Gamma
  0.5 0.5 0.5 ! R

  0.5 0.5 0.5 ! R
  0.0 0.5 0.0 ! X

  0.5 0.5 0.0 ! M
  0.5 0.5 0.5 ! R


.. _KPOINT parameters: https://www.vasp.at/wiki/index.php/KPOINTS
