#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
      echo '[INFO] Launching the back-end' \
  && pushd server \
    &&  poetry run uvicorn \
          --host 0.0.0.0 \
          --port 8000 \
          --reload \
          backend.asgi:SERVER \
  &&  popd \
  ||  return 1
}

main
