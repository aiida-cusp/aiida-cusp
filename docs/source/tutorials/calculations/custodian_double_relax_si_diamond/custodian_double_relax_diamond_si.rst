.. _tutorials-calculations-si-diamond-structure-double-relaxation:

Double Relaxation of a Si Diamond Structure using Custodian
===========================================================

Topics covered in this tutorial:

* Setting up calculation inputs
* Setting up an (error corrected) VASP calculation
* Add multiple Custodian jobs to the Calculation
* Access generated outputs

Introduction
------------

In this (simple) tutorial the :class:`~aiida_cusp.calculators.VaspCalculation` calculator of this plugin is used to perform a double relaxation run.
In particular, the double relaxation is performed solely using Custodian using a two job workflow provided by the Custodian package that is directly connected to the AiiDA calculation.
Here, a simple silicon diamond structure is used as an example on which the double relaxation is performed.

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
   lattice = Lattice.cubic(5.231)
   species = ["Si"]
   coords = [[0.0, 0.0, 0.0]]
   si_diamond_structure = Structure.from_spacegroup(227, lattice, species, coords)
   si_diamond_structure.perturb(0.1)

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
   incar_params = {'ISIF': 3, 'NSW': 100, 'IBRION': 1, 'EDIFFG': -0.1}
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

and one custodian code that will be used for the error correction and execution of the connected jobs:

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

In order to finally run the Custodian double relaxation we also need to add the corresponding jobs to the calculation.
To do so we first need to add the Custodian executable, defined by the `custodian_2020427@CompMPI` code object


, and the error handlers we want to use to the calculation as additional inputs:

.. code-block:: python

   # add the **additional** custodian code to the calculation inputs
   VaspSiRelax.custodian.code = Code.get_from_string('custodian_2020427@CompMPI')

With the custodian code added to the calculation, we can now also assign the jobs, required to run the double relaxation, to the calculation:

.. code-block:: python

   # add the double relaxation jobs to the `custodian.jobs` keyword
   from custodian.vasp.jobs import VaspJob
   double_relax_jobs = VaspJob.double_relaxation_run(None)
   VaspSiRelax.custodian.jobs = double_relax_jobs

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
   1664  43s ago    VaspCalculation       ⏵ Waiting        Monitoring scheduler: job state RUNNING

Inspecting the Outputs
----------------------

After the job has finished the automatically connected default :class:`~aiida_cusp.parsers.vasp_file_parser.VaspFileParser` will add the generated `vasprun.xml`, `OUTCAR` and `CONTCAR` files as outputs to the stored calculation node.
In general, all parsed calculation outputs are defined to the `outputs.parsed_results` namespace.
However, if multiple custodian jobs are defined, a sub-namespace is created for all defined job-suffixes, to which the parsed files for each individual job are stored.
In case of the discussed double relaxation, the generated process output section (available via the `verdi process show` command) would therefore look like

.. code-block:: bash

   Outputs              PK    Type
   -------------------  ----  ---------------
   parsed_results
       relax1
           contcar      1667  VaspContcarData
           vasprun_xml  1669  VaspVasprunData
           outcar       1671  VaspOutcarData
       relax2
           contcar      1668  VaspContcarData
           vasprun_xml  1670  VaspVasprunData
           outcar       1672  VaspOutcarData
   remote_folder        1665  RemoteData
   retrieved            1666  FolderData

To access a file available from the node that is stored in a specific sub-namespace we simple extend the `outputs.parsed_results` namespace with the corresponding sub-namespace.
As an example, we extract the calculated lattice constants obtained from the just performed double relaxation run using the parsed `CONTCAR` of the first and second relaxation run (i.e. the calculations with suffix `.relax1` and `.relax2` whose files have thus been stored to the `relax1` and `relax2` sub-namespace, respectively)
Using the `PK` of the stored calculation node, printed next to the running calculation in the output of `verdi process list` (see above), the nodes can be loaded from the database using AiiDA's :func:`~aiida.orm.utils.loaders.load_node` function.
In the following a `verdi shell`_ is used to load the `CONTCAR` nodes and to retrieved the lattice constants of both calculations by inspecting the loaded nodes' outputs:

.. code-block:: python

   >>> from aiida.orm import load_node
   >>> si_double_relax_node = load_node(1664)
   >>> si_double_relax_node
   <CalcJobNode: uuid: 5e27556c-3ba6-42ee-a8d2-f81c6b56fe44 (pk: 1664) (aiida.calculations:cusp.vasp)>
   >>> contcar_relax1 = si_relax_node.outputs.parsed_results.relax1.contcar
   >>> contcar_relax1
   <VaspContcarData: uuid: af951a4e-f138-4152-8ce0-d4334bbf3e65 (pk: 1667)>
   >>> contcar_relax2 = si_relax_node.outputs.parsed_results.relax2.contcar
   >>> contcar_relax2
   <VaspContcarData: uuid: f557cec6-2552-4008-8011-422019d421c8 (pk: 1668)>

Since the plugin tightly integrates AiiDA with the Pymatgen framework we can easily get to the lattice constants of both output structures (and actually many more quantities) using the :meth:`~aiida_cusp.data.VaspPoscarData.get_structure` method inherited by the :class:`~aiida_cusp.data.VaspContcarData` class:

.. code-block:: python

   >>> structure_relax1 = contcar_relax1.get_structure()
   >>> structure_relax2 = contcar_relax2.get_structure()
   >>> print(type(structure_relax1))
   <class 'pymatgen.core.structure.Structure'>
   >>> print(type(structure_relax2))
   <class 'pymatgen.core.structure.Structure'>
   # print out the lattice constants
   >>> print(f"Relax1 abc = {structure_relax1.lattice.abc} (Angstrom)")
   Relax1 abc = (5.465553969593606, 5.465016691078316, 5.46511582291087) (Angstrom)
   >>> print(f"Relax2 abc = {structure_relax2.lattice.abc} (Angstrom)")
   Relax2 abc = (5.465510440923655, 5.465511092210795, 5.4655567623820325) (Angstrom)


Copy-and-Paste
--------------

.. code-block:: python

   from pymatgen.core import Lattice, Structure
   from custodian.vasp.handlers import VaspErrorHandler
   from custodian.vasp.jobs import VaspJob

   from aiida.orm import Code
   from aiida.plugins import CalculationFactory, DataFactory
   from aiida.engine import submit, run

   # setup the code-labels defining the codes to be used
   vasp_code_label = 'place_your_vasp_code_label_here'
   custodian_code_label = 'place_your_custodian_code_label_here'


   # define all input datatypes
   VaspIncarData = DataFactory('cusp.incar')
   VaspKpointData = DataFactory('cusp.kpoints')
   VaspPoscarData = DataFactory('cusp.poscar')
   VaspPotcarData = DataFactory('cusp.potcar')

   # setup the silicon diamond structure
   lattice = Lattice.cubic(5.231)
   species = ["Si"]
   coords = [[0.0, 0.0, 0.0]]
   si_diamond_structure = Structure.from_spacegroup(227, lattice, species, coords)
   si_diamond_structure.perturb(0.1)

   # define calculation inputs
   incar = VaspIncarData(incar={'ISIF': 3, 'NSW': 100, 'IBRION': 1, 'EDIFFG': -0.1})
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

   # this will setup two different, custodian controlled jobs with suffixes
   # '.relax1' and '.relax2'
   jobs = VaspJob.double_relaxation_run(None)
   VaspSiRelax.custodian.code = custodian_code
   VaspSiRelax.custodian.handlers = VaspErrorHandler()
   VaspSiRelax.custodian.jobs = jobs

   # submit calculation the daemon
   node = submit(VaspSiRelax)

   # print out the PK of the submitted job
   print("Submitted VaspSiRelax with PK: {}".format(node.pk))

.. _AiiDA scheduler documentation: https://aiida-core.readthedocs.io/en/stable/scheduler/index.html#supported-schedulers
.. _verdi shell: https://aiida-core.readthedocs.io/en/stable/working_with_aiida/scripting.html#verdi-shell
