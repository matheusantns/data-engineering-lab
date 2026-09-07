import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")
MODEL_ID = "model.snowflake_analytics.stg_inventory_movements"


class StgInventoryMovementsTest(unittest.TestCase):
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

    def test_model_preserves_ledger_and_normalizes_created_at(self):
        self.assertEqual(
            self.parse_result.returncode,
            0,
            msg=f"{self.parse_result.stdout}\n{self.parse_result.stderr}",
        )
        model = self.manifest["nodes"][MODEL_ID]
        self.assertEqual(model["config"]["materialized"], "view")
        self.assertEqual(
            model["depends_on"]["nodes"],
            ["source.snowflake_analytics.ecommerce.inventory_movements"],
        )
        self.assertIn(
            "convert_timezone('utc', created_at) as created_at_utc",
            model["raw_code"].lower(),
        )

    def test_primary_key_and_relationships_match_source_nullability(self):
        tests = [
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node.get("attached_node") == MODEL_ID
        ]
        self.assertEqual(
            {
                node["test_metadata"]["name"]
                for node in tests
                if node["column_name"] == "movement_id"
            },
            {"not_null", "unique"},
        )
        for column, parent_model, required in (
            ("variant_id", "model.snowflake_analytics.stg_product_variants", True),
            ("order_id", "model.snowflake_analytics.stg_orders", False),
        ):
            column_tests = [
                node for node in tests if node["column_name"] == column
            ]
            relationship = next(
                node
                for node in column_tests
                if node["test_metadata"]["name"] == "relationships"
            )
            self.assertIn(parent_model, relationship["depends_on"]["nodes"])
            self.assertEqual(
                "not_null"
                in {node["test_metadata"]["name"] for node in column_tests},
                required,
            )

    def test_reason_domain_and_nonzero_delta_are_enforced(self):
        reason_test = next(
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node.get("attached_node") == MODEL_ID
            and node["column_name"] == "reason"
            and node["test_metadata"]["name"] == "accepted_values"
        )
        self.assertEqual(
            reason_test["test_metadata"]["kwargs"]["values"],
            ["restock", "sale", "return", "adjustment"],
        )
        delta_test = next(
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node["name"] == "assert_stg_inventory_movements_delta_nonzero"
        )
        self.assertIn(
            "where quantity_delta = 0",
            delta_test["raw_code"].lower(),
        )

    def test_project_contains_all_sixteen_silver_views(self):
        silver_views = [
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "model"
            and node["original_file_path"].replace("\\", "/").startswith(
                "models/silver/"
            )
            and node["config"]["materialized"] == "view"
        ]
        self.assertEqual(len(silver_views), 16)


if __name__ == "__main__":
    unittest.main()
