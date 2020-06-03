# -*- coding: utf-8 -*-


"""
AiiDA command line extension for handling VASP pseudo-potential files
"""


import pathlib

import click
from aiida.cmdline.commands.cmd_data import verdi_data


@verdi_data.group('potcar')
def potcar():
    """
    Manage VASP POTCAR files.
    """
    pass


@potcar.group('add')
def add_potcar():
    """
    Add one or multiple VASP pseudo-potential files to the database.
    """
    pass


@add_potcar.command('family')
@click.argument('path', nargs=1, type=click.Path(exists=True))
def add_potcar_family(path):
    """
    Adds a VASP pseudo-potential family to an existing AiiDA database.

    Recursively searches the given folder [PATH] for files named POTCAR and
    adds all discovered potentials to the database. Note that this only works
    if the folder structure corresponds to that of the shipped VASP
    pseudo-potential libraries, i.e. every file path complies with the scheme

    \b
      /path/{FUNCTIONAL_FOLDER}/{POTENTIAL_NAME}/POTCAR

    where {FUNCTIONAL_FOLDER} contains one of the potential library archive
    names identifying the corresponding functional:

    \b
      - potuspp_lda
      - potpaw_lda
      - potpaw_lda.52
      - potpaw_lda.54
      - potpaw_pbe
      - potpaw_pbe.52
      - potpaw_pbe.54
      - potuspp_gga
      - potpaw_gga

    and the parent folder name {POTENTIAL_NAME} is identified with the
    potential's unique name that is used to store the potential to the
    database:

    \b
      - Li
      - Li_sv
      - Si_pv_GW
      - etc.
    """
    # no need to check for valid functional and element since this will be
    # checked by the VaspPotcarFile class anyways
    # only check it's indeed a folder
    pass


@add_potcar.command('single')
@click.argument('path', nargs=1, type=click.Path(exists=True))
@click.option('--name', '-n', nargs=1, type=str,
              help=("Name of the pseudo-potential used to identify the "
                    "potential in the database (i.e., Li, Li_sv, ...)."))
@click.option('--functional', '-f', nargs=1, type=str,
              help=("Functional of the pseudo-potential (i.e. one of "
                    "lda_us, lda, lda_52, lda_54, pbe, pbe_52, pbe_54, "
                    "pw91_us or pw91)."))
def add_potcar_single(path, name, functional):
    """
    Adds a single VASP pseudo-potential to an existing AiiDA database.

    Requires the explicit definition of the pseudo-potential's functional,
    i.e. one of

    \b
      - lda_us   (Ultrasoft LDA potential)
      - lda
      - lda_52
      - lda_54
      - pbe
      - pbe_52
      - pbe_54
      - pw91_us  (Ultrasoft GGA potential)
      - pw91

    and the pseudo-potential's unique name that is used to store and
    disover it in the AiiDA database:

    \b
      - Li
      - Li_sv
      - Si_pv_GW
      - etc.
    """
    # no need to check for valid functional and element since this will be
    # checked by the VaspPotcarFile class anyways
    # only check if it is file and if it's named POTCAR
    pass


@potcar.command('list')
@click.option('--name', '-n', nargs=1, type=str,
              help=("Name used to identify the stored pseudo-potential (i.e. "
                    "Li, Li_sv, ...)"))
@click.option('--element', '-e', nargs=1, type=str,
              help=("Element associated with the stored pseudo-potential "))
@click.option('--functional', '-f', nargs=1, type=str,
              help=("Functional of the stored pseudo-potential (i.e. one of "
                    "lda_us, lda, lda_52, lda_54, pbe, pbe_52, pbe_54, "
                    "pw91_us or pw91)"))
def list_potcar(name, element, functional):
    """
    List VASP pseudo-potentials available in the AiiDA database.

    Generate and display a list of all pseudo-potentials available in the
    database with certain properties (i.e. name, functional or the "
    associated element)
    """
    pass


@potcar.command('show')
@click.option('--name', '-n', nargs=1, type=str)
@click.option('--functional', '-f', nargs=1, type=str)
# only required if multiple potentials are found
@click.option('--version', '-v', nargs=1, type=int)
def show_potcar(name, functional, version):
    """
    Display a pseudo-potential's header contents.
    """
    pass
