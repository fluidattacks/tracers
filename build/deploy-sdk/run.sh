#! /usr/bin/env bash

source 'build/include/generic/shell-options.sh'

function main {
  export PYPI_PASSWORD
  export PYPI_USERNAME
  export _PWD="${PWD}"
  local version

  function restore_version {
    rm --force "${_PWD}/sdk/README.md"
    sed --in-place 's|^version.*$|version = "1.0.0"|g' "${_PWD}/sdk/pyproject.toml"
    sed --in-place 's|^readme.*$|readme = "../README.md"|g' "${_PWD}/sdk/pyproject.toml"
  }

      ./build/build-sdk/run.sh \
  &&  ./build/lint-sdk/run.sh \
  &&  ./build/test-sdk/run.sh \
  &&  pushd sdk \
    &&  version=$(poetry run python -c 'if True:
          import time
          now=time.gmtime()
          minutes_month=(
            (now.tm_mday - 1) * 1440
            + now.tm_hour * 60
            + now.tm_min
          )
          print(time.strftime(f"%y.%m.{minutes_month}"))
        ') \
    &&  echo "[INFO] Tagging: ${version}" \
    &&  git tag \
          --message "release-${version}" \
          --sign \
          "release-${version}" \
    &&  git push \
          origin \
          "release-${version}" \
    &&  echo "[INFO] Publishing: ${version}" \
    &&  trap 'restore_version' 'EXIT' \
    &&  cp --force ../README.md . \
    &&  sed --in-place \
          "s|^version = .*$|version = \"${version}\"|g" \
          'pyproject.toml' \
    &&  sed --in-place \
          "s|^readme.*$|readme = \"README.md\"|g" \
          'pyproject.toml' \
    &&  poetry publish \
          --build \
          --no-interaction \
          --password "${PYPI_PASSWORD}" \
          --username "${PYPI_USERNAME}" \
  &&  popd \
  ||  return 1
}

main
