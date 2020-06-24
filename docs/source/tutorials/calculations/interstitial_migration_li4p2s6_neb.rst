NEB Calculation for Interstitial Migration of Li in Li\ :sub:`4`\ P\ :sub:`2`\ S\ :sub:`6`
==========================================================================================

Installed codes

.. code-block:: console

   $ verdi code list
   # List of configured codes:
   # (use 'verdi code show CODEID' to see the details)
   * pk 1228 - custodian_2020427@CompMPI
   * pk 1271 - vasp_5.4.1_openmpi_4.0.3_scalapack_2.1.0@CompMPI
   * pk 1366 - vasp_5.4.1_openmpi_4.0.3_scalapack_2.1.0_vtst@CompMPI

In the following the vasp VTST executable (`PK 1366`) will be used to run the VASP calculation while ,in addition, the
custodian executable (`PK 1228`) is used to run the error corrections for the VASP calculation.

.. note::

   When following this tutorial do not forget to adjust the code and computer names used here to the actual names used on your system

