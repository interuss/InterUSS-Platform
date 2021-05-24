import uuid
from monitoring.rid_qualifier.aircraft_state_replayer import TestHarness, TestBuilder
import arrow
from monitoring.rid_qualifier.utils import RIDQualifierTestConfiguration, RIDQualifierUSSConfig

def build_uss_config(injection_base_url:str) -> RIDQualifierUSSConfig:
  return RIDQualifierUSSConfig(injection_base_url=injection_base_url)


def build_test_configuration(locale: str, auth_spec:str, uss_config:RIDQualifierUSSConfig) -> RIDQualifierTestConfiguration:
    now = arrow.now()
    test_start_time = now.shift(minutes=3) # Start the test three minutes from the time the test_exceutor is run.

    test_config = RIDQualifierTestConfiguration(
      locale = locale,
      now = now.isoformat(),
      test_start_time = test_start_time.isoformat(),
      auth_spec = auth_spec,
      usses = [uss_config]
    )

    return test_config

def main(test_configuration: RIDQualifierTestConfiguration):
    # This is the configuration for the test.
    my_test_builder = TestBuilder(test_configuration = test_configuration)
    test_payloads = my_test_builder.build_test_payloads()
    test_id = str(uuid.uuid4())

    # Inject flights into all USSs
    for i, uss in enumerate(test_configuration.usses):
      uss_injection_harness = TestHarness(
        auth_spec=test_configuration.auth_spec,
        injection_base_url=uss.injection_base_url)
      uss_injection_harness.submit_test(test_payloads[i], test_id)

    # TODO: call display data evaluator to read RID system state and compare to expectations
