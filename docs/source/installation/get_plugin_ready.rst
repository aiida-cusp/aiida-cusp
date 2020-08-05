.. _installation-getpluginready:

************************
Getting the Plugin Ready
************************

For the steps discussed in the following a working AiiDA installation is expected, i.e.

* AiiDA and a corresponding database has been setup already
* all services (i.e. postgresql, rabbitmq and the daemon) are up and running
* a computer is already configured and the next logical step is to add a(nother) code for it

If the above is not true for your installation, please complete the AiiDA installation before proceeding.

.. note::

   Although the plugin installation automatically installs AiiDA to the plugin's environment you still need to manually configure and setup the new AiiDA installation.
   In case you are new to AiiDA please refer to the `AiiDA documentation`_ for detailed instructions on how to setup a new AiiDA installation and it's related services.

.. _installation-getpluginready-setupcustodian:

Setting up the Custodian Codes
==============================

Setting up the codes for Custodian is straightforward and does in general not differ compared to the `setup of regular codes <https://aiida.readthedocs.io/projects/aiida-core/en/latest/howto/run_codes.html#how-to-setup-a-code>`_.
Similar to setting up the VASP code which tells AiiDA how to load and access the corresponding ``vasp`` executable, Custodian codes are setup to give AiiDA the same information on the ``cstdn`` executable.
The only reason for the Custodian code setup being covered in more detail here is the fact that it may likely not be available on your system by default and thus may required some extra steps to setup.

.. note::

   In case Custodian is already available on your system you may skip the following steps and directly setup the code as usual.
   To check if Custodian is already available simply you can simply test if the  ``cstdn`` executable is available, for instance using the command

   .. code:: console

      $ module load anaconda
      $ conda activate aiida-cusp-dev
      $ which cstdn
      /home/andreas/local/apps/anaconda3/2019.3/envs/aiida-cusp-dev/bin/cstdn

Assuming the above check has failed for you and Custodian is obviously not available on your system yet, the following example shows how to install and setup the code through anaconda.

.. note::

   Keep in mind that the example shown in the following is only one possibility of installing Custodian on your system.
   The solution best suited for your use case, of course, depends on the available python installation and your personal preferences.
   Thus, consider the given example as a basic guide giving you a general idea of the required installation steps

.. warning::

   Custodian has to be installed on the **target computer** that is later used to run the calculation (i.e. usually the same computer where also VASP is installed).
   Keep in mind that this computer may be different from the computer running your AiiDA installation!


To setup the Custodian code on a remote computer using anaconda we first create a new environment containing the Custodian installation.
Using ``custodian`` for the environment name the required ``conda`` command could look like the following

.. code:: console

   $ conda create --name custodian python=3.6 custodian

After the installation is completed you may check that custodian was indeed installed.
To do this simply activate the created environment and perform the above mentioned check for the ``cstdn`` executable:

.. code:: console

   $ conda activate custodian
   $ which cstdn
   /home/user/envs/custodian/bin/cstdn

If the the full path to the ``cstdn`` executable is printed to the screen the installation was successful.
Note that the printed path should point to the folder in which the new Anaconda environment was installed previously.
After installing the required executable, the next step is now to setup the code on your local computer (i.e. the computer you're actually running AiiDA on!)
To setup the code simply run the ``verdi code setup`` command and provide all the necessary information you're asked for.
(Please refer to the `AiiDA documentation <https://aiida.readthedocs.io/projects/aiida-core/en/latest/howto/run_codes.html#how-to-setup-a-code>`_ for detailed instructions on how to setup a new code)

.. note::

   When asked for the input plugin, choose the ``cusp.vasp`` entry-point in order to connect the code to the plugin's calculator.
   At the very end of the setup the code's prepend / append sections are requested: Please make sure the Custodian installation is made available at the code's loading time by adding the appropriate commands to the requested prepend section
   (See the example below)

After successful code setup you may run the `verdi code show` command  on your newly configured Custodian code which should give an output similar to the following:

.. code:: console

   $ verdi code show Custodian@RemoteComputer
   --------------------  ----------------------------------------------------
   PK                    14166
   UUID                  ec3d6056-4d9c-452b-8453-410b28e7a126
   Label                 Custodian
   Description           Custodian code on remote Computer
   Default plugin        cusp.vasp
   Type                  remote
   Remote machine        RemoteComputer
   Remote absolute path  /home/user/envs/custodian/bin/cstdn
   Prepend text
                         module load anaconda                                  # load anaconda module and conda command
                         source "$(conda info --base)/etc/profile.d/conda.sh"  # make 'conda activate' command available
                         conda activate custodian                              # load the actual environment and add cstdn to PATH
   Append text           No append text
   --------------------  ----------------------------------------------------

.. _installation-getpluginready-preparepseudos:

Populating the Database with VASP Pseudo-Potentials
===================================================

With the code now being setup we're almost set to run the first calculation.
However, before doing so we first need to populate the AiiDA database with appropriate pseudo-potentials.
To this end the plugin extends the ``verdi data`` command with the additional ``potcar`` sub-command.
This new sub-command allows to interact with VASP pseudo-potential files and offers two different ways of adding potentials:

 * adding only single potentials using ``verdi data potcar add single``
 * or adding a batch of potentials at once using ``verdi data potcar add family``

.. note::

   Type ``verdi data potcar --help`` on the command line to get more information on the provided commands and the expected syntax.
   The command is also documented :ref:`here<user-guide-commands-potcar>`.

In the following, only a single pseudo-potential for silicon, required to run the calculation example presented in the next section, is added to the database.
As stated above a single pseudo-potential may be added to the database using the ``verdi data potcar add single`` command, thus:

.. code:: console

   $ verdi potcar add single /home/andreas/plugin_dev/testing/potcar/potpaw_PBE/Si/POTCAR --name Si --functional pbe

   New pseudo-potential(s) to be stored:

   name    element    functional      version  path
   ------  ---------  ------------  ---------  -------------------------------------------------------------------------------
   Si      Si         pbe            19990402  /home/andreas//plugin_dev/testing/potcar/potpaw_PBE/Si/POTCAR

   File location: /home/andreas/plugin_dev/testing/potcar/potpaw_PBE/Si/POTCAR

   Discovered a total of 1 POTCAR file(s) of which
           1       will be stored to the database,
           0       are already available in the database and
           0       will be skipped due to errors

   Before continuing, please check the displayed list for possible errors! Continue and store? [y/N]: y
   Created new VaspPotcarFile node with UUID c6dd3acc-7ffe-44de-b638-4dff4ff8bab8 at ID 918

Check the printed summary to check if the potential was recognized correctly and press ``Y`` to continue and save the potential with the shown attributes to the database.

.. note::

   In later calculations you can choose from the different stored potentials by referencing to the ``name``, ``functional`` and ``version`` printed to the screen when adding the potential.
   Fixing all of the three attributes uniquely defines a pseudo-potential which is the reason why these attributes are used as potential identifiers throughout this plugin.

   If you want know which potentials are already stored, use the ``vasp data potcar list`` command to get an overview of the available potentials, i.e.

   .. code:: console

      $ verdi data potcar list --element Si

      Showing available pseudo-potentials for
              name:       all
              element:    Si
              functional: all

        id  uuid                                  name         element    functional
      ----  ------------------------------------  -----------  ---------  ------------
       209  d31eea80-f1fc-432c-b68d-1553f44f73a8  Si_d_GW_nr   Si         pbe
       210  bee20ab8-8b38-4255-9885-ab7e53605678  Si_d_GW      Si         pbe
       211  47787525-9dc1-4c8b-a327-72dd6223df96  Si_h_old     Si         pbe
       212  1991a70b-440a-4626-ac27-330b4b546b7e  Si_h         Si         pbe
       213  6730058f-e2d9-4a51-baa1-cee8887f9a70  Si_nopc      Si         pbe
       214  b8d542b6-dd56-49b3-8e57-6281b4971ff7  Si           Si         pbe
       215  d832b49d-6c36-469e-afef-0fc8b8533fb3  Si_pv_GW     Si         pbe
       216  c19da65f-c696-4d02-bdbe-c5211e1c896f  Si_sv_GW_nr  Si         pbe
       217  537a85fa-34b8-4267-bbc0-aed06346a03f  Si_sv_GW     Si         pbe


.. _installation-getpluginready-calcexample:

Calculation Example
===================

As an example the following code snippet describes the relaxation for a simple silicon diamond structure using both Custodian and the VASP code.
(Note that this is only for demonstration purposes and simply adding a custodian code will **not** enable any error correction for that calculation!
Please refer to the calculator section on how to run a calculation with error corrections)
For the sake of simplicity, here, all calculation input parameters are taken as defined by pymatgen's :class:`~pymatgen.io.vasp.sets.MPRelaxSet`.

.. code:: python

   #!/usr/bin/env python

   from aiida.plugins import CalculationFactory, DataFactory
   from aiida.engine import submit
   from aiida.orm import Code

   from pymatgen.io.vasp.sets import MPRelaxSet

   # load the plugin's datatypes
   VaspIncarData = DataFactory('cusp.incar')
   VaspKpointData = DataFactory('cusp.kpoints')
   VaspPoscarData = DataFactory('cusp.poscar')
   VaspPotcarData = DataFactory('cusp.potcar')

   def si_diamond_structure():
       """
       Setup a cubic unitcell containing the Si diamond structure
       """
       from pymatgen import Lattice, Structure
       lattice = Lattice.cubic(5.4309)
       species = ['Si']
       coords = [[.0, .0, .0]]
       # setup the structure
       structure = Structure.from_spacegroup('Fd-3m', lattice, species, coords)
       return structure

   # define the vasp and custodian codes to be used for the calculation
   code_vasp = 'vasp_5.4.1_openmpi_4.0.3_scalapack_2.1.0@CompMPI'
   code_custodian = 'custodian_2020427@CompMPI'

   # get the builder for the VASP calculation object and setup the codes
   # and job resources
   VaspSiRelax = CalculationFactory('cusp.vasp').get_builder()
   VaspSiRelax.code = Code.get_from_string(code_vasp)
   VaspSiRelax.custodian.code = Code.get_from_string(code_custodian)
   VaspSiRelax.metadata.options.resources = {
       'tot_num_mpiprocs': 4,
       'num_machines': 1
   }
   # simplest case: simply use the calculation inputs as defined by
   # pymatgen's MPRelaxSet
   mprelaxset = MPRelaxSet(si_diamond_structure())
   # set the calculation parameters
   VaspSiRelax.incar = VaspIncarData(incar=mprelaxset.incar)
   VaspSiRelax.kpoints = VaspKpointData(kpoints=mprelaxset.kpoints)
   VaspSiRelax.poscar = VaspPoscarData(structure=mprelaxset.poscar)
   VaspSiRelax.potcar = VaspPotcarData.from_structure(
                               mprelaxset.poscar, mprelaxset.potcar_functional,
                               potcar_params=mprelaxset.potcar_symbols)
   # submit the code to the daemon
   calc_node = submit(VaspSiRelax)

Saving the above contents to a new python file, i.e. ``test_calc.py``, we are now ready to actually run the calculation.
One the command line simply execute the following command to start the calculation:

.. code:: console

   $ verdi run test_calc.py

After the calculation has been successfully deployed to the daemon it should now appear in the list of active processes.
You may check this using AiiDA's ``verdi process list`` which will output all active processes:

.. code:: console

   $ verdi process list
     PK  Created    Process label         Process State    Process status
   ----  ---------  --------------------  ---------------  ---------------------------------------
   1332  5s ago     VaspCalculation       ⏵ Waiting        Monitoring scheduler: job state RUNNING

.. note::

   You should be able to run this example by simply copy and pasting the code to a local file on your computer.
   Of course, the code names used in the snippet have to be adapted accordingly before submission.


.. _AiiDA documentation: https://aiida.readthedocs.io/projects/aiida-core/en/latest/
