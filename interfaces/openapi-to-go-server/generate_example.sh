#!/usr/bin/env bash

OS=$(uname)
if [[ $OS == "Darwin" ]]; then
	# OSX uses BSD readlink
	BASEDIR="$(dirname "$0")"
else
	BASEDIR=$(readlink -e "$(dirname "$0")")
fi

cd "${BASEDIR}" || exit

docker image build -t openapi-to-go-server .

docker container run -it \
  	-v "$(pwd)/../astm-utm/Protocol/utm.yaml:/resources/utm.yaml" \
  	-v "$(pwd)/../uastech/standards/remoteid/augmented.yaml:/resources/rid.yaml" \
	  -v "$(pwd)/example:/resources/example" \
	  openapi-to-go-server \
	      --api_import example/api \
	      --api /resources/utm.yaml@scd \
	      --api /resources/rid.yaml@rid \
	      --api_folder /resources/example/api \
	      --example_folder /resources/example \
	      --include_endpoint_tags dss
