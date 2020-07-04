#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
      echo '[INFO] Launching client' \
  && pushd client \
    &&  npx webpack-dev-server \
  &&  popd \
  ||  return 1
}

main
