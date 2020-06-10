# -*- coding: utf-8 -*-


import pytest


@pytest.fixture(scope='function')
def code_cusp_vasp(vasp_code):
    """
    Create a code object using the cusp.vasp input plugin.
    """
    vasp_code.set_attribute('input_plugin', 'cusp.vasp')
    vasp_code.store()
    yield vasp_code


@pytest.fixture(scope='function')
def code_cusp_cstdn(cstdn_code):
    """
    Create a code object using the cusp.vasp input plugin.
    """
    cstdn_code.set_attribute('input_plugin', 'cusp.vasp')
    cstdn_code.store()
    yield cstdn_code


@pytest.mark.parametrize('valid_input', ['incar', 'kpoints', 'poscar',
                         'potcar', 'restart'])
def test_input_port_availability(valid_input):
    from aiida.plugins import CalculationFactory
    inputs = CalculationFactory('cusp.vasp').get_builder()._valid_fields
    assert valid_input in inputs


@pytest.mark.parametrize('with_mpi,runcmd_expected',
[   # noqa: E128
    (True, "'mpirun' '-np' '1' '/path/to/vasp'  > 'aiida.out' 2> 'aiida.err'"),
    (False, "'/path/to/vasp'  > 'aiida.out' 2> 'aiida.err'"),
])
# ignore BadPotcarWarning raised by pymatgen. i don't care if pymatgen does
# not like my test "potential"
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_basic_vasp_no_custodian(code_cusp_vasp, incar, kpoints, poscar,
                                 with_H_PBE_potcar, temporary_cwd,
                                 clear_database_after_test, with_mpi,
                                 runcmd_expected):
    import pathlib

    from aiida.plugins import CalculationFactory
    from aiida.engine import run, submit

    from aiida_cusp.data import VaspPotcarData

    VaspCalc = CalculationFactory('cusp.vasp')
    # setup calculation inputs
    builder = VaspCalc.get_builder()
    builder.code = code_cusp_vasp
    builder.incar = incar
    builder.kpoints = kpoints
    builder.poscar = poscar
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
# ignore BadPotcarWarning raised by pymatgen. i don't care if pymatgen does
# not like my test "potential"
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_basic_vasp_with_custodian(code_cusp_vasp, code_cusp_cstdn, incar,
                                   kpoints, poscar, with_H_PBE_potcar,
                                   temporary_cwd, clear_database_after_test,
                                   with_mpi, runcmd_expected):
    import pathlib

    from aiida.plugins import CalculationFactory
    from aiida.engine import run, submit

    from aiida_cusp.data import VaspPotcarData

    VaspCalc = CalculationFactory('cusp.vasp')
    # setup calculation inputs
    builder = VaspCalc.get_builder()
    builder.code = code_cusp_vasp
    builder.custodian.code = code_cusp_cstdn
    builder.incar = incar
    builder.kpoints = kpoints
    builder.poscar = poscar
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


# ignore BadPotcarWarning raised by pymatgen. i don't care if pymatgen does
# not like my test "potential"
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_vasp_calculation_setup(code_cusp_vasp, incar, kpoints, poscar,
                                with_H_PBE_potcar, temporary_cwd,
                                clear_database_after_test):
    import pathlib

    from aiida.plugins import CalculationFactory
    from aiida.engine import run, submit

    from aiida_cusp.data import VaspPotcarData

    VaspCalc = CalculationFactory('cusp.vasp')
    # setup calculation inputs
    builder = VaspCalc.get_builder()
    builder.code = code_cusp_vasp
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
