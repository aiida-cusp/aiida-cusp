.. _user-guide-custodian:

*********
Custodian
*********

One of the most distinct characteristics of this plugin is its ability to wrap VASP calculations in `Custodian`_ to enable error correction on the runtime level.
To this end, calculators implemented by this plugin, in addition to the VASP code, accept a second, optional custodian code object under the ``inputs.custodian.code`` input.
Similary to the actual VASP code input, defined by the ``inputs.code`` option, additional settings for the Custodian code may be passed through the ``inputs.custodian.settings`` option to customize Custodian's behavior.
Possible settings that can be set for calculations employing the Custodian executable are documented in the :ref:`Custodian settings<user-guide-custodian-settings>` section.
Error handlers defining which errors are monitored and corrected can be defined for each calculation via the ``inputs.custodian.handlers`` input.
The available set of error handlers that can be used with this plugin is documented in the :ref:`handler section<user-guide-custodian-handlers>`.

.. warning::

   Note that all custodian inputs, i.e. ``custodian.code``, ``custodian.settings`` and ``custodian.handlers`` are entirely optional and do not need to be specified.
   However, be advised that setting a custodian code via the ``custodian.code`` input without specifying any handler does not enable any error correction for the calculation!
   In that case custodian will simply run the VASP calculation with its default settings, ignoring any emerging errors.

.. toctree::
   :maxdepth: 1

   custodian/settings.rst
   custodian/handlers.rst

.. _Custodian: https://materialsproject.github.io/custodian/
