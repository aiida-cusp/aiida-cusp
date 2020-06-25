.. _user-guide-calculators-vaspcalculator:

Vasp Calculator (``cusp.vasp``)
===============================

The :class:`~aiida_cusp.calculators.VaspCalculator` is available using the ``cusp.vasp`` entry point allows you to perform all kind of VASP calculation ranging from simple calculations to AIMD and even NEB calculations.
Similar to VASP itself the behavior of the calculation is entirely controllable by the passed input parameters defined for `KPOINTS`, `INCAR` and the `POTCAR` pseudo-potential.
(Please refer to the :ref:`potcar command documentation<user-guide-commands-potcar>` how to add pseudo-potentials for VASP to the database)
Whether a simple calculation or complex NEB calculation is run is decided by the calculation object based on the given structural inputs (i.e. ``poscar`` or ``neb_path``).
Note that by default the output files containing calculation results are parsed using the :ref:`VaspFileParser class<user-guide-parsers-vaspfileparser>`.
Of course the default parser may be changed to a different parser class using the calculation's `metadata.options.parser_class` option with corresponding parser options passed to the parser through the `metadata.options.parser_settings` option.
For an overview of the available parsers and the accepted settings please refer to the :ref:`Parser section<user-guide-parsers>`.
Despite the already mentioned, optional parser options the calculator accepts several other (non-)optional inputs that are used to setup the actual VASP calculation.
In the following these calculation inputs are discussed and, for clarity, have been clustered into three main input groups that can be set with the calculation class:

* :ref:`Vasp Calculation Inputs:<user-guide-calculators-vaspcalculator-inputs-vasp>`
  All inputs found in this group are the direct VASP inputs that are used to setup the VASP calculation, i.e. `KPOINTS`, `INCAR`, etc.
* :ref:`Custodian Inputs:<user-guide-calculators-vaspcalculator-inputs-custodian>`
  Set of input parameters for the Custodian executable needed to run an error corrected VASP calculation through the Custodian framework.
  If a Custodian code and corresponding error handlers are defined error correction is enabled by wrapping the previously defined VASP calculation in Custodian.
  However, note that all inputs listed in this group are completely optional!
* :ref:`Restart Options:<user-guide-calculators-vaspcalculator-inputs-restart>`
  Available options when a calculation is restarted from a prevoius run using the remote folder of the parent calculation.

.. _user-guide-calculators-vaspcalculator-inputs:

Calculator Inputs
-----------------

.. _user-guide-calculators-vaspcalculator-inputs-vasp:

VASP Calculation Inputs:
""""""""""""""""""""""""

  .. note::

     Note that for the :class:`~aiida_cusp.calculators.VaspCalculation` class the input options `inputs.poscar` and `inputs.neb_path` may not be set simultaneously.
     If both are set at the same time an error will be raised and the calculation will fail!

* **code** (:class:`aiida.orm.Code`) --
  VASP code used to run the calculation.
* **incar** (:class:`aiida_cusp.data.VaspIncarData`) -- i
  INCAR data input defining the calculation parameters for the VASP calculation (see :ref:`INCAR<user-guide-datatypes-inputs-incar>`)
* **kpoints** (:class:`aiida_cusp.data.VaspKpointData`) --
  KPOINTS data input defining the k-point grid to be used for the calculation (see :ref:`KPOINTS<user-guide-datatypes-inputs-kpoints>`)
* **poscar** (:class:`aiida_cusp.data.VaspPoscarData`) --
  Structure data input required for regular VASP or AIMD simulations (see :ref:`POSCAR<user-guide-datatypes-inputs-poscar>`)
* **neb_path** (:class:`dict`) --
  Structure data input required for VASP NEB calculations.

  .. note::

     For NEB calculations a dictionary of multiple structures defining the NEB path is expected as input to the `neb_path` option.
     Here, every structure has to passed under the corresponding key `'node_XX'` where `'XX'` represents the name of the NEB subfolder the image data is written to.
     As an example consider the following input:

     .. code-block:: python

        inputs.neb_path = {'node_00': poscar_1, 'node_01': poscar_2, 'node_02': poscar_3}

     Then, upon submission of the calculation the contents of `poscar_1` are written to the calculation's `'00'` subfolder, the contents of `poscar_2` to the `'01'` subfolder and so on.

* **potcar** (:class:`dict`) --
  The VASP pseudo-potentials to be used for the calculation.
  Potentials are expected to be defined as dictionary containing the structure's elements as keys and the :class:`aiida_cusp.data.VaspPotcarData` of the potential to be used for that eleme

  .. note::

     There is no need to build this dictionary manually and it is highly recommended to setup the `options.potcar` inputs using the :meth:`aiida_cusp.data.VaspPotcarData.from_structure` method.
     Please refer to the :ref:`VaspPotcarData documentation<user-guide-datatypes-inputs-potcar>` for more details in how this method is used to generate the appropriate inputs.

.. _user-guide-calculators-vaspcalculator-inputs-custodian:

Custodian Settings:
"""""""""""""""""""

Options passed to the Custodian executable if a custodian code is set for the `custodian.code` option.
(Also refer to the :ref:`Custodian section<user-guide-custodian>` for more details on the available settings)

.. note::

   If no settings are defined for Custodian the VASP code is not wrapped by Custodian (i.e. the `vasp` executable defined by the VASP code set for the `code` input is called directly)

* **custodian.code** (:class:`aiida.orm.Code`) --
* **custodian.handlers** (:class:`list` or :class:`dict`) --
  Optional input option defining the error handlers connected to the calculation.
  For a complete list of available error handlers that may be set here please refer to the :ref:`handler section<user-guide-custodian-handlers>` in the Custodian documentation of this plugin.
  (optional, default: ``{}``)

  .. warning::

     Be advised that setting no error handlers for Custodian is perfectly fine, however, defining a Custodian code without setting any handlers will disable the error correction.

* **custodian.settings** (:class:`dict`) --
  Optional dictionary containing the settings that should be set to customize the behavior of the Custodian executable.
  If no settings are passed (default) then the plugin's default settings for Custodian will be used.
  For a complete list of available settings that may be set here and their corresponding default values, please refer to the :ref:`settings section<user-guide-custodian-settings>` in the Custodian documentation of this plugin.
  (default: ``{}``)

.. _user-guide-calculators-vaspcalculator-inputs-restart:

Restart Options:
""""""""""""""""

* **restart.folder** (:class:`aiida.orm.RemoteData`) --
  Remote folder of the parent calculation from which the calculation is restarted.
  All files in the remote folder will be copied to the restarted calculation's folder and are used as input to the new calculation.

  .. note::

     For restarted calculations the previous used `INCAR` and `KPOINTS` data can be ignored by setting new parameters through the `inputs.incar` and `inputs.kpoints` options.
     Note, however, that setting an alternative structure or using different pseudo-potentials is not allowed for a restarted calculation which will raise an error.

* **restart.contcar_to_poscar** (:class:`bool`) --
  If this option is set to `True` the `POSCAR` file of the restarted calculations will be replaced with the parent calculation's `CONTAR` contents.
  (optional, default: `True`)

.. _user-guide-calculators-vaspcalculator-outputs:

Default Calculator Outputs
---------------------------

After the calculation has finished, parsed outputs are available via the calculation nodes `outputs.parsed_results` key.
Note that the contents that are stored to this output key of course depend the parser plugin used for the calculation (see the :ref:`Parsers section<user-guide-parsers>`).
By default the :class:`~aiida_cusp.calculators.VaspCalculator` class uses the :ref:`VaspFileParser<user-guide-parsers-vaspfileparser>` to parse the generated results.
Note that if no additional parser options are passed to this parser class only the `CONTCAR`, `vasprun.xml` and `OUTCAR` files will be avilable in the calculation's outputs.

.. note::

   Files not generated as a result of the calculation, i.e. the logged scheduler and stdout / stderr outputs as well as the used submit script and custodian inputs are not stored under the `outputs.parsed_results` key.
   You can find these files in the calculation's retrieved folder located under the `output.retrieved` key.
