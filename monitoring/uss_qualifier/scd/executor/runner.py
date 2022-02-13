
import json
import typing
from typing import Dict

from monitoring.monitorlib.scd_automated_testing.scd_injection_api import InjectFlightResult, \
    InjectFlightResponse
from monitoring.uss_qualifier.scd.configuration import SCDQualifierTestConfiguration
from monitoring.uss_qualifier.scd.data_interfaces import AutomatedTest, TestStep, FlightInjectionAttempt
from monitoring.uss_qualifier.scd.executor.target import TestTarget
from monitoring.uss_qualifier.scd.reports import Report


class TestRunner:
    """A class to run automated test steps for a specific combination of targets per uss roles"""

    def __init__(self, automated_test_id: str, automated_test: AutomatedTest, targets: Dict[str, TestTarget]):
        self.automated_test_id = automated_test_id
        self.automated_test = automated_test
        self.targets = targets
        self.report = Report(configuration=self.get_scd_configuration())

    def get_scd_configuration(self) -> SCDQualifierTestConfiguration:
        return SCDQualifierTestConfiguration(injection_targets=list(map(lambda t: t.config, self.targets.values())))

    def run_automated_test(self, dry=False):
        for step in self.automated_test.steps:
            print('[SCD]   Running step {}'.format(step.name))
            self.execute_step(step, dry=dry)

    def teardown(self, dry=False):
        print ("[SCD]   Teardown {}".format(self.automated_test.name))
        for role, target in self.targets.items():
            target.delete_all_flights(dry=dry)

    def execute_step(self, step: TestStep, dry=False):
        target = self.get_target(step)
        if target is None:
            # TODO implement reporting
            self.print_targets_state()
            raise RuntimeError("[SCD] Error: Unable to identify the target managing flight {}".format(
                step.inject_flight.name if 'inject_flight' in step else step.delete_flight.flight_name
            ))

        if 'inject_flight' in step:
            print("[SCD]     Step: Inject flight {} to {}".format(step.inject_flight.name, target.name))
            resp = target.inject_flight(step.inject_flight, dry=dry)
            # TODO: Move evaluation at the end of the execution
            self.evaluate_inject_flight_response(step.inject_flight, resp, dry=dry)
        elif 'delete_flight' in step:
            print("[SCD]     Step: Delete flight {} to {}".format(step.delete_flight.flight_name, target.name))
            target.delete_flight(step.delete_flight.flight_name, dry=dry)
        else:
            print("[SCD] Warning: no action defined for step {}".format(step.name))

    def get_managing_target(self, flight_name: str) -> typing.Optional[TestTarget]:
        for role, target in self.targets.items():
            if target.is_managing_flight(flight_name):
                return target
        return None

    def get_target(self, step: TestStep) -> typing.Optional[TestTarget]:
        if 'inject_flight' in step:
            return self.targets[step.inject_flight.injection_target.uss_role]
        elif 'delete_flight' in step:
            return self.get_managing_target(step.delete_flight.flight_name)
        else:
            raise NotImplementedError("Unsupported step. A Test Step shall contain either a inject_flight or a delete_flight object.")

    # TODO: Use this method as a canvas to create findings and move the final evaluation at the end of the execution.
    def evaluate_inject_flight_response(self, attempt: FlightInjectionAttempt, resp: InjectFlightResponse, dry=False) -> bool:
        if dry and resp.result == InjectFlightResult.DryRun:
            print("[SCD]     Result: SKIP")
            return True
        if resp.result not in attempt.known_responses.acceptable_results:
            print("[SCD]     Result: ERROR. Received {}, expected one of {}. Reason: {}".format(
                resp.result,
                attempt.known_responses.acceptable_results,
                resp.get('notes', None))
            )
            return False
        print("[SCD]     Result: SUCCESS")
        return True

    def print_targets_state(self):
        print("[SCD] Targets States:")
        for name, target in self.targets.items():
            print(f"[SCD]   - {name}: {target.created_flight_ids}")

    def print_test_plan(self):
        self.run_automated_test(dry=True)
        self.teardown(dry=True)

    def print_report(self):
        print(json.dumps(self.report))

