# DSS testing

All of the tests below except the Interoperability tests are run as part of
continuous integration before a pull request is approved to be merged.

## Unit tests
Source code is often accompanied by `*_test.go` files which define unit tests
for the associated code.  All unit tests for the repo may be run with the
following command from the root folder of the repo:
```shell script
go test -count=1 -v ./...
```
The above command skips the CockroachDB tests because a `store-uri` argument is
 not provided.  To perform the CockroachDB tests, run the following command
 from the root folder of the repo:
```shell script
make test-cockroach
```

## Integration tests
For tests that benefit from being run in a fully-constructed environment, the
[`docker_e2e.sh`](docker_e2e.sh) script in this folder sets up a full
environment and runs a set of tests in that environment.  Docker is the only
prerequisite to running this end-to-end test on your local system.

## Lint checks
One of the continuous integration presubmit checks on this repository checks Go
style with a linter.  To run this check yourself, run the following command in
the root folder of this repo:
```shell script
docker run --rm -v $(pwd):/app -w /app golangci/golangci-lint:v1.26.0 golangci-lint run --timeout 5m -v -E gofmt,bodyclose,rowserrcheck,misspell,golint -D staticcheck,vet
```

## Interoperability tests
The [interoperability folder](interoperability) contains a test suite that
verifies interoperability between two DSS instances in the same region; see
[the README](interoperability/README.md) for more information.
