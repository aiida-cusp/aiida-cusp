# -*- coding: utf-8 -*-

"""
Multi-Relaxation Workchain for VASP Relaxations
"""

import re

from aiida.plugins import CalculationFactory
from aiida.engine import WorkChain, ToContext, while_
from aiida.orm import Bool
from aiida_cusp.calculators.calculation_base import CalculationBase
from aiida_cusp.calculators import VaspCalculation
from aiida_cusp.data import VaspIncarData


class MultiRelaxWorkChain(WorkChain):
    """
    Multi-Relaxation Workflow for VASP calculations.

    Beside the usually required inputs for VASP calculations, i.e.
    POSCAR, KPOINTS and POTCAR, this workchain, instead of a single
    one, introduces a dynamical input namespace `incars` which
    accepts an arbitrary amount of INCAR entries of the form

    incars = {
        'incar_1': VaspIncarData,
        'incar_2': VaspIncarData,

           ...

        'incar_N': VaspIncarData,
    }

    In the initial relaxation run the provided POSCAR, KPOINTS and
    POTCAR are used together with the INCAR provided at the first
    index, i.e. `incar_1` to start the calculation. The workchain
    then proceeds to iterate over the given INCAR namespace and
    starts subsequent calculations from the given `incar_2` up
    to the last `incar_N`. Note that for every restarted calculation
    the outputs of the previous calculation are used, with CONTCAR
    copied over to POSCAR, and only INCAR being overwritten with the
    data provided by the corresponding incar-namespace entry.

    A flow chart illustrating which and how the provided resources
    are used within this workflow is show in the following:

    {
        'incar_1': INCAR_DATA, ------.  POSCAR, KPOINTS, POTCAR
        'incar_2': INCAR_DATA, ----. |    |        |        |
                                   | |    `--------+--------´
         ...                       | |             |
                                   | |             |
        'incar_N': INCAR_DATA, --. | |             |
    }                            | | |             V
                                 | | '---> RELAXATION RUN 1
                                 | |               |
                                 | |            OUTPUTS
                                 | |               |
                                 | |               V
                                 | '-----> RELAXATION RUN 2
                                 |                 |
                                 |              OUTPUTS
                                 |                 |
                                 |                 V
                                 |                ...
                                 |                 |
                                 |                 V
                                 '-------> RELAXATION RUN N
                                                   |
                                                   V
                                             FINAL OUTPUTS

    """
    @classmethod
    def define(cls, spec):
        super(MultiRelaxWorkChain, cls).define(spec)
        # only expose the required settings from the base calculation
        spec.expose_inputs(VaspCalculation, exclude=('incar', 'neb_path',
                           'remote_folder', 'restart', 'metadata'))
        # setup new namespace for incar
        spec.input_namespace("incar", valid_type=VaspIncarData, dynamic=True)
        # introduce job_options namespace. everything defined here is directly
        # passed to the calculations metadata.options key
        spec.input_namespace("job_options", required=True, valid_type=dict,
                             non_db=True)
        # outline for the job
        spec.outline(
            cls.verify_workflow_inputs,
            cls.initialize_multi_relaxation,
            while_(cls.incar_not_exhausted)(
                cls.setup_calculation_inputs,
                cls.run_vasp_relaxation,
                cls.assert_run_successful,
            ),
            cls.register_workflow_outputs,
        )
        # register generated workflow outputs
        spec.expose_outputs(VaspCalculation)
        # failure codes
        spec.exit_code(400, 'ENOATTR', ('Missing workchain parameter'))
        spec.exit_code(401, 'EINVAL', ('Invalid parameter name'))
        spec.exit_code(402, 'ECANCELED', ('Workflow aborted'))
        spec.exit_code(403, 'ENOENT', ('File or directory not found'))

    def verify_workflow_inputs(self):
        """
        Check and verify the given workchain inputs
        """
        self.report("verifying passed workflow inputs")
        # inputs are marked optional on base calculation class to allow
        # restarts without any inputs given, thus we need to check that
        # those are present on the workchain!
        if not self.inputs.get('incar', False):
            self.report("at least one INCAR is needed to run this "
                        "workflow")
            return self.exit_codes.ENOATTR
        if not self.inputs.get('poscar', False):
            self.report("no input structure (POSCAR) was passed to the "
                        "workflow")
            return self.exit_codes.ENOATTR
        if not self.inputs.get('kpoints', False):
            self.report("no KPOINTS were passed to the workflow")
            return self.exit_codes.ENOATTR
        if not self.inputs.get('potcar', False):
            self.report("no pseudo-potentials (POTCAR) were passed to "
                        "the workflow")
            return self.exit_codes.ENOATTR
        # validate namespace keys for provided incar data
        int_keys = []
        for key, item in self.inputs.get('incar').items():
            match = re.match(r"^incar_\d+$", key)
            if not match:
                self.report(f"encountered INCAR parameter with "
                            f"malformed namespace key '{key}'")
                return self.exit_codes.EINVAL
            # assure that all identifiers are unique, i.e. 1, 01, etc., will
            # be treated as identical
            int_key = int(match.group().split("_")[-1])
            if int_key in int_keys:
                self.report(f"encountered INCAR parameter with "
                            f"non-unique index identifier '{key}'")
                return self.exit_codes.EINVAL
            else:
                int_keys.append(int_key)

    def initialize_multi_relaxation(self):
        self.report("setting up and initializing internal workflow "
                    "parameters")
        # store initial parameters internally
        self.ctx.initial_poscar = self.inputs.get('poscar')
        self.ctx.initial_potcar = self.inputs.get('potcar')
        self.ctx.initial_kpoints = self.inputs.get('kpoints')
        self.ctx.initial_options = self.inputs.get('job_options')
        # create ordered list of provided incar data
        self.ctx.incars = sorted([(int(k.split("_")[-1]), v) for (k, v) in
                                  self.inputs.incar.items()])
        self.ctx.run_id = 0
        self.ctx.next_run_inputs = None

        self.report(f"{self.exposed_inputs(VaspCalculation)}")

    def setup_calculation_inputs(self):
        """
        This function sets up the required inputs for the VASP calculation
        """
        if self.ctx.run_id == 0:  # this is the first run
            self.report("setting up calculation inputs for first run")
            inputs = self.exposed_inputs(VaspCalculation)
            self.report(f"{inputs}")
            inputs['incar'] = self.get_next_incar_data()
            inputs['metadata'] = {'options': self.ctx.initial_options}
        else:
            self.report("setting up calculation inputs for subsequent run")
            inputs = self.exposed_inputs(VaspCalculation)
            inputs['metadata'] = {'options': self.ctx.initial_options}
            # remove poscar, potcar and kpoints
            inputs.pop('poscar')
            inputs.pop('potcar')
            inputs.pop('kpoints')
            # update incar from the stored incar list
            inputs['incar'] = self.get_next_incar_data()
            # setup restart options with remote folder from previous
            # calculation
            remote_folder = self.ctx.last_calculation.outputs.remote_folder
            copy_contcar = inputs.get('restart.contcar_to_poscar', Bool(True))
            inputs['restart'] = {
                'folder': remote_folder,
                'contcar_to_poscar': copy_contcar,
            }
        self.ctx.next_run_inputs = inputs

    def get_current_step_name(self):
        """
        Creates the name of the current calculation step
        """
        return f"workflow_step_{self.ctx.run_id}"

    def get_next_incar_data(self):
        """
        Return INCAR data for next step
        """
        (index, incar) = self.ctx.incars.pop()
        return incar

    def incar_not_exhausted(self):
        """
        Check the list of available INCARs before each run.

        Returns `True` as long as there are INCARs stored in the
        internal list. Once the internal list is exhausted this
        function returns `False` effectively ending the relaxation
        loop and stopping the workchain
        """
        return len(self.ctx.incars) != 0

    def run_vasp_relaxation(self):
        """
        Run the VASP calculation
        """
        step_name = self.get_current_step_name()
        inputs = self.ctx.next_run_inputs
        self.report(f"submitting calculation for current workflow step "
                    f"#{self.ctx.run_id}")
        node = self.submit(VaspCalculation, **inputs)
        return ToContext(last_calculation=node)

    def assert_run_successful(self):
        """
        Make sure the previous run was successful
        """
        if not self.ctx.last_calculation.is_finished_ok:
            step_name = self.get_current_step_name()
            self.report(f"workflow step '{step_name}' (run_id = "
                        f"{self.ctx.run_id} did not finish successfully")
            return self.exit_codes.ECANCELED
        if not self.ctx.last_calculation.outputs.remote_folder:
            self.report(f"unable to retrieved remote folder from parent "
                        f"calculation ({self.ctx.last_calculation.pid})")
            return self.exit_codes.ENOENT
        # Otherwise, increase counter and proceed with next iteration
        self.ctx.run_id += 1

    def register_workflow_outputs(self):
        """
        Simply register the outputs of the last calculation as
        workflow outputs
        """
        self.out_many(
            self.exposed_outputs(self.ctx.last_calculation, VaspCalculation)
        )
