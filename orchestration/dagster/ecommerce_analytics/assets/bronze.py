import sys
from pathlib import Path

from dagster import asset

_BRONZE_DIR = str(
    Path(__file__).resolve().parents[4] / "pipelines" / "ecommerce_bronze"
)
if _BRONZE_DIR not in sys.path:
    sys.path.insert(0, _BRONZE_DIR)


@asset(key="ecommerce_bronze")
def ecommerce_bronze() -> None:
    from ecommerce_bronze_pipeline import load_ecommerce_bronze

    load_ecommerce_bronze()
