import sys
import unittest
from types import ModuleType
from unittest.mock import MagicMock

from dagster import materialize


class BronzeAssetTest(unittest.TestCase):
    def test_ecommerce_bronze_calls_load_ecommerce_bronze(self):
        fake_pipeline = ModuleType("ecommerce_bronze_pipeline")
        fake_pipeline.load_ecommerce_bronze = MagicMock()
        sys.modules["ecommerce_bronze_pipeline"] = fake_pipeline

        from orchestration.dagster.ecommerce_analytics.assets.bronze import (
            ecommerce_bronze,
        )

        result = materialize([ecommerce_bronze])

        self.assertTrue(result.success)
        self.assertEqual(ecommerce_bronze.key.to_user_string(), "ecommerce_bronze")
        fake_pipeline.load_ecommerce_bronze.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
