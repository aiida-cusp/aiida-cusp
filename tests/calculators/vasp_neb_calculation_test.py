# -*- coding: utf-8 -*-


import pytest


@pytest.fixture(scope='function')
def code_cusp_vasp_neb(vasp_code):
    """
    Create a code object using the cusp.vasp_neb input plugin.
    """
    vasp_code.set_attribute('input_plugin', 'cusp.vasp_neb')
    vasp_code.store()
    yield vasp_code


@pytest.fixture(scope='function')
def code_cusp_cstdn_neb(cstdn_code):
    """
    Create a code object using the cusp.vasp input plugin.
    """
    cstdn_code.set_attribute('input_plugin', 'cusp.vasp_neb')
    cstdn_code.store()
    yield cstdn_code


@pytest.mark.parametrize('valid_input', ['incar', 'kpoints', 'neb_path',
                         'potcar', 'restart'])
def test_input_port_availability(valid_input):
    from aiida.plugins import CalculationFactory
    inputs = CalculationFactory('cusp.vasp_neb').get_builder()._valid_fields
    assert valid_input in inputs


@pytest.mark.parametrize('with_mpi,runcmd_expected',
[   # noqa: E128
    (True, "'mpirun' '-np' '1' '/path/to/vasp'  > 'aiida.out' 2> 'aiida.err'"),
    (False, "'/path/to/vasp'  > 'aiida.out' 2> 'aiida.err'"),
])
def test_vasp_neb_no_custodian(code_cusp_vasp_neb, incar, kpoints, poscar,
                               with_H_PBE_potcar, temporary_cwd,
                               clear_database_after_test, with_mpi,
                               runcmd_expected):
    import pathlib

    from aiida.plugins import CalculationFactory
    from aiida.engine import run, submit

    from aiida_cusp.data import VaspPotcarData

    VaspCalc = CalculationFactory('cusp.vasp_neb')
    # setup calculation inputs
    builder = VaspCalc.get_builder()
    builder.code = code_cusp_vasp_neb
    builder.incar = incar
    builder.kpoints = kpoints
    builder.neb_path = {'00': poscar, '01': poscar, '02': poscar}
    builder.potcar = VaspPotcarData.from_structure(poscar, 'pbe')
    builder.metadata.options.resources = {'num_machines': 1}
    builder.metadata.dry_run = True
    builder.metadata.options.withmpi = with_mpi
    # perform the dry run
    run(builder)
    # assert submit script contains expected run command
    submit_test_path = pathlib.Path.cwd().absolute() / 'submit_test'
    for submit_script in submit_test_path.rglob('_aiidasubmit.sh'):
        with open(submit_script, 'r') as submit_script_file:
            contents = submit_script_file.read()
        assert runcmd_expected in contents


@pytest.mark.parametrize('with_mpi,runcmd_expected',
[   # noqa: E128
    (True, "'/path/to/cstdn' 'run' 'cstdn_spec.yaml'"),
    (False, "'/path/to/cstdn' 'run' 'cstdn_spec.yaml'"),
])
def test_vasp_neb_with_custodian(code_cusp_vasp_neb, code_cusp_cstdn_neb,
                                 incar, kpoints, poscar, with_H_PBE_potcar,
                                 temporary_cwd, clear_database_after_test,
                                 with_mpi, runcmd_expected):
    import pathlib

    from aiida.plugins import CalculationFactory
    from aiida.engine import run, submit

    from aiida_cusp.data import VaspPotcarData

    VaspCalc = CalculationFactory('cusp.vasp_neb')
    # setup calculation inputs
    builder = VaspCalc.get_builder()
    builder.code = code_cusp_vasp_neb
    builder.custodian.code = code_cusp_cstdn_neb
    builder.incar = incar
    builder.kpoints = kpoints
    builder.neb_path = {'00': poscar, '01': poscar, '02': poscar}
    builder.potcar = VaspPotcarData.from_structure(poscar, 'pbe')
    builder.metadata.options.resources = {'num_machines': 1}
    builder.metadata.dry_run = True
    builder.metadata.options.withmpi = with_mpi
    # perform the dry run
    run(builder)
    # assert submit script contains expected run command
    submit_test_path = pathlib.Path.cwd().absolute() / 'submit_test'
    for submit_script in submit_test_path.rglob('_aiidasubmit.sh'):
        with open(submit_script, 'r') as submit_script_file:
            contents = submit_script_file.read()
        assert runcmd_expected in contents


def test_vasp_neb_calculation_setup(code_cusp_vasp_neb, incar, kpoints, poscar,
                                    with_H_PBE_potcar, temporary_cwd,
                                    clear_database_after_test):
    import pathlib

    from aiida.plugins import CalculationFactory
    from aiida.engine import run, submit

    from aiida_cusp.data import VaspPotcarData

    VaspCalc = CalculationFactory('cusp.vasp_neb')
    # setup calculation inputs
    builder = VaspCalc.get_builder()
    builder.code = code_cusp_vasp_neb
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
