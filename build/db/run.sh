#! /usr/bin/env nix-shell
#!   nix-shell -i bash
#!   nix-shell --option restrict-eval false
#!   nix-shell --option sandbox false
#!   nix-shell --show-trace
#!   nix-shell default.nix
#  shellcheck shell=bash

source "${srcShellOptions}"

function main {
  export srcExternalDynamoDbLocal
  local data_folder='./.data/dynamo'
  local dynamo_port='8022'
  local dynamo_pid=''

      echo '[INFO] Unzipping DynamoDB' \
  &&  mkdir -p "${data_folder}" \
  &&  pushd "${data_folder}" \
    &&  unzip -u "${srcExternalDynamoDbLocal}" \
  &&  popd \
  &&  {
        java \
          -delayTransientStatuses \
          -Djava.library.path="${data_folder}/DynamoDBLocal_lib" \
          -inMemory \
          -jar "${data_folder}/DynamoDBLocal.jar" \
          -port "${dynamo_port}" \
          -sharedDb \
        &
        dynamo_pid="$!"
      } \
  &&  echo '[INFO] Waiting 5 seconds to leave DynamoDB start' \
  &&  sleep 5 \
  &&  echo "[INFO] DynamoDB is ready and listening on port ${dynamo_port}!" \
  &&  echo "[INFO] Hit Ctrl+C to exit" \
  &&  fg %1 \
  ||  kill -9 "${dynamo_pid}"
}

main
