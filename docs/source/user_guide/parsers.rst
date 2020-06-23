.. _user-guide-parsers:

**************
Parser Classes
**************

In the following the parser classes implemented by this plugin are documented.
Implemented parser plugins are used to parse calculation outputs of VASP calculations performed with the plugins' calculation plugins.
Parser can be set for each calculation thtough the ``metadata.options.parser_name`` option.
Similarly, additional settings for each parser can be passed trough the ``metadata.options.parser_settings`` option.
Of course, the available ``parser_settings`` and generated outputs depend on the parser class used for each calculation.
For the generated outputs and available settings please refer to the documentation for the individual parser classes given below.

.. toctree::
   :maxdepth: 1
   :caption: Available Parser Classes:

   parsers/vasp_file_parser.rst
