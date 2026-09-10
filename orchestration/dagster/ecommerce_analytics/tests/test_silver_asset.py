import sys
import unittest
from types import ModuleType
from unittest.mock import MagicMock, patch

from dagster import AssetKey, materialize


class SilverAssetTest(unittest.TestCase):
    def test_ecommerce_silver_depends_on_bronze_and_runs_dbt_silver_select(self):
        fake_pipeline = ModuleType("ecommerce_bronze_pipeline")
        fake_pipeline.load_ecommerce_bronze = MagicMock()
        sys.modules["ecommerce_bronze_pipeline"] = fake_pipeline

        from orchestration.dagster.ecommerce_analytics.assets.bronze import (
            ecommerce_bronze,
        )
        from orchestration.dagster.ecommerce_analytics.assets.silver import (
            ecommerce_silver,
        )

        self.assertEqual(ecommerce_silver.key.to_user_string(), "ecommerce_silver")
        self.assertIn(AssetKey("ecommerce_bronze"), ecommerce_silver.dependency_keys)

        with patch(
            "orchestration.dagster.ecommerce_analytics.assets.silver.run_dbt_build"
        ) as mock_run:
            result = materialize([ecommerce_bronze, ecommerce_silver])

        self.assertTrue(result.success)
        mock_run.assert_called_once_with("path:models/silver")


if __name__ == "__main__":
    unittest.main()
