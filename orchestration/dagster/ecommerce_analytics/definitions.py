from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
)

from orchestration.dagster.ecommerce_analytics.assets.bronze import ecommerce_bronze
from orchestration.dagster.ecommerce_analytics.assets.gold import ecommerce_gold
from orchestration.dagster.ecommerce_analytics.assets.silver import ecommerce_silver

# SPEC_DEVIATION: Dagster JobDefinition has no max_concurrent_runs field.
# Reason: encode lock-parity intent as job metadata for unit tests; instance
# run-queue / tag limits are wired with dagster.yaml in the Compose phase.
ecommerce_medallion_job = define_asset_job(
    name="ecommerce_medallion_job",
    selection=AssetSelection.assets(
        ecommerce_bronze,
        ecommerce_silver,
        ecommerce_gold,
    ),
    metadata={"max_concurrent_runs": 1},
)

ecommerce_medallion_daily = ScheduleDefinition(
    name="ecommerce_medallion_daily",
    job=ecommerce_medallion_job,
    cron_schedule="0 6 * * *",
    execution_timezone="America/Sao_Paulo",
)

defs = Definitions(
    assets=[ecommerce_bronze, ecommerce_silver, ecommerce_gold],
    jobs=[ecommerce_medallion_job],
    schedules=[ecommerce_medallion_daily],
)
