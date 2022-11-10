#!/usr/bin/env bash

OS=$(uname)
if [[ $OS == "Darwin" ]]; then
	# OSX uses BSD readlink
	BASEDIR="$(dirname "$0")"
else
	BASEDIR=$(readlink -e "$(dirname "$0")")
fi

cd "${BASEDIR}"

docker image build . -t interuss/repo_hygiene

cd ../..

docker container run \
	-v $(pwd):/repo \
	interuss/repo_hygiene \
  /repo
