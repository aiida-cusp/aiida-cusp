.. _tutorials-calculations-si-diamond-structure:

Relaxation of a Si Diamond Structure
====================================

Topics covered in this tutorial:

* Setting up calculation inputs
* Setting up an (error corrected) VASP calculation
* Access generated outputs

Introduction
------------

In this (simple) tutorial the :class:`~aiida_cusp.calculators.VaspCalculation` calculator of this plugin is used to run an error corrected VASP calculation.
In particular, a silicon diamond structure is relaxed and finally the ground state energy per Si atom is calculated for the relaxed structure.

Setting up the Inputs
---------------------

Before we can start the calculation we need to setup all the required inputs.
As every normal VASP calculation the plugin also requires the basic VASP inputs to be provided, i.e.

* `POSCAR`
* `INCAR`
* `KPOINTS`
* `POTCAR`

We will start in the following with setting up the structure inputs for the silicon diamond relaxation.
To this end we first need to setup the silicon diamond structure.
Since the plugin is tightly connected to pymatgen's data types the structure is setup using pymatgen:

.. code-block:: python

   from pymatgen.core import Lattice, Structure
   lattice = Lattice.cubic(5.431)
   species = ["Si"]
   coords = [[0.0, 0.0, 0.0]]
   si_diamond_structure = Structure.from_spacegroup(227, lattice, species, coords)

Using this structure we can now directly setup the required `POSCAR` data for the calculation expecting a :class:`~aiida_cusp.data.VaspPoscarData` as input:

.. code-block:: python

   from aiida.plugins import DataFactory
   VaspPoscarData = DataFactory('cusp.poscar')
   poscar = VaspPoscarData(structure=si_diamond_structure)

.. note::

   You're not restricted to the pymatgen structure type here but you may also initialize the :class:`~aiida_cusp.data.VaspPotcarData` from several other types, i.e.:
   :class:`~pymatgen.io.vasp.inputs.Poscar` or :class:`~aiida.orm.nodes.data.structure.StructureData` are also accepted input types.

With the `POSCAR` data now being set we are already done with the structure setup for our calculation.
Next we define the `INCAR` parameters for the calculation allowing for a full cell relaxation of the passed structure (i.e. `ISIF=3`).
As this is only a tutorial and not a serious calculation we, of course, want the calculation to finish quickly.
Thus, a not very sophisticated force-convergence threshold of `EDIFFG=-0.1` is chosen for the tutorial.
The expected input for the `INCAR` parameters is of type :class:`~aiida_cusp.data.VaspIncarData` and we can set it up by simply passing a dictionary containing the `INCAR` settings we want to apply for the calculation:

.. code-block:: python

   VaspIncarData = DataFactory('cusp.incar')
   incar_params = {'ISIF': 3, 'EDIFFG': -0.1}
   incar = VaspIncarData(incar=incar_params)


For the `KPOINTS` parameters we also use a rather sparse grid.
In the following the grid is setup using the automatic method:

.. code-block:: python

   VaspKpointData = DataFactory('cusp.kpoints')
   kpoint_params = {'mode': 'auto', 'kpoints': 100}
   kpoints = VaspKpointData(kpoints=kpoint_params)

Finally, we setup the last missing input: the pseudo-potential.
For the pseudo-potential the :class:`~aiida_cusp.data.VaspPotcarData` type is expected by the calculator.
Here, the pseudo-potentials have to be passed as dictionary with key-value pairs where each key defines an element present in the `POSCAR` data with the pseudo-potential that should be used for the element as value.
However, we do not need to construct this dictionary by hand: We simply use the :meth:`~aiida_cusp.data.VaspPotcarData.from_structure` method and let the function do the job.
For the calculation we use the default PBE potential for silicon (i.e. the pseudo-potential with name `'Si'`):

.. code-block:: python

   VaspPotcarData = DataFactory('cusp.potcar')
   potcar = VaspPotcarDara.from_structure(poscar, 'pbe')

which initializes a dictionary containing a single entry of the following form

.. code-block:: python

   {'Si': <VaspPotcarData: uuid: 1f6ea785-876f-4942-9f30-51a8eac39573 (unstored)>}

.. note::

   Before you can initialize the pseudo-potential data using the aforementioned :meth:`~aiida_cusp.data.VaspPotcarData.from_structure` you have to add the required potentials to the database.
   This can be easily done using the implemented ``verdi data potcar add`` command.
   For the required silicon pseudo-potential this command could look like the following:

   .. code-block:: console

      $ verdi data potcar add single --name "Si" --functional "pbe" /vasp_pseudos/potpaw_PBE/Si/POTCAR

   Please refer to the :ref:`potcar command documentation<user-guide-commands-potcar>` for a detailed introduction to the command and the expected parameters and their meanings.

Preparing and Running the Calculation
-------------------------------------

Since we now have defined all required inputs we are ready to setup and finally also run the calculation.
To setup the calculation we need to define a code that should be used to run the VASP calculation.
We can check for available codes using the ``verdi code list`` command which will list all codes available in the database:

.. code-block:: console

   $ verdi code list
   # List of configured codes:
   # (use 'verdi code show CODEID' to see the details)
   * pk 1228 - vasp_5.4.1_openmpi_4.0.3_scalapack_2.1.0@CompMPI
   * pk 1271 - custodian_2020427@CompMPI
   * pk 1366 - vasp_5.4.1_openmpi_4.0.3_scalapack_2.1.0_vtst@CompMPI

Here, three different codes are available from the database, two VASP codes

* `vasp_5.4.1_openmpi_4.0.3_scalapack_2.1.0@CompMPI`
* `vasp_5.4.1_openmpi_4.0.3_scalapack_2.1.0_vtst@CompMPI`

and one custodian code that can be used for the error correction

* `custodian_2020427@CompMPI`

In the following the `vasp_5.4.1_openmpi_4.0.3_scalapack_2.1.0@CompMPI` code is used to run the calculation.
To connect the code and setup the calculation we first load the corresponding builder for the VASP calculator :class:`aiida_cusp.calculators.VaspCalculation` implemented by this plugin.

.. code-block:: python

   from aiida.plugins import CalculationFactory
   VaspSiRelax = CalculationFactory('cusp.vasp').get_builder()

Using the returned builder we can now simply add our inputs to the calculation.
For the VASP code and the required calculation inputs, setup in the previous step, this could look like the following

.. code-block:: python

   from aiida.orm import Code
   # setup the VASP code
   VaspSiRelax.code = Code.get_from_string('vasp_5.4.1_openmpi_4.0.3_scalapack_2.1.0@CompMPI')
   resources = {'tot_num_mpiprocs': 4, 'num_machines': 1}
   VaspSiRelax.metadata.options.resources = resources
   # setup the VASP calculation inputs
   VaspSiRelax.incar = incar
   VaspSiRelax.kpoints = kpoints
   VaspSiRelax.poscar = poscar
   VaspSiRelax.potcar = potcar

.. note::

   Note the added resources for the job defined via the `metadata.options.resources` option.
   These define the calculation jobs resources the scheduler acquires upon submission, i.e. the number of cores and machines to be used on the computer to run the job.
   As the settings defined here usually depend on the type of scheduler you are using, please refer to the `AiiDA scheduler documentation`_ for the options available for your scheduler.

Finally, we want to run the VASP calculation defined by the above inputs with automated error correction using Custodian.
To do so we need to add the Custodian executable, defined by the `custodian_2020427@CompMPI` code object, and the error handlers we want to use to the calculation as additional inputs:

.. code-block:: python

   # enable error correction by adding an  **additional** custodian code ...
   VaspSiRelax.custodian.code = Code.get_from_string('custodian_2020427@CompMPI')
   # ... and the corresponding custodian error handlers
   VaspSiRelax.custodian.handlers = ['VaspErrorHandler']

In the above example only a single error handlers, i.e. the `'VaspErrorHandler'`, is set in the calculation and the default settings as defined by the plugin are used for the connected Custodian code.
For a complete overview of the available error handlers and the available Custodian settings that may be set for the code, please refer to the :ref:`Custodian section<user-guide-custodian>` of this documentation.

.. note::

   You can also run this example without error corrections by simply leaving the `VaspSiRelax.custodian.code` and `VaspSiRelax.custodian.handler` inputs empty (those inputs are optional!)
   In that case the calculator will call the VASP executable defined by the code given in the `VaspSiRelax.code` input directly instead of wrapping VASP with Custodian.

With all required inputs defined, we are now ready to run the code.
The following code shows how the calculation can be submitted to the AiiDA daemon via the :func:`~aiida.engine.launch.submit` function provided by the :mod:`aiida.engine` module:

.. code-block:: python

   from aiida.engine import submit
   node = submit(VaspSiRelax)

.. note::

   If you want to run the calculation in your interpreter replace the used :func:`~aiida.engine.launch.submit` function with the :func:`~aiida.engine.launch.run` function.

We can check that the calculation was indeed submitted to the daemon by checking the output of the ``verdi process list`` command which should now list our submitted calculation as running process:

.. code-block:: console

   $ verdi process list
     PK  Created    Process label         Process State    Process status
   ----  ---------  --------------------  ---------------  ---------------------------------------
   1377  43s ago    VaspCalculation       ⏵ Waiting        Monitoring scheduler: job state RUNNING

Inspecting the Outputs
----------------------

After the job has finished the automatically connected default :class:`~aiida_cusp.parsers.vasp_file_parser.VaspFileParser` will add the generated `vasprun.xml`, `OUTCAR` and `CONTCAR` files as outputs to the stored calculation node.
As the stored files are available from the node using the `outputs.parsed_results` namespace we can easily determine the energy per Si atom in the relaxed structure using the parsed `vasprun.xml` file by loading the calculation node and inspecting the stored file contents.
Using the `PK` of the stored calculation node printed, next to the running calculation in the output of `verdi process list` (see above), the node can be loaded from the database using AiiDA's :func:`~aiida.orm.utils.loaders.load_node` function.
In the following a `verdi shell`_ is used to load the node and calculated the energy per Si atom by inspecting the loaded node's outputs:

.. code-block:: python

   >>> from aiida.orm import load_node
   >>> si_relax_node = load_node(1377)
   >>> print(si_relax_node)
   uuid: f97a5909-6a3d-4cec-b4ea-39a69a3a125e (pk: 1337)
   >>> print(si_relax_node.outputs.parsed_results__vasprun_xml)
   <VaspVasprunData: uuid: 136e55a1-b1d4-4aeb-9661-8830808552f5 (pk: 1339)>

Since the plugin tightly integrates AiiDA with the Pymatgen framework we can easily get to the total energy of the system (and actually many more quantities) using the :meth:`~aiida_cusp.data.VaspVasprunData.get_vasprun` method implemented by the :class:`~aiida_cusp.data.VaspVasprunData` class:

.. code-block:: python

   >>> pymatgen_vasprun = si_relax_node.outputs.parsed_results.vasprun_xml.get_vasprun()
   >>> print(type(pymatgen_vasprun))
   <class 'pymatgen.io.vasp.outputs.Vasprun'>
   >>> total_energy = float(pymatgen_vasprun.final_energy)
   >>> num_atoms = float(len(pymatgen_vasprun.final_structure))
   >>> energy_per_atom = total_energy / num_atoms
   >>> print("Energy per atom: {} (eV/atom)".format(energy_per_atom))
   Energy per atom: -5.41045657375 (eV/atom)


Copy-and-Paste
--------------

.. code-block:: python

   from pymatgen.core import Lattice, Structure
   from aiida.orm import Code
   from aiida.plugins import CalculationFactory, DataFactory
   from aiida.engine import submit

   # setup the code-labels defining the codes to be used
   vasp_code_label = 'place_your_vasp_code_label_here'
   custodian_code_label = 'place_your_custodian_code_label_here'

   # define all input datatypes
   VaspIncarData = DataFactory('cusp.incar')
   VaspKpointData = DataFactory('cusp.kpoints')
   VaspPoscarData = DataFactory('cusp.poscar')
   VaspPotcarData = DataFactory('cusp.potcar')

   # setup the silicon diamond structure
   lattice = Lattice.cubic(5.431)
   species = ["Si"]
   coords = [[0.0, 0.0, 0.0]]
   si_diamond_structure = Structure.from_spacegroup(227, lattice, species, coords)

   # define calculation inputs
   incar = VaspIncarData(incar={'ISIF': 3, 'EDIFFG': -0.1})
   poscar = VaspPoscarData(structure=si_diamond_structure)
   potcar = VaspPotcarData.from_structure(poscar, 'pbe')
   kpoints = VaspKpointData(kpoints={'mode': 'auto', 'kpoints': 25})

   # fetch codes from the AiiDA database
   vasp_code = Code.get_from_string(vasp_code_label)
   custodian_code = Code.get_from_string(custodian_code_label)

   # setup the calculation object
   VaspSiRelax = CalculationFactory('cusp.vasp').get_builder()
   resources = {'tot_num_mpiprocs': 4, 'num_machines': 1}
   VaspSiRelax.metadata.options.resources = resources
   VaspSiRelax.code = vasp_code
   VaspSiRelax.incar = incar
   VaspSiRelax.poscar = poscar
   VaspSiRelax.potcar = potcar
   VaspSiRelax.kpoints = kpoints

   # optional inputs for the custodian error correction (skip this if you
   # do not want to enable error correction)
   VaspSiRelax.custodian.code = custodian_code
   VaspSiRelax.custodian.handlers = ['VaspErrorHandler']

   # submit calculation the daemon
   node = submit(VaspSiRelax)

   # print out the PK of the submitted job
   print("Submitted VaspSiRelax with PK: {}".format(node.pk))

.. _AiiDA scheduler documentation: https://aiida-core.readthedocs.io/en/stable/scheduler/index.html#supported-schedulers
.. _verdi shell: https://aiida-core.readthedocs.io/en/stable/working_with_aiida/scripting.html#verdi-shell
