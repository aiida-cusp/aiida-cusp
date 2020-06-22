.. _user-guide-custodian-handlers:

Custodian Error Handlers
========================

Custodian uses different error handlers to check and correcto for different failures of VASP calculations.
Thus, one can individually decide which error should be corrected and which error should fail the calculation and connect the corresponding handlers.
Error handlers for the calculations run with the calculation classes implemented in this plugin can be passed via the ``inputs.custodian.handlers`` input.
Here, the input is expected to be a dictionary of the following form:

.. code-block:: python

   handler_input = {
      'HandlerName1': {
          'option': 'value',
          ...
          },
      'HandlerName2': {
          'option', 'value',
          ...
          }
      ...
  }

In that case every dictionary entry corresponds to an individual handler specified by its name and the corresponding handler options to be used for it.
Note if an empty dictionary is passed as option to any handler, i.e. `'HandlerName': {}`, the plugin's default options are used for the handler.
Since one often wants to use the defined default for **all** handlers in the first place handlers may also be passed as a simple list of handler names.
In that case the default values are used for every defined handler and the example above would simplify to

.. code-block:: python

   handler_inputs = ['HandlerName1', 'HandlerName2', ...]

In the following all handlers available for VASP calculations are described in more detail and the available settings and their used defaults are shown.
(For more complete overview please refer to the original `Custodian documentation`_)


`'VaspErrorHandler'`
--------------------

Most basic error handler for VASP calculations checking for the most common VASP errors logged to the stdout output (i.e. Call to ZHEGV failed, TOO FEW BANDS, etc.)
(See also `VaspErrorHandler`_)

**Handler Settings:**

* **natoms_large_cell** (:class:`int`) --
  Number of atoms above which a structure is considered as large.
  This has implications on the strategy of resolving some kind of the errors (for instance whether LREAL should be set to True or False, etc.)
  (default: `100`)
* **errors_subset_to_catch** (:class:`list`) --
  List of errors that will be catched (other errors not in the list are ignored!).
  If set to `None` all errors known to the handler will be deteched.
  (default: :class:`None`)

  .. note::

     A complete list of errors known to the handler that may be passed in this list can be directly found from the VaspErrorHandler:

     .. code-block:: python

        >>> from custodian.vasp.handlers import VaspErrorHandler
        >>> known_errors = list(VaspErrorHandler.error_msgs.keys())
        >>> for error in known_errors:
        ...    print(error)
        ...
        tet
        inv_rot_mat
        brmix
        subspacematrix
        tetirr
        incorrect_shift
        real_optlay
        rspher
        dentet
        too_few_bands
        triple_product
        rot_matrix
        brions
        pricel
        zpotrf
        amin
        zbrent
        pssyevx
        eddrmm
        edddav
        grad_not_orth
        nicht_konv
        zheev
        elf_kpar
        elf_ncl
        rhosyg
        posmap
        point_group



`'FrozenJobErrorHandler'`
-------------------------

Considers a calulation as frozen if the output to stdout is not updated for a defined amount of time and restarts the job if frozen.
(See also `FrozenJobErrorHandler`_)

.. warning::

   If using this handler do not set the timeout too low for demanding calculations with many atoms and / or a dense kpoint grid!

**Handler Settings:**

* **timeout** (:class:`int`) --
  Seconds without activity on the stdout output after which the job is considered as frozen
  (default: `21600`)


`'PotimErrorHandler'`
---------------------

Check for positive energy changes in electronic steps (dE) larger than the defined threshold and reduce POTIM parameter accordingly.

**Handler Settings:**

* **dE_threshold** (:class:`float`) --
  Maximum threshold (in eV) for energy changes between consecutive electronic steps.
  For energy changes larger than the defined value the handler will restart the calculation with reduced POTIM parameter
  (default: `1.0`)


`'NonConvergingErrorHandler'`
-----------------------------

Check if NELM is reach for ``nionic_steps`` consecutive ionic steps and correct by first switching to more stable algorithms (ALGO) and secondly ajusting the mixing parameters (AMIX, BMIX, BMIN).
(See also `NonConvergingErrorHandler`_)

**Handler Settings:**

* **nionic_steps** (:class:`int`) --
  Number of consecutive ionic steps with the maximum number of electronic steps being reached before considered an error.
  (default: `10`)


`'DriftErrorHandler'`
---------------------

Checks if the final drift exceeds the force convergence criterion defined by *EDIFFG* tag and restarts if true.
(See also `DriftErrorHandler`_)

**Handler Settings:**

* **max_drift** (:class:`float`) --
  Defines the maximal acceptable drift. If set to `None` the value is set to the supplied value defined by *EDIFFG* in the *INCAR* parameters.
  (default: `None`)
* **to_average** (:class:`int`) --
  Demand at least that many steps to calculate the average drift
  (default: `3`)
* **enaug_multiply** (:class:`int`) --
  Value used to multiply the value of *ENAUG* found from the *INCAR* parameters when restarting the calculation
  (default: `2`)


`'WalltimeHandler'`
-------------------

Write a STOPCAR to the calculation folder if the calculation's runtime approaches the defined wall time.
(See also `WalltimeHandler`_)

**Handler Settings:**

* **wall_time** (:class:`int`) --
  Total wall time of the job in seconds.
  (If running using the PBS scheduler this value is retrieved from the PBS_WALLTIME environment variable if not set here)
  (default: `None`)
* **buffer_time** (:class:`int`) --
  Buffer time in seconds between writing the STOPCAR and the total wall time is reached.
  Note that if the average time required to complete 3 ionic steps is larger the set buffer_time this value will be used as buffer_time.
  (default: `300`)
* **electronic_step_stop** (:class:`bool`) --
  If set to `True` compare the defined buffer_time to the time required to complete electronic steps rather than ionic steps.
  (default: `False`)


`'StdErrHandler'`
-----------------

Handler checking for common errors only written to stderr.
(See also `StdErrHandler`_)

**Handler Settings:**

* This handler does not provide any custom settings


`'AliasingErrorHandler'`
------------------------

Corrects for aliasing (small wrap around) errors encountered for insufficient FFT grids.
(See also `AliasingErrorHandler`_)


**Handler Settings:**

* This handler does not provide any custom settings


`'UnconvergedErrorHandler'`
---------------------------

Check for both ionic and electronic convergence and restart the job with different strategies if convergence was not reached.
(See also `UnconvergedErrorHandler`_)

**Handler Settings:**

* This handler does not provide any custom settings


`'PositiveEnergyErrorHandler'`
------------------------------

Check for a positive absolute energy at the end of a calculation and restart with ALGO=Normal (Stops calculation is ALGO is already set to Normal).
(See also `PositiveEnergyErrorHandler`_)

**Handler Settings:**

* This handler does not provide any custom settings


`'MeshSymmetryErrorHandler'`
----------------------------

Check for symmetry errors and switch off symmetry (i.e. set ISYM=0) if reciprocal lattices and kpoint lattices belong to different classes of lattices.
(See also `MeshSymmetryErrorHandler`_)

**Handler Settings:**

* This handler does not provide any custom settings


`'LrfCommutatorErrorHandler'`
-----------------------------

Checks for *LRF_COMMUTATOR* errors corrects the error by switching to finit-differences when calculating the cell-periodic derivative or orbitals (i.e. sets LPEAD=True).
(See also `LrfCommutatorErrorHandler`_)

**Handler Settings:**

* This handler does not provide any custom settings


.. _Custodian documentation: https://materialsproject.github.io/custodian/
.. _AliasingErrorHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.AliasingErrorHandler
.. _DriftErrorHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.DriftErrorHandler
.. _FrozenJobErrorHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.FrozenJobErrorHandler
.. _LrfCommutatorErrorHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.LrfCommutatorHandler
.. _MeshSymmetryErrorHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.MeshSymmetryErrorHandler
.. _NonConvergingErrorHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.NonConvergingErrorHandler
.. _PositiveEnergyErrorHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.PositiveEnergyErrorHandler
.. _PotimErrorHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.PotimErrorHandler
.. _StdErrHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.StdErrHandler
.. _UnconvergedErrorHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.UnconvergedErrorHandler
.. _VaspErrorHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.VaspErrorHandler
.. _WalltimeHandler: https://materialsproject.github.io/custodian/custodian.vasp.html#custodian.vasp.handlers.WalltimeHandler
