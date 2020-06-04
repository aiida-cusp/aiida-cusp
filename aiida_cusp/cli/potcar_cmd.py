# -*- coding: utf-8 -*-


"""
AiiDA command line extension for handling VASP pseudo-potential files
"""


import click
from aiida.cmdline.commands.cmd_data import verdi_data


# FIXME: Add tests for implemented CLI commands


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
    import pathlib
    import warnings

    from tabulate import tabulate

    from aiida_cusp.data.inputs.vasp_potcar import VaspPotcarFile
    from aiida_cusp.utils.defaults import VaspDefaults
    from aiida_cusp.utils.potcar import PotcarPathParser
    from aiida_cusp.utils.exceptions import (VaspPotcarFileError,
                                             MultiplePotcarError,
                                             CommandLineError)

    # verify is folder
    path = pathlib.Path(path)
    if not path.is_dir():
        raise CommandLineError("Given path does not point to a folder")
    # recurse through the folder to find all POTCAR files
    potcar_file_paths = list(path.rglob(VaspDefaults.FNAMES['potcar']))
    potentials_to_store = []
    potentials_present = []
    potentials_skipped = []
    tab_entries = []
    for potcar_file_path in potcar_file_paths:
        # parse functional and name from path (will raise if functional
        # cannot be parsed from the path)
        parsed_path = PotcarPathParser(potcar_file_path)
        functional = parsed_path.functional
        name = parsed_path.name
        try:
            potential_file_node = VaspPotcarFile.add_potential(
                potcar_file_path, name=name, functional=functional)
            potentials_to_store.append(potential_file_node)
            tab_entries.append([
                potential_file_node.name,
                potential_file_node.element,
                potential_file_node.functional,
                potential_file_node.version,
                str(potcar_file_path.absolute()),
            ])
        except VaspPotcarFileError:
            warnings.warn("Skipping '{}' due to a parsing error"
                          .format(potcar_file_path.absolute()))
            potentials_skipped.append(potcar_file_path)
            continue
        except MultiplePotcarError:
            potentials_present.append(potcar_file_path)
    # create a tabulated overview over the new potentials
    tab_headers = ['name', 'element', 'functional', 'version', 'path']
    table = tabulate(tab_entries, headers=tab_headers, tablefmt='simple')
    click.echo("")
    click.echo("New pseudo-potential(s) to be stored:")
    click.echo("")
    click.echo(table)
    # print summary to the screen
    num_new = len(potentials_to_store)
    num_present = len(potentials_present)
    num_skipped = len(potentials_skipped)
    click.echo("")
    click.echo("File location: {}".format(path.absolute()))
    click.echo("")
    click.echo("Discovered a total of {} POTCAR file(s) of which"
               .format(num_new + num_present + num_skipped))
    click.echo("\t{}\twill be stored to the database,".format(num_new))
    click.echo("\t{}\tare already available in the database and"
               .format(num_present))
    click.echo("\t{}\twill be skipped due to errors".format(num_skipped))
    click.echo("")
    # exit if no potentials will be stored anyway
    if num_new == 0:
        return
    # ask for confirmation before the actual storing is performed
    if click.confirm("Before continuing, please check the displayed list "
                     "for possible errors! Continue and store?"):
        for potcar_file_node in potentials_to_store:
            stored_node = potcar_file_node.store()
            click.echo("Created new VaspPotcarFile node with UUID {} at ID {}"
                       .format(stored_node.uuid, stored_node.id))
    else:
        click.echo("Aborting. No potential was stored to the database!")


@add_potcar.command('single')
@click.argument('path', nargs=1, type=click.Path(exists=True))
@click.option('--name', '-n', nargs=1, type=str, required=True,
              help=("Name of the pseudo-potential used to identify the "
                    "potential in the database (i.e., Li, Li_sv, ...)."))
@click.option('--functional', '-f', nargs=1, type=str, required=True,
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
    import pathlib
    import warnings

    from tabulate import tabulate

    from aiida_cusp.data.inputs.vasp_potcar import VaspPotcarFile
    from aiida_cusp.utils.defaults import VaspDefaults
    from aiida_cusp.utils.exceptions import (VaspPotcarFileError,
                                             MultiplePotcarError,
                                             CommandLineError)

    # verify is potcar file
    path = pathlib.Path(path)
    if not path.is_file():
        raise CommandLineError("Given path does not point to a file.")
    if not path.name == VaspDefaults.FNAMES['potcar']:
        raise CommandLineError("The specified file does not seem to be a "
                               "VASP pseudo-potential file (Expected filename "
                               "'POTCAR'")
    # do the actual parsing
    functional = functional.lower()
    potentials_to_store = []
    potentials_present = []
    potentials_skipped = []
    tab_entries = []
    try:
        potential_file_node = VaspPotcarFile.add_potential(
            path, name=name, functional=functional, return_duplicate=True)
        potentials_to_store.append(potential_file_node)
        tab_entries.append([
            potential_file_node.name,
            potential_file_node.element,
            potential_file_node.functional,
            potential_file_node.version,
            str(path.absolute()),
        ])
    except VaspPotcarFileError:
        warnings.warn("Skipping '{}' due to a parsing error"
                      .format(path.absolute()))
        potentials_skipped.append(path)
    except MultiplePotcarError:
        potentials_present.append(path.absolute())

    # create a tabulated overview over the new potentials
    tab_headers = ['name', 'element', 'functional', 'version', 'path']
    table = tabulate(tab_entries, headers=tab_headers, tablefmt='simple')
    click.echo("")
    click.echo("New pseudo-potential(s) to be stored:")
    click.echo("")
    click.echo(table)
    # print summary to the screen
    num_new = len(potentials_to_store)
    num_present = len(potentials_present)
    num_skipped = len(potentials_skipped)
    click.echo("")
    click.echo("File location: {}".format(path.absolute()))
    click.echo("")
    click.echo("Discovered a total of {} POTCAR file(s) of which"
               .format(num_new + num_present + num_skipped))
    click.echo("\t{}\twill be stored to the database,".format(num_new))
    click.echo("\t{}\tare already available in the database and"
               .format(num_present))
    click.echo("\t{}\twill be skipped due to errors".format(num_skipped))
    click.echo("")
    # exit if no potentials will be stored anyway
    if num_new == 0:
        return
    # ask for confirmation before the actual storing is performed
    if click.confirm("Before continuing, please check the displayed list "
                     "for possible errors! Continue and store?"):
        for potcar_file_node in potentials_to_store:
            stored_node = potcar_file_node.store()
            click.echo("Created new VaspPotcarFile node with UUID {} at ID {}"
                       .format(stored_node.uuid, stored_node.id))
    else:
        click.echo("Aborting. No potential was stored to the database!")


@potcar.command('list')
@click.option('--name', '-n', nargs=1, type=str, default=None,
              help=("Name used to identify the stored pseudo-potential (i.e. "
                    "Li, Li_sv, ...)"))
@click.option('--element', '-e', nargs=1, type=str, default=None,
              help=("Element associated with the stored pseudo-potential "))
@click.option('--functional', '-f', nargs=1, type=str, default=None,
              help=("Functional of the stored pseudo-potential (i.e. one of "
                    "lda_us, lda, lda_52, lda_54, pbe, pbe_52, pbe_54, "
                    "pw91_us or pw91)"))
def list_potcar(name, element, functional):
    """
    List VASP pseudo-potentials available in the AiiDA database.

    Generate and display a list of all pseudo-potentials available in the
    database with certain properties (i.e. name, functional or the
    associated element). If multiple identifiers are specified only
    pseudo-potentials matching all identifiers simultaneously will be shown
    """
    from tabulate import tabulate

    from aiida_cusp.data.inputs.vasp_potcar import VaspPotcarFile

    if not any([name, element, functional]):
        click.echo("Please specify a potential name, element or a "
                   "functional")
        return
    # query the database for stored pseudo-potentials matching all of the
    # given identifiers simultaneously
    potential_nodes = VaspPotcarFile.from_tags(name=name, element=element,
                                               functional=functional)
    # exit immediately if no potentials are found
    if len(potential_nodes) == 0:
        click.echo("No pseudo-potentials found for the given identifiers")
        return
    click.echo("")
    click.echo("Showing potentials for")
    click.echo("\tname:       {}".format(name or 'all'))
    click.echo("\telement:    {}".format(element or 'all'))
    click.echo("\tfunctional: {}".format(functional or 'all'))
    click.echo("")
    tab_entries = []
    for potential_node in potential_nodes:
        tab_entries.append([
            potential_node.id,
            potential_node.uuid,
            potential_node.name,
            potential_node.element,
            potential_node.functional,
        ])
    tab_headers = ['id', 'uuid', 'name', 'element', 'functional']
    table = tabulate(tab_entries, headers=tab_headers, tablefmt='simple')
    click.echo(table)


@potcar.command('show')
@click.argument('pk', nargs=1, type=int)
@click.option('--full', is_flag=True)
def show_potcar(pk, full):
    """
    Display a pseudo-potential's header contents.

    By default only displays the header contents of the potential file stored
    at the given ID. The complete contents can be accessed by specifying the
    `--full` flag.
    """
    import re
    from aiida.orm import load_node

    from aiida_cusp.utils.exceptions import CommandLineError

    potential_content = load_node(pk).get_content()
    if not full:  # only show the header contents
        match = re.search(r"(?i)([\S\s]*)(?=end of psctr)", potential_content)
        if match is not None:
            info = match.group(0)
        else:
            raise CommandLineError("An error occured while parsing the "
                                   "potential header from the stored "
                                   "pseudo-potential file contents (Try to "
                                   "add the --full flag to show the contents "
                                   "anyway)")
    else:  # show the full potential contents
        info = potential_content
    # print out the potential info to screen
    click.echo(info)
