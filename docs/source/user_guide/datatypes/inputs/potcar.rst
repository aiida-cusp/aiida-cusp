.. _user-guide-datatypes-inputs-potcar:

POTCAR (``cusp.potcar``)
------------------------

The class :class:`~aiida_cusp.data.VaspPotcarData` is used to represent the VASP pseudo-potentials used as the inputs for a VASP calculation.
To this end the class implements the simple :meth:`~aiida_cusp.data.VaspPotcarData.from_structure` method that creates the pseudo-potential inputs for VASP calculations.
Based on the input structure and the optionally passed potcar names and versions this function queries the database for the requested potentials and automatically builds the list of potentials that can be passed via the calculation's `input.potcar` option (see also the :ref:`following section<user-guide-datatypes-inputs-potcar-generatepseudoinput>` and the :ref:`example<user-guide-datatypes-inputs-potcar-examples>` given at the end of this section)

.. note::

   Note that the :class:`~aiida_cusp.data.VaspPotcarData` class was introduced to respect the copyright enforced on the VASP pseudo-potentials.
   Because of that no actual contents of the original pseudo-potential are stored to this node to avoid any copyright infringement when exporting and sharing the calculation.
   Rather than storing the actual contents only a link to the corresponding pseudo-potential data stored in the database is added such that the node is independent of the underlying data.

.. _user-guide-datatypes-inputs-potcar-generatepseudoinput:

Generating Pseudo-Potential Inputs for VASP Calculations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automethod:: aiida_cusp.data.VaspPotcarData.from_structure
   :noindex:

.. _user-guide-datatypes-inputs-potcar-examples:

Example
^^^^^^^

In the following some examples are given to show how the :meth:`aiida_cusp.data.VaspPotcarData.from_structure` method can be used to initialize the pseudo-potential inputs for a VASP calculation.
To test this functionality a test structure is required.
In the following example a simple fcc structure is used to demonstrate the process of the pseudo-potential setup:

.. code-block:: python

   >>> from pymatgen import Structure, Lattice
   >>> from aiida.plugins import DataFactory
   >>> VaspPotcarData = DataFactory('cusp.potcar')
   >>> lattice = Lattice.cubic(3.524)
   >>> structure = Structure.from_spacegroup(225, lattice, ["Cu"], [[0.0, 0.0, 0.0]])

Simply passing the structure and the desired functional to the method without specifying any `potcar_params` initializes the pseudo-potential list with the default settings.
This means: For each element present in the structure the database is queried for a pseudo-potential with the defined functional and a potential name matching the element name.
From the list of potentials matching these requirements the potential with the highest version number will be return as input potential:

.. code-block:: python

   >>> potcar = VaspPotcarData.from_structure(structure, 'pbe')
   >>> potcar
   {'Cu': <VaspPotcarData: uuid: 0ea424b7-9b9e-446a-8d44-7690cb0006d7 (unstored)>}
   >>> print("{} {} {}".format(potcar['Cu'].name, potcar['Cu'].version, potcar['Cu'].functional))
   Cu 20010105 pbe

If your calculation requires a different potential, for instance the `Cu_pv` potential, the above shown default behavior can be overridden by passing the desired potential parameters to the function using the `potcar_params` dictionary.
To use the `Cu_pv` potential instead of the `Cu` potential, chosen by default, the following `potcar_params` need to passed:

.. code-block:: python

   >>> potcar = VaspPotcarData.from_structure(structure, 'pbe', potcar_params={'Cu': {'name': 'Cu_pv'}})
   >>> potcar
   {'Cu': <VaspPotcarData: uuid: c55928e9-3f3a-4d03-87f7-5b2c4be5fd9a (unstored)>}
   >>> print("{} {} {}".format(potcar['Cu'].name, potcar['Cu'].version, potcar['Cu'].functional))
   Cu_pv 20000906 pbe

Note that the `potcar_params` also allows a `'version'` key for each element to not only define the potential's name to be used but also potentially fix the potential's version.
However, since in the above example only the potential name is changed and the version remains unchanged (i.e. whatever highest version found) the above given is equivalent to passing the pseudo-potential name only:

.. code-block:: console

   >>> potcar = VaspPotcarData.from_structure(structure, 'pbe', potcar_params=['Cu_pv'])
   >>> potcar
   {'Cu': <VaspPotcarData: uuid: 1f6ea785-876f-4942-9f30-51a8eac39573 (unstored)>}
   >>> print("{} {} {}".format(potcar['Cu'].name, potcar['Cu'].version, potcar['Cu'].functional))
   Cu_pv 20000906 pbe
