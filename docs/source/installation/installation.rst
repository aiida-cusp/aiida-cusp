.. _installation-installingtheplugin:

*********************
Installing the Plugin
*********************


Installing the plugin is possible using different channels.
To this end the plugin is published on the pypi channel and the conda-forge repository and may be installed through pip and conda.
The exact procedure how to install using the different package managers is discussed in the following sections.
After the plugin was installed you can check if the installation was successful by running the command

.. code:: console

   $ verdi plugin list aiida.calculations
   Registered entry points for aiida.calculations:
   * arithmetic.add
   * cusp.vasp
   * templatereplacer

The output of this command should now contain the new calculation entry point ``cusp.vasp``.

.. note::

   Independent of the method you chose to install the plugin never forget
   to run ``reentry`` after successful installation in order to discover
   the newly added entry points using the command:

   .. code:: console

      $ reentry scan

   If this post-installation step is skipped new entry points installed by the
   plugin will not be discoverable and the plugin will not work as expected.

.. _installation-installingtheplugin-pip:

Installing via PIP
==================


To install the plugin via the ``pip`` installer simply run the command

.. code:: console

   $ pip install aiida-cusp

which will install the plugin and all the required dependencies using
the pypi repository.

.. _installation-installingtheplugin-conda:

Installing via Conda
====================


To install the plugin via the ``conda`` installer anaconda needs to be
installed on your machine. To install the plugin simply run the command

.. code:: console

   $ conda install -c conda-forge aiida-cusp

which will install the plugin and all the required dependencies.

.. _installation-installingtheplugin-fromsource:

Installing from Source
======================


Installation from source, discssed in this section, will install the latest
development version of the plugin. Thus, installations from source are
reccomended for anyone planning to contribute to the plugin or to simply check
if experienced bugs are fixed in the latest version.

To install the plugin simply clone the latest version directly from the
github repository using the command

.. code:: console

   $ git clone abc

which will fetch a copy of the repository and store it into the folder named
onto your disc. After the cloning has finished changed to the created
directory containing the ``setup.py`` of the project and run

.. code:: console

  $ pip install -e .

to install an ediatble installation of the locally checked out code base. For
development purposes you may also install the provided extras ``devlop`` and
``docs`` wich will allow you to run the provided unittests or build the
plugin's documentation, respectively:

.. code:: console

   $ pip install -e .[develop,docs]
