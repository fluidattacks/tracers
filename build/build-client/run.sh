#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
      echo '[INFO] Building client' \
  && pushd client \
    &&  npx webpack --mode=production \
  &&  popd \
  ||  return 1
}

main
