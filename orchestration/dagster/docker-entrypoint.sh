#!/bin/sh
# Inject host bind-mount paths into dagster.yaml for DockerRunLauncher.
# Docker resolves volume sources on the host (via docker.sock), so paths must
# be absolute host paths from DLT_SECRETS_HOST_PATH / DBT_PROFILES_HOST_PATH.
set -e

if [ -z "${DLT_SECRETS_HOST_PATH:-}" ] || [ -z "${DBT_PROFILES_HOST_PATH:-}" ]; then
  echo "ERROR: DLT_SECRETS_HOST_PATH and DBT_PROFILES_HOST_PATH must be set" >&2
  echo "       (absolute host paths; see orchestration/dagster/.env.example)." >&2
  exit 1
fi

sed \
  -e "s|__DLT_SECRETS_HOST_PATH__|${DLT_SECRETS_HOST_PATH}|g" \
  -e "s|__DBT_PROFILES_HOST_PATH__|${DBT_PROFILES_HOST_PATH}|g" \
  /opt/dagster/dagster_home/dagster.yaml.template \
  > /opt/dagster/dagster_home/dagster.yaml

exec "$@"
