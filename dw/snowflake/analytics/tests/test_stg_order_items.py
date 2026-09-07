import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")
MODEL_ID = "model.snowflake_analytics.stg_order_items"


class StgOrderItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        profiles_dir = Path(cls.temp_dir.name) / "profiles"
        target_dir = Path(cls.temp_dir.name) / "target"
        profiles_dir.mkdir()
        (profiles_dir / "profiles.yml").write_text(
            """
snowflake_analytics:
  target: test
  outputs:
    test:
      type: snowflake
      account: test_account
      user: test_user
      password: test_password
      role: test_role
      database: DATA_LAB
      warehouse: test_warehouse
      schema: TEST_SCHEMA
      threads: 1
""".lstrip(),
            encoding="utf-8",
        )
        cls.parse_result = subprocess.run(
            [
                str(DBT_EXECUTABLE),
                "parse",
                "--project-dir",
                str(PROJECT_DIR),
                "--profiles-dir",
                str(profiles_dir),
                "--target-path",
                str(target_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        manifest_path = target_dir / "manifest.json"
        cls.manifest = (
            json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest_path.exists()
            else {}
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_model_is_source_conformed_silver_view(self):
        self.assertEqual(
            self.parse_result.returncode,
            0,
            msg=f"{self.parse_result.stdout}\n{self.parse_result.stderr}",
        )
        model = self.manifest["nodes"][MODEL_ID]
        self.assertEqual(model["config"]["materialized"], "view")
        self.assertEqual(
            model["depends_on"]["nodes"],
            ["source.snowflake_analytics.ecommerce.order_items"],
        )

    def test_order_and_variant_foreign_keys_are_required_and_valid(self):
        for column, parent_model in (
            ("order_id", "model.snowflake_analytics.stg_orders"),
            ("variant_id", "model.snowflake_analytics.stg_product_variants"),
        ):
            tests = [
                node
                for node in self.manifest["nodes"].values()
                if node["resource_type"] == "test"
                and node.get("attached_node") == MODEL_ID
                and node["column_name"] == column
            ]
            self.assertEqual(
                {node["test_metadata"]["name"] for node in tests},
                {"not_null", "relationships"},
            )
            relationship = next(
                node
                for node in tests
                if node["test_metadata"]["name"] == "relationships"
            )
            self.assertIn(parent_model, relationship["depends_on"]["nodes"])

    def test_grain_and_numeric_limits_match_source_contract(self):
        model_tests = [
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and MODEL_ID in node["depends_on"]["nodes"]
        ]
        grain_test = next(
            node
            for node in model_tests
            if node["name"] == "assert_stg_order_items_grain"
        )
        self.assertIn(
            "group by order_id, variant_id",
            grain_test["raw_code"].lower(),
        )
        self.assertIn("having count(*) > 1", grain_test["raw_code"].lower())

        limits_test = next(
            node
            for node in model_tests
            if node["name"] == "assert_stg_order_items_limits"
        )
        limits_sql = limits_test["raw_code"].lower()
        for expression in (
            "qty <= 0",
            "unit_price < 0",
            "discount < 0",
            "discount > 1",
            "line_total < 0",
        ):
            self.assertIn(expression, limits_sql)


if __name__ == "__main__":
    unittest.main()
