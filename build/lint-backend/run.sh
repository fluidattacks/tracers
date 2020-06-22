#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
      echo '[INFO] Linting the back-end' \
  && pushd src/backend \
    &&  poetry run mypy \
          --ignore-missing-imports \
          --strict \
          . \
    &&  poetry run prospector \
          --strictness veryhigh \
          --without-tool pep257 \
  &&  popd \
  ||  return 1
}

main
