from dagster import asset

from orchestration.dagster.ecommerce_analytics.assets.bronze import ecommerce_bronze
from orchestration.dagster.ecommerce_analytics.resources.dbt_runner import run_dbt_build


@asset(key="ecommerce_silver", deps=[ecommerce_bronze])
def ecommerce_silver() -> None:
    run_dbt_build("path:models/silver")
