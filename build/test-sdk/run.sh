#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
      pushd src/sdk \
    &&  echo '[INFO] Running tests' \
    &&  rm -f ../../examples/*.output \
    &&  for example in ../../examples/*.py
        do
              echo "[INFO] Running test: ${example}" \
          &&  poetry run python "${example}" | tee "${example%.*}.output"
        done \
  &&  popd \
  ||  return 1
}

main
