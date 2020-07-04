#! /usr/bin/env nix-shell
#!   nix-shell -i bash
#!   nix-shell --keep AWS_ACCESS_KEY_ID
#!   nix-shell --keep AWS_DEFAULT_REGION
#!   nix-shell --keep AWS_SECRET_ACCESS_KEY
#!   nix-shell --keep AWS_SESSION_TOKEN
#!   nix-shell --keep DYNAMO_ENDPOINT
#!   nix-shell --option restrict-eval false
#!   nix-shell --option sandbox false
#!   nix-shell --show-trace
#!   nix-shell default.nix
#  shellcheck shell=bash

source "${srcShellOptions}"

function main {
  export srcExternalDynamoDbLocal
  export TF_VAR_dynamo_endpoint="${DYNAMO_ENDPOINT}"
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
          -Djava.library.path="${data_folder}/DynamoDBLocal_lib" \
          -jar "${data_folder}/DynamoDBLocal.jar" \
          -delayTransientStatuses \
          -inMemory \
          -port "${dynamo_port}" \
          -sharedDb \
        &
        dynamo_pid="$!"
      } \
  &&  echo '[INFO] Deploying infrastructure' \
  &&  pushd infra \
    &&  terraform init \
    &&  terraform plan \
    &&  terraform apply -auto-approve \
  &&  popd \
  &&  echo "[INFO] DynamoDB is ready and listening on port ${dynamo_port}!" \
  &&  echo "[INFO] Hit Ctrl+C to exit" \
  &&  fg %1 \
  ||  kill -9 "${dynamo_pid}"
}

main
