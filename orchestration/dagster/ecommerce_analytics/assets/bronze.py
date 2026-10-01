import os
import sys
from pathlib import Path

from dagster import asset

# Repo root is parents[4] from .../ecommerce_analytics/assets/bronze.py
# (mirrored in the user_code image under /opt/dagster/app).
_BRONZE_DIR = Path(__file__).resolve().parents[4] / "pipelines" / "ecommerce_bronze"


def _ensure_bronze_pipeline_importable() -> None:
    """Keep import working under DockerRunLauncher multiprocess workers.

    Module-level sys.path edits can be wiped when Dagster respawns step
    workers; re-apply immediately before import. Also chdir so dlt loads
    secrets from pipelines/ecommerce_bronze/.dlt.
    """
    bronze = str(_BRONZE_DIR)
    if bronze not in sys.path:
        sys.path.insert(0, bronze)
    os.chdir(bronze)


@asset(key="ecommerce_bronze")
def ecommerce_bronze() -> None:
    _ensure_bronze_pipeline_importable()
    from ecommerce_bronze_pipeline import load_ecommerce_bronze

    load_ecommerce_bronze()
