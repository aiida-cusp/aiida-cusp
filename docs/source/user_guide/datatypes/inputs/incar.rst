.. _user-guide-datatypes-inputs-incar:

INCAR (``cusp.incar``)
----------------------

The :class:`~aiida_cusp.data.VaspIncarData` is the central object used to define and pass `INCAR parameters`_ to the VASP calculation object.
It is made available by the plugin using the ``cusp.incar`` entry point and can be loaded via AiiDA's :func:`~aiida.plugins.DataFactory` function.
Note that the class cannot be used directly as input for VASP calculations but has to be first initialized with the desired input parameters.
As discussed in the following, the parameters may be passed directly (i.e. as dictionary) or indirect via a pymatgen :class:`~pymatgen.io.vasp.inputs.Incar` instance.

Initializing the class
^^^^^^^^^^^^^^^^^^^^^^

In general the constructor of the :class:`~aiida_cusp.data.VaspIncarData` class is of the following form:

.. code-block:: python

   VaspIncarData(incar=None)

**Arguments:**

* **incar** (:class:`dict` or :class:`pymatgen.io.vasp.inputs.Incar`) --
  The INCAR parameters used to run a VASP calculation.
  May be given as :class:`~pymatgen.io.vasp.inputs.Incar` object which is useful if you want to use the parameters directly from a pymatgen set.
  Alternatively, if you do not use a pymatgen set the desired parameters may also be passed directly as :class:`dict` of the form

  .. code-block:: python

     incar_params = {
        'PARAM_1': VALUE_1,
        'PARAM_2': VALUE_2,
        ...
        'PARAM_N': VALUE_N,
     }

  In that case, the dictionary keys (``PARAM``) define the INCAR parameter to be set and the values (``VALUE``) the corresponding value.

Example
^^^^^^^

The following example illustrates how to initialize the :class:`aiida_cusp.data.VaspIncarData` object from an INCAR parameter :class:`dict`::

   >>> from aiida.plugins import DataFactory
   >>> IncarData = DataFactory('cusp.incar')
   >>> incar_params = {
   ...    'ALGO': 'Fast',
   ...    'EDIFF': 1.0E-6,
   ...    'EDIFFG': -0.01,
   ...    'LWAVE': False,
   ...    'MAGMOM': 56*[0.6],
   ... }
   >>> incar = IncarData(incar=incar_params)
   >>> print(incar)
   uuid: dc37533e-9d70-4493-8c6f-f51a503cd3e5 (unstored)
   >>> print(incar.get_incar())
   ALGO = Fast
   EDIFF = 1e-06
   EDIFFG = -0.01
   LWAVE = False
   MAGMOM = 56*0.6


.. _INCAR parameters: https://www.vasp.at/wiki/index.php/Category:INCAR
