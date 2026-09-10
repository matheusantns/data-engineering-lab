import sys
import unittest
from types import ModuleType
from unittest.mock import MagicMock, patch

from dagster import AssetKey, AssetSelection, materialize


class DefinitionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fake_pipeline = ModuleType("ecommerce_bronze_pipeline")
        fake_pipeline.load_ecommerce_bronze = MagicMock()
        sys.modules["ecommerce_bronze_pipeline"] = fake_pipeline

        from orchestration.dagster.ecommerce_analytics.definitions import defs

        cls.defs = defs

    def setUp(self):
        fake = sys.modules["ecommerce_bronze_pipeline"]
        fake.load_ecommerce_bronze = MagicMock()

    def test_definitions_expose_three_layer_asset_keys(self):
        keys = {
            key.to_user_string()
            for key in self.defs.resolve_asset_graph().get_all_asset_keys()
        }
        self.assertEqual(
            keys,
            {"ecommerce_bronze", "ecommerce_silver", "ecommerce_gold"},
        )

    def test_dependency_edges_bronze_to_silver_to_gold(self):
        graph = self.defs.resolve_asset_graph()
        bronze = AssetKey("ecommerce_bronze")
        silver = AssetKey("ecommerce_silver")
        gold = AssetKey("ecommerce_gold")

        self.assertEqual(graph.get(silver).parent_keys, {bronze})
        self.assertEqual(graph.get(gold).parent_keys, {silver})
        self.assertEqual(graph.get(bronze).parent_keys, set())

    def test_medallion_job_selects_three_assets_with_max_concurrent_runs_one(self):
        # Lock parity with former run_daily.lock: at most one full-job run.
        job = self.defs.resolve_job_def("ecommerce_medallion_job")
        selected = {
            key.to_user_string() for key in job.asset_layer.executable_asset_keys
        }
        self.assertEqual(
            selected,
            {"ecommerce_bronze", "ecommerce_silver", "ecommerce_gold"},
        )
        self.assertEqual(job.metadata["max_concurrent_runs"].value, 1)

    def test_daily_schedule_cron_and_timezone(self):
        schedule = self.defs.resolve_schedule_def("ecommerce_medallion_daily")
        self.assertEqual(schedule.cron_schedule, "0 6 * * *")
        self.assertEqual(schedule.execution_timezone, "America/Sao_Paulo")
        self.assertEqual(schedule.job_name, "ecommerce_medallion_job")

    def test_silver_and_gold_are_independently_targetable(self):
        # Replaces former -SkipExtract: selective layer materialization.
        graph = self.defs.resolve_asset_graph()
        silver = AssetKey("ecommerce_silver")
        gold = AssetKey("ecommerce_gold")
        self.assertIn(silver, graph.materializable_asset_keys)
        self.assertIn(gold, graph.materializable_asset_keys)
        silver_only = AssetSelection.assets(silver).resolve(graph)
        gold_only = AssetSelection.assets(gold).resolve(graph)
        self.assertEqual(silver_only, {silver})
        self.assertEqual(gold_only, {gold})

    def test_bronze_failure_short_circuits_silver_and_gold(self):
        # Parity with run_daily: bronze failure must not run dbt layers.
        from orchestration.dagster.ecommerce_analytics.assets.bronze import (
            ecommerce_bronze,
        )
        from orchestration.dagster.ecommerce_analytics.assets.gold import ecommerce_gold
        from orchestration.dagster.ecommerce_analytics.assets.silver import (
            ecommerce_silver,
        )

        fake = sys.modules["ecommerce_bronze_pipeline"]
        fake.load_ecommerce_bronze = MagicMock(
            side_effect=RuntimeError("bronze extraction failed")
        )

        with patch(
            "orchestration.dagster.ecommerce_analytics.assets.silver.run_dbt_build"
        ) as mock_silver, patch(
            "orchestration.dagster.ecommerce_analytics.assets.gold.run_dbt_build"
        ) as mock_gold:
            result = materialize(
                [ecommerce_bronze, ecommerce_silver, ecommerce_gold],
                raise_on_error=False,
            )

        self.assertFalse(result.success)
        mock_silver.assert_not_called()
        mock_gold.assert_not_called()

    def test_silver_failure_short_circuits_gold(self):
        from orchestration.dagster.ecommerce_analytics.assets.bronze import (
            ecommerce_bronze,
        )
        from orchestration.dagster.ecommerce_analytics.assets.gold import ecommerce_gold
        from orchestration.dagster.ecommerce_analytics.assets.silver import (
            ecommerce_silver,
        )

        fake = sys.modules["ecommerce_bronze_pipeline"]
        fake.load_ecommerce_bronze = MagicMock()

        with patch(
            "orchestration.dagster.ecommerce_analytics.assets.silver.run_dbt_build",
            side_effect=RuntimeError("dbt silver failed"),
        ), patch(
            "orchestration.dagster.ecommerce_analytics.assets.gold.run_dbt_build"
        ) as mock_gold:
            result = materialize(
                [ecommerce_bronze, ecommerce_silver, ecommerce_gold],
                raise_on_error=False,
            )

        self.assertFalse(result.success)
        mock_gold.assert_not_called()


if __name__ == "__main__":
    unittest.main()
