.. _installation-installingtheplugin:

*********************
Installing the Plugin
*********************

The plugin may be installed using a package manager, i.e. using :ref:`pip<installation-installingtheplugin-pip>` or :ref:`conda<installation-installingtheplugin-conda>`, or directly from the plugin's :ref:`source code<installation-installingtheplugin-source>`.
After the plugin has been installed you can check if the installation was successful by running the command

.. code:: console

   $ verdi plugin list aiida.calculations
   Registered entry points for aiida.calculations:
   * arithmetic.add
   * cusp.vasp
   * templatereplacer

The output of this command should now contain the new calculation entry point ``cusp.vasp``.

.. note::

   Independent of the method you chose to install the plugin never forget to run ``reentry`` after successful installation in order to discover the newly added entry points using the command:

   .. code:: console

      $ reentry scan

   If this post-installation step is skipped new entry points installed by the plugin will not be discoverable and the plugin will not work as expected.

.. _installation-installingtheplugin-pip:

Installing via PIP
==================


To install the plugin via the ``pip`` installer run the command

.. code:: console

   $ pip install aiida-cusp

which will install the plugin and all the required dependencies using the resources available from the python package index (PyPi_).

.. _installation-installingtheplugin-conda:

Installing via Conda
====================


To install the plugin via the ``conda`` installer Anaconda_ needs to be installed on your machine.
To install the plugin run the command

.. code:: console

   $ conda install -c conda-forge aiida-cusp

which will install the plugin and all the required dependencies using the resources available from the `anaconda package repository <https://anaconda.org/anaconda/repo>`_.

.. _installation-installingtheplugin-source:

Installing from Source
======================

Alternatively to the previous installation methods, install the plugin directly from source by cloning the plugin's repository.
After cloning go to the source root directory containing the project's `setup.py` and run

.. code:: console

   $ python setup.py install


.. _PyPi: https://pypi.org/
.. _Anaconda: https://anaconda.org/
.. _anaconda package repository: https://anaconda.org/anaconda/repo
