import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")
MODEL_ID = "model.snowflake_analytics.stg_cart_items"


class StgCartItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.profiles_dir = Path(cls.temp_dir.name) / "profiles"
        cls.target_dir = Path(cls.temp_dir.name) / "target"
        cls.profiles_dir.mkdir()
        (cls.profiles_dir / "profiles.yml").write_text(
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
                str(cls.profiles_dir),
                "--target-path",
                str(cls.target_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        cls.manifest = {}
        manifest_path = cls.target_dir / "manifest.json"
        if manifest_path.exists():
            cls.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_model_preserves_source_columns_and_normalizes_timestamps(self):
        self.assertEqual(
            self.parse_result.returncode,
            0,
            msg=f"{self.parse_result.stdout}\n{self.parse_result.stderr}",
        )
        model = self.manifest["nodes"][MODEL_ID]
        self.assertEqual(model["config"]["materialized"], "view")
        self.assertEqual(
            model["depends_on"]["nodes"],
            ["source.snowflake_analytics.ecommerce.cart_items"],
        )
        raw_code = model["raw_code"].lower()
        for source_name in ("created_at", "updated_at"):
            self.assertIn(
                f"convert_timezone('utc', {source_name}) as {source_name}_utc",
                raw_code,
            )

    def test_cart_and_variant_foreign_keys_are_required_and_valid(self):
        for column, parent_model in (
            ("cart_id", "model.snowflake_analytics.stg_carts"),
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

    def test_grain_is_unique_and_quantity_is_positive(self):
        model_tests = [
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and MODEL_ID in node["depends_on"]["nodes"]
        ]
        grain_test = next(
            node
            for node in model_tests
            if node["name"] == "assert_stg_cart_items_grain"
        )
        self.assertIn(
            "group by cart_id, variant_id",
            grain_test["raw_code"].lower(),
        )
        self.assertIn("having count(*) > 1", grain_test["raw_code"].lower())

        quantity_test = next(
            node
            for node in model_tests
            if node["name"] == "assert_stg_cart_items_qty_positive"
        )
        self.assertIn("where qty <= 0", quantity_test["raw_code"].lower())


if __name__ == "__main__":
    unittest.main()
