import sys
import unittest
from types import ModuleType
from unittest.mock import MagicMock, patch

from dagster import AssetKey, materialize


class GoldAssetTest(unittest.TestCase):
    def test_ecommerce_gold_depends_on_silver_and_runs_dbt_gold_select(self):
        fake_pipeline = ModuleType("ecommerce_bronze_pipeline")
        fake_pipeline.load_ecommerce_bronze = MagicMock()
        sys.modules["ecommerce_bronze_pipeline"] = fake_pipeline

        from orchestration.dagster.ecommerce_analytics.assets.bronze import (
            ecommerce_bronze,
        )
        from orchestration.dagster.ecommerce_analytics.assets.gold import ecommerce_gold
        from orchestration.dagster.ecommerce_analytics.assets.silver import (
            ecommerce_silver,
        )

        self.assertEqual(ecommerce_gold.key.to_user_string(), "ecommerce_gold")
        self.assertIn(AssetKey("ecommerce_silver"), ecommerce_gold.dependency_keys)

        with patch(
            "orchestration.dagster.ecommerce_analytics.assets.silver.run_dbt_build"
        ), patch(
            "orchestration.dagster.ecommerce_analytics.assets.gold.run_dbt_build"
        ) as mock_run:
            result = materialize([ecommerce_bronze, ecommerce_silver, ecommerce_gold])

        self.assertTrue(result.success)
        mock_run.assert_called_once_with("path:models/gold")


if __name__ == "__main__":
    unittest.main()
