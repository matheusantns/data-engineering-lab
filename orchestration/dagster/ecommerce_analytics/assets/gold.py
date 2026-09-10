from dagster import asset

from orchestration.dagster.ecommerce_analytics.assets.silver import ecommerce_silver
from orchestration.dagster.ecommerce_analytics.resources.dbt_runner import run_dbt_build


@asset(key="ecommerce_gold", deps=[ecommerce_silver])
def ecommerce_gold() -> None:
    run_dbt_build("path:models/gold")
