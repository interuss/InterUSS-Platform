# UFT Message Signing tests for SCD using uss_qualifier

UTM Field Test (UFT) has a requirement for USSes to sign their message requests
and responses in the SCD flow using IATF certificates provided by FAA.

This test suite helps to test the message signing by extending [suites.astm.utm.f3548_21](monitoring/uss_qualifier/suites/astm/utm/f3548_21.yaml)
with scenarios that trigger reporting of message signing in the interactions with mock_uss.

## Test Setup

The test setup includes running the following components, as also shown in the [diagram](./InterUss_Test_Harness_With_Message_Signing.png)

1. uss_qualifier - This is the test driver that injects the operations for the SCD flow tests in USSes.
2. Auth - This auth server provides access tokens and the public key for token validation for USS-to-USS and USS-to-DSS communication. In a local deployment of the test infrastructure, this can be supplied by an instance of dummy auth running as a dockerized container exposing port 8085, as per build/dev/run_locally.sh.
3. DSS - This is a local DSS running in dockerized container, and is available at port 8082.
4. Mock USS - This is a mock implementation of a USS running as a dockerized container at port 8074.
5. USS-under-Test - This is the USS that needs to be tested.
6. uss_qualifier interface. USSes need to develop an interface for their USS
to interface with the test harness. Uss_Qualifer will inject operations through this interface. The spec to
implement is - [Strategic Coordination Test Data Injection](https://github.com/interuss/automated_testing_interfaces/blob/fa3a5f544161c408f50255630a23b670c74a67d1/scd/v1/scd.yaml)

The main idea behind the tests is that mock_uss will consume and validate all the requests and responses from USS-under-test.

Note - As different USSes have different implementations, it could happen that you might need to create a subscription in the area of the flights.

## Steps to run the test

1. Set your uss_qualifier Interface implementation url in the [configuration file ](monitoring/uss_qualifier/configurations/dev/faa/uft/local_message_signing.yaml )to run the UFT message signing tests. If personal changes are needed, copy this yaml file to monitoring/uss_qualifier/configurations/personal/message_signing.yaml, and edit this file instead.
The property to set is `resources.resource_declarations.flight_planners.specification.flight_planners.participant_id`
2. Run DSS and dummy-oauth using the script [run_locally.sh](build/dev/run_locally.sh)
    ```bash
    ./run_locally.sh
    ```
3. Run mock_uss using the script [run_locally_msgsigning.sh](monitoring/mock_uss/run_locally_msgsigning.sh)
    ```bash
   ./run_locally_msgsigning.sh
    ```
4. Prepare your USS to run with
   1. The auth server used by the UTM ecosystem under test (dummy auth at http://localhost:8085/token or http://host.docker.internal:8085/token in a local deployment of the test infrastructure).
   2. A DSS instance supporting SCD in the UTM ecosystem under test (DSS at http://localhost:8082 or http://host.docker.internal:8085 in a local deployment of the test infrastructure).
5. Run the uss_qualifier interface for your USS.
6. Run uss_qualifier tests using script [run_locally.sh](monitoring/uss_qualifier/run_locally.sh) with config
    ```bash
   ./run_locally.sh configurations.dev.faa.uft.local_message_signing
   ```

## Results
SCD tests report is generated under [uss_qualifier](monitoring/uss_qualifier).
The message signing results will be in the report created for the overall run - report.json. Failed message signing checks will show up as `FailedChecks` within the `FinalizeMessageSigningReport` test scenario.  

### Positive tests -
A valid set of private/public keys are provided for message signing analysis under the [monitioring/monitorlib/messagesigning/keys] folder. The valid key pair, `mock_faa_priv.pem`/`mock_faa_pub.der`, is used by default. The public key is served under the mock_uss endpoint `/mock/scd/.well-known/uas-traffic-management/mock_pub.der`, and can be retreived by the USS under test in order for it to validate the mock_uss responses. This public key was provided by the FAA and will pass SCVP validation. To ensure that this valid keypair is used, make sure that the `USE_VALID_KEY_PAIR` in `run_locally_msgsigning.sh` is set to "true". 


A USS should pass all the uss_qualifier tests in this suite.
The message_signing report includes interactions and issues between the mock_uss and the USS-under-test.
No issues indicate the USS-under-test message-signed all its requests and responses.


### Negative tests -
Replace the private/public keys with invalid key pair by setting the `USE_VALID_KEY_PAIR` in `run_locally_msgsigning.sh` to "false". This will set the keypair to be `mock_priv.pem`/`mock_pub.der`. Using this keypair will lead to invalid signatures, and the `mock_pub.der` will not pass SCVP validation.
The USS-under-test will respond with 403 to all requests from mock_uss. The uss_qualifier tests will not pass.
The message signing section of the report would show `403` in interactions with mock_uss.


### Other notes
Below are examples of valid http message signature headers. Malformed headers can cause validation to fail, for example providing an unreachable url within an `x5u`, or missing quotes in the `utm-message-signature-input` field.


```
{
    ...
    "headers": {
        ...
        "content-digest": "sha-512=:8eCoJlCRDjzhhswDGwC00GfIe7AvGsHuXsBphaZCB9U4kfdMOTJP+bnYNhHdKVPQaSWxTjuim3ywMxh+kIA25w==:",
        "x-utm-jws-header": "alg=\"RS256\", typ=\"JOSE\", kid=\"mock_uss_keyid\", x5u=\"https://host.docker.internal:8074/mock/scd/.well-known/uas-traffic-management/mock_pub.der\"",
        "x-utm-message-signature-input": "utm-message-signature=(\"@status\" \"content-type\" \"content-digest\" \"x-utm-jws-header\");created=1670277282425",
        "x-utm-message-signature": "utm-message-signature=:VrUhTe7g2PdnrX37t4hM6Dj7ggSy9YSYt6AqxvICSBTo+AFTVnhCw6k4Kpo1udVboepVYzYC4MHdjaGoTQ6hDT4gvH63QB3JyEqjs0TrAxFj78D5Rau7Sysku18Y/MJG1/cta7DRekdBQJnhFks0aIYzPTizYt0tUL9jx3yybyuK7jTNdtsFmN5qQDs2upTe0ivQjOWggGACMF1yxMZBsGmPLs24E5LssAfSpa1qunnWQNukMHYxtJ+GFMhAV4LDLsO3QQRidKhuhndqittYrGGujQwSz6WSaO8D+4DjR8vpWeR14JnwEIoS2oS6DiyX4fHMB296ai/tkbzklkbe5g==:"
    }
}
```