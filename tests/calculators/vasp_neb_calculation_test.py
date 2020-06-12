# -*- coding: utf-8 -*-


import pytest


@pytest.mark.parametrize('valid_input', ['incar', 'kpoints', 'neb_path',
                         'potcar', 'restart'])
def test_input_port_availability(valid_input):
    from aiida.plugins import CalculationFactory
    inputs = CalculationFactory('cusp.vasp_neb').get_builder()._valid_fields
    assert valid_input in inputs


# TODO: Do this directly in the sanbox using prepare_for_submission
# ignore BadPotcarWarning raised by pymatgen. i don't care if pymatgen does
# not like my test "potential"
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_vasp_neb_calculation_setup(code_vasp, incar, kpoints, poscar,
                                    with_pbe_potcars, temporary_cwd,
                                    clear_database_after_test):
    import pathlib

    from aiida.plugins import CalculationFactory
    from aiida.engine import run, submit

    from aiida_cusp.data import VaspPotcarData

    # set the input plugin for code
    code_vasp.set_attribute('input_plugin', 'cusp.vasp_neb')

    VaspCalc = CalculationFactory('cusp.vasp_neb')
    # setup calculation inputs
    builder = VaspCalc.get_builder()
    builder.code = code_vasp
    builder.incar = incar
    builder.kpoints = kpoints
    builder.neb_path = {'00': poscar, '01': poscar, '02': poscar}
    builder.potcar = VaspPotcarData.from_structure(poscar, 'pbe')
    builder.metadata.options.resources = {'num_machines': 1}
    builder.metadata.dry_run = True
    # perform the dry run
    run(builder)
    # assert the written files and folder structure
    submit_test_path = pathlib.Path.cwd().absolute() / 'submit_test'
    for written_file in submit_test_path.rglob('*'):
        print(written_file)
