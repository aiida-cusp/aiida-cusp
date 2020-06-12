# -*- coding: utf-8 -*-


import pytest


@pytest.mark.parametrize('valid_input', ['incar', 'kpoints', 'poscar',
                         'potcar', 'restart'])
def test_input_port_availability(valid_input):
    from aiida.plugins import CalculationFactory
    inputs = CalculationFactory('cusp.vasp').get_builder()._valid_fields
    assert valid_input in inputs


# TODO: Do this directly in the sanbox using prepare_for_submission
# ignore BadPotcarWarning raised by pymatgen. i don't care if pymatgen does
# not like my test "potential"
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_vasp_calculation_setup(code_vasp, incar, kpoints, poscar,
                                with_pbe_potcars, temporary_cwd,
                                clear_database_after_test):
    import pathlib

    from aiida.plugins import CalculationFactory
    from aiida.engine import run, submit

    from aiida_cusp.data import VaspPotcarData

    # set the input plugin for code
    code_vasp.set_attribute('input_plugin', 'cusp.vasp')

    VaspCalc = CalculationFactory('cusp.vasp')
    # setup calculation inputs
    builder = VaspCalc.get_builder()
    builder.code = code_vasp
    builder.incar = incar
    builder.kpoints = kpoints
    builder.poscar = poscar
    builder.potcar = VaspPotcarData.from_structure(poscar, 'pbe')
    builder.metadata.options.resources = {'num_machines': 1}
    builder.metadata.dry_run = True
    # perform the dry run
    run(builder)
    # assert the written files / folders
    submit_test_path = pathlib.Path.cwd().absolute() / 'submit_test'
    written_files = [f.name for f in submit_test_path.rglob('*')
                     if f.is_file()]
    assert 'INCAR' in written_files
    assert 'KPOINTS' in written_files
    assert 'POSCAR' in written_files
    assert 'POTCAR' in written_files
