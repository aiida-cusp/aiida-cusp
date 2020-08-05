.. _installation-installingtheplugin:

*********************
Installing the Plugin
*********************

It is strongly recommended to install the plugin using the :ref:`conda<installation-installingtheplugin-conda>` package manager which will also install the required RabbitMQ_ and PostgreSQL_ services.
However, you may also install the plugin using either :ref:`pip<installation-installingtheplugin-pip>` or directly from the plugin's :ref:`source code<installation-installingtheplugin-source>`.

.. warning::
   Be advised that the installation via ``pip`` or directly from source will **not** install the required RabbitMQ_ or PostgreSQL_ services automatically!
   While this allows you to use RabbitMQ_ or PostgreSQL_ installations already available on your system, it requires more manual work to get AiiDA setup and running.
   Thus, these installation routes are considered suitable only for advanced AiiDA users.

After the plugin has been installed you can check if the installation was successful by running the command

.. code:: console

   $ reentry scan
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

.. _installation-installingtheplugin-conda:

Installing via Conda (recommended)
==================================


To install the plugin via the ``conda`` installer Anaconda_ needs to be installed on your machine first.
Consult the `conda installation guide <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`_ for more information on how to install Anaconda_ on your system.

.. note::

   Instead of installing the full Anaconda distribution you may also install the more lightweight Miniconda distribution which will take up less disk space.

Once Anaconda (or Miniconda) is installed on your system you may install the plugin using ``conda`` by running the command

.. code-block:: console

   $ conda create --name aiida-cusp -c conda-forge aiida-cusp aiida-core.services

The command shown above will create a new python environment named `aiida-cusp` and installs the plugin and all required dependencies to that environment.
After the installation has finished we can activate the newly created environment and run the ``reentry scan`` command to discover the added entry points:

.. code-block:: console

   $ conda activate aiida-cusp
   (aiida-cusp) $ reentry scan

If the installation was successful the new calculation entry point ``cusp.vasp`` should now be available from the ``verdi`` command line:

.. code-block:: console

   (aiida-cusp) $ verdi plugin list aiida.calculations
   Registered entry points for aiida.calculations:
   * arithmetic.add
   * cusp.vasp
   * templatereplacer

If the new entry point ``cusp.vasp`` is disovered correctly please proceed with the :ref:`next step<installation-getpluginready>` to finalize the plugin's installation.

.. _installation-installingtheplugin-pip:

Installing via PIP (advanced)
=============================


To install the plugin via the ``pip`` installer run the command

.. code:: console

   $ pip install aiida-cusp

which will install the plugin and the required dependencies using the resources available from the python package index (PyPi_).


.. _installation-installingtheplugin-source:

Installing from Source (advanced)
=================================

Alternatively to the previous installation methods, install the plugin directly from source by cloning the plugin's repository.
After cloning go to the source root directory containing the project's `setup.py` and run

.. code:: console

   $ python setup.py install


.. _PyPi: https://pypi.org/
.. _Anaconda: https://anaconda.org/
.. _anaconda package repository: https://anaconda.org/anaconda/repo
.. _RabbitMQ: https://www.rabbitmq.com
.. _PostgreSQL: https://www.postgresql.org
