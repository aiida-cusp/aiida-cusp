.. _user-guide-parsers-vaspfileparser:

Vasp File Parser (``cusp.default``)
===================================

The :class:`~aiida_cusp.parsers.vasp_file_parser.VaspFileParser` class is the default class used by each calculation if no alternative parser is set through the ``metadata.options.parser_name`` option.
This parser does not apply any parser magic but simply checks the output files and adds them as gzip-compressed archives to the repository.
Since no parsing of individual values is applied this parser class is suitable for all VASP calculations (i.e. normal calculations, AIMD as well as NEB).
Of course, the set of files added for each calculation can be changes based on the available parser settings discussed in the following.,

Parser Settings
---------------

Parser settings are expected to be passed as dictionary to the calculations ``metadata.options.parser_settings`` option.
The dictionary thereby accepts the settings show in the following.

.. warning::

   Note that if the dictionary passed through the ``metadata.options.parser_settings`` contains any setting unknown to the parser the parsing will fail!

**Settings:**

* **parse_files** (:class:`list`, optional) --
  List of filenames (i.e. `'OUTCAR'`, `'vasprun.xml'`, etc.) or wildcards (i.e. `'\*CAR'`, `'\*'`, etc.).
  Every file in the list of retrieved files matching a defined filename or a given wildcard is added to the calculation.

  .. note::

     Mixing filenames and wildcards is allowed, i.e. `['\*CAR', 'vasprun.xml', ...]` is perfectly fine.

  By default (i.e. if unset) only the files `'CONTCAR'`, `'OUTCAR'` and `'vasprun.xml'` are added to the outputs.
  (default: `['CONTCAR', 'OUTCAR', 'vasprun.xml'`)

* **fail_on_missing_files** (:class:`bool`, optional) --
  Set this flag to :class:`True` if the parsing should fail if a file defined in the ``parse_files`` list cannot be found in the retrieved outputs.
  (default: :class:`False`)

Parser Outputs
--------------

All files defined by the ``parse_files`` options are added by the parser to the calculation as outputs available under the `outputs.parsed_results` key.

.. note::

   Note that only the files *vasprun.xml*, *OUTCAR*, *WAVECAR*, *CHGCAR*  and *CONTCAR*  are added using their corresponding :ref:`output datatype<user-guide-datatypes-outputs>`.
   All other files will be added using the :class:`~aiida_cusp.data.outputs.vasp_generic.VaspGenericData` class (see also :ref:`generic datatype<user-guide-datatypes-outputs-generic>`).

Parsed files are registered in the output namespace using the corresponding lower case filename neglecting any suffixes.
Thus, after parsing a stored *CONTCAR* file can be accessed from the stored calculation node via

.. code-block:: python

   calulation_node.outputs.parsed_results.contcar

while a parsed *vasprun.xml* file would be accessible (with the corresponding *.xml* suffix being replaced by *_xml*) via

.. code-block:: python

   calculation_node.outputs.parsed_results.vasprun_xml

In case of NEB calculation featuring files stored at different NEB sub-folders all files found inside the top-folder are added corresponding to the scheme above.
However, files located in NEB sub-folders will be added to an individual namespace corresponding to the sub-folder it was found in prefixed with ``node_``.
As an example consider parsing the *CONTCAR* outputs of a NEB calculation located in the NEB calculation's three sub-folders `'00'`, `'01'` and `'02'`.
Then each of the individual output files is accessible via the output links

.. code-block:: python

   calculation_node.outputs.parsed_results.node_00.contcar  # output 00/CONTCAR
   calculation_node.outputs.parsed_results.node_01.contcar  # output 01/CONTCAR
   calculation_node.outputs.parsed_results.node_02.contcar  # output 02/CONTCAR

.. note::

   This scheme applies to all calculation output files found in NEB sub-folders which will also be added to the corresponding sub-namespace.
