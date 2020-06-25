.. _user-guide-custodian-settings:

Custodian Settings
==================

Settings changing the default behavior of the custodian executable can be passed for every VASP calculation via the ``inputs.custodian.settings`` input.
Inputs passed to the calculation by this option are expected to be of type :class:`dict` containing the parameters and the corresponding values to be set as key-value pairs.
For instance, if you are using a builder to setup the calculation the settings may be given as

.. code-block:: python

   builder.inputs.custodian.settings = {
     'max_errors': 10,
     'monitor_freq': 5,
     ...
   }

In the following all available options that may be defined and the corresponding default options that are used in case they are undefined are shown in the following.

**Available Options:**

* **max_errors** (:class:`int`) --
  This sets the maximum number of errors that may occur for a single
  calculation before terminating the calculation (default: `10`)
* **polling_time_step** (:class:`int`) --
  Seconds between two consecutive checks for the calculation being completed
  (default: `10`)
* **monitor_freq** (:class:`int`) --
  Number of performed polling steps before the calculation is checked for
  possibly encountered errors (default: `30`)
* **skip_over_errors** (:class:`bool`) --
  Set this option to :class:`True` to skip over any failed error handler
  (default: :class:`False`)
