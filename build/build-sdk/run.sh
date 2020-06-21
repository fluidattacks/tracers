#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
      echo '[INFO] Building the SDK' \
  && pushd src/sdk \
    &&  poetry update \
    &&  poetry install \
  &&  popd \
  ||  return 1
}

main
