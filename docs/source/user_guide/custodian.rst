.. _user-guide-custodian:

*********
Custodian
*********

One characteristic of this plugin is the ability to wrap VASP calculations in `Custodian`_ to enable error correction on the runtime level.
To this end, calculators implemented by this plugin, in addition to the VASP code, accept a second, optional custodian code object under the ``inputs.custodian.code`` input.
Similary to the actual VASP code input, defined by ``inputs.code``, settings may be passed through the ``inputs.custodian.settings`` option to customize Custodian's behavior.
Possible settings that are available for the Custodian executable are discussed in the :ref:`Custodian settings<user-guide-custodian-settings>` section.
Error handlers defining which errors are monitored and corrected are defined via the ``inputs.custodian.handlers`` input, discussed in the :ref:`handler section<user-guide-custodian-handlers>`.

.. warning::

   Note that all custodian inputs, i.e. ``custodian.code``, ``custodian.settings`` and ``custodian.handlers`` are optional and do not need to be specified.
   However, be advised that setting a custodian code via the ``custodian.code`` input without specifying any handler does not enable any error correction!
   In that case custodian will simply run the VASP calculation with its default settings not looking and correcting any emerging errors.

.. toctree::
   :maxdepth: 1

   custodian/settings.rst
   custodian/handlers.rst

.. _Custodian: https://materialsproject.github.io/custodian/
