.. aiida-cusp documentation master file, created by
   sphinx-quickstart on Tue Jun 16 19:41:18 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


#####################################################
aiida-cusp -- a Custodian based VASP Plugin for AiiDA
#####################################################

The aiida-cusp plugin is an AiiDA plugin for VASP optionally utilizing
Custodian to run the VASP calculations with automated error correction.
Contrary to error correction methods that may be implemented directly in AiiDA
workflows that allow for error corrections on the workflows' step level, the
Custodian interface of this plugin introduces error corrections for VASP on
the calculation's runtime level. In addition to the error correction of
VASP calculations this plugin was also designed with fast and  easy pre- and
post-processing in mind. Thus, all datatypes serving as inputs and outputs
to the calculators, implemented by this plugin, are tightly connected to the
Pymatgen framework mainting direct access to the rich set of implemented
analysis tools.

.. toctree::
   :maxdepth: 1
   :titlesonly:
   :caption: Installation
   :name: installation

   installation/installation.rst
   installation/get_plugin_ready.rst
   installation/next_steps.rst

.. toctree::
   :maxdepth: 1
   :caption: Tutorials
   :name: tutorials

   tutorials/calculations.rst
   tutorials/workflows.rst

.. toctree::
   :maxdepth: 1
   :caption: User Guide
   :name: user-guide

   user_guide/calculators.rst
   user_guide/custodian.rst
   user_guide/parsers.rst
   user_guide/datatypes.rst
   user_guide/commands.rst


.. toctree::
   :maxdepth: 1
   :caption: Development
   :name: development

   development/development.rst





******************
Indices and tables
******************

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _AiiDA: https://aiida.readthedocs.io/projects/aiida-core/en/latest/
