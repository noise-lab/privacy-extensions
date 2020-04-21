#!/bin/bash

set -e

SELFPATH=$(dirname $(realpath "$0"))

LOGS=$(realpath "${1}")
DATABASE_CONFIG=$(realpath "${2}")
DOMAINS_LIST=$(realpath "${3}")
BROWSER=${4}

mkdir -p ${LOGS}

# wrapper.py assumes that various files are in the same directory
pushd "${SELFPATH}/../docker" > /dev/null

while true; do
    UUID=$(uuidgen -t)
    echo "Starting measurement run '${UUID}' at $(date)"
    pipenv run python3 wrapper.py \
        ${LOGS}/${UUID}.log \
        ${DATABASE_CONFIG} \
        ${DOMAINS_LIST} \
        ${UUID} \
        ${BROWSER}
    echo "Completed measurement run '${UUID}' at $(date)"
done

popd > /dev/null
