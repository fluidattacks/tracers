#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
      echo '[INFO] Linting client' \
  && pushd client \
    &&  npm set audit-level high \
    &&  npm config set audit-level high \
    &&  npm audit \
    &&  npx eslint --fix . \
  &&  popd \
  ||  return 1
}

main
