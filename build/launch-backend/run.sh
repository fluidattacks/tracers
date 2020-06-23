#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
  export TRACERS_API_TOKEN='token'
  export TRACERS_ENDPOINT_URL='http://localhost:8000/api'

      echo '[INFO] Launching the back-end' \
  && pushd src/backend \
    &&  poetry run uvicorn \
          --host 0.0.0.0 \
          --port 8000 \
          --reload \
          backend.asgi:SERVER \
  &&  popd \
  ||  return 1
}

main
