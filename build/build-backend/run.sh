#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
      echo '[INFO] Building the Backend' \
  && pushd src/backend \
    &&  poetry cache clear --all . \
    &&  poetry update \
    &&  poetry install \
  &&  popd \
  ||  return 1
}

main
