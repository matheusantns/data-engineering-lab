import sys
import unittest
from types import ModuleType
from unittest.mock import MagicMock

from dagster import AssetKey, AssetSelection


class DefinitionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fake_pipeline = ModuleType("ecommerce_bronze_pipeline")
        fake_pipeline.load_ecommerce_bronze = MagicMock()
        sys.modules["ecommerce_bronze_pipeline"] = fake_pipeline

        from orchestration.dagster.ecommerce_analytics.definitions import defs

        cls.defs = defs

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
        graph = self.defs.resolve_asset_graph()
        silver = AssetKey("ecommerce_silver")
        gold = AssetKey("ecommerce_gold")
        self.assertIn(silver, graph.materializable_asset_keys)
        self.assertIn(gold, graph.materializable_asset_keys)
        silver_only = AssetSelection.assets(silver).resolve(graph)
        gold_only = AssetSelection.assets(gold).resolve(graph)
        self.assertEqual(silver_only, {silver})
        self.assertEqual(gold_only, {gold})


if __name__ == "__main__":
    unittest.main()
