#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
  export TRACERS_API_TOKEN='token'
  export TRACERS_ENDPOINT_URL='http://localhost:8000/api'

      echo '[INFO] Testing the SDK' \
  && pushd src/sdk \
    &&  echo '[INFO] Running tests' \
    &&  rm -f ../../examples/*.output \
    &&  for example in ../../examples/*.py
        do
              echo "[INFO] Running test: ${example}" \
          &&  poetry run python "${example}" |& tee "${example%.*}.output" \
          ||  return 1
        done \
  &&  popd \
  ||  return 1
}

main
