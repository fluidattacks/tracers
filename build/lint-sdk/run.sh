#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
      pushd src/sdk \
    &&  poetry run mypy \
          --strict \
          . \
    &&  poetry run prospector \
          --strictness veryhigh \
          --with-tool mypy \
          --without-tool pep257 \
    &&  poetry run prospector \
          --strictness veryhigh \
          --without-tool pep257 \
          ../../examples \
  &&  popd \
  ||  return 1
}

main
