#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
      pushd src/sdk \
    &&  poetry update \
    &&  poetry install \
  &&  popd \
  ||  return 1
}

main
