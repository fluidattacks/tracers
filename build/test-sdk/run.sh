#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
  export TRACERS_DAEMON_SECONDS_BETWEEN_UPLOADS='0'

      echo '[INFO] Testing the SDK' \
  && pushd sdk \
    &&  echo '[INFO] Running tests' \
    &&  rm -f ../examples/*.output \
    &&  for example in ../examples/*.py
        do
              echo "[INFO] Running test: ${example}" \
          &&  poetry run python "${example}" |& tee "${example%.*}.output" \
          ||  return 1
        done \
  &&  popd \
  ||  return 1
}

main
