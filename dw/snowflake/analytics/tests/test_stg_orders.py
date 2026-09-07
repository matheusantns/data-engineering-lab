import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")
MODEL_ID = "model.snowflake_analytics.stg_orders"


class StgOrdersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        profiles_dir = Path(cls.temp_dir.name) / "profiles"
        cls.target_dir = Path(cls.temp_dir.name) / "target"
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
                str(cls.target_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        manifest_path = cls.target_dir / "manifest.json"
        cls.manifest = (
            json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest_path.exists()
            else {}
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_model_preserves_order_contract_and_utc_timestamps(self):
        self.assertEqual(
            self.parse_result.returncode,
            0,
            msg=f"{self.parse_result.stdout}\n{self.parse_result.stderr}",
        )
        model = self.manifest["nodes"][MODEL_ID]
        self.assertEqual(model["config"]["materialized"], "view")
        self.assertEqual(
            model["depends_on"]["nodes"],
            ["source.snowflake_analytics.ecommerce.orders"],
        )
        raw_code = model["raw_code"].lower()
        for source_name in ("ordered_at", "created_at", "updated_at"):
            self.assertIn(
                f"convert_timezone('utc', {source_name}) as {source_name}_utc",
                raw_code,
            )

    def test_order_id_and_number_are_unique_and_not_null(self):
        tests_by_column = {
            column: {
                node["test_metadata"]["name"]
                for node in self.manifest["nodes"].values()
                if node["resource_type"] == "test"
                and node.get("attached_node") == MODEL_ID
                and node["column_name"] == column
            }
            for column in ("order_id", "order_number")
        }
        self.assertEqual(
            tests_by_column,
            {
                "order_id": {"not_null", "unique"},
                "order_number": {"not_null", "unique"},
            },
        )

    def test_user_and_status_domains_are_enforced(self):
        tests = [
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node.get("attached_node") == MODEL_ID
        ]
        user_relationship = next(
            node
            for node in tests
            if node["column_name"] == "user_id"
            and node["test_metadata"]["name"] == "relationships"
        )
        self.assertIn(
            "model.snowflake_analytics.stg_users",
            user_relationship["depends_on"]["nodes"],
        )
        self.assertIn(
            "not_null",
            {
                node["test_metadata"]["name"]
                for node in tests
                if node["column_name"] == "user_id"
            },
        )
        status_test = next(
            node
            for node in tests
            if node["column_name"] == "status"
            and node["test_metadata"]["name"] == "accepted_values"
        )
        self.assertEqual(
            status_test["test_metadata"]["kwargs"]["values"],
            ["pending", "paid", "processing", "shipped", "delivered", "cancelled"],
        )

    def test_financial_values_are_nonnegative(self):
        test = next(
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node["name"] == "assert_stg_orders_values_nonnegative"
        )
        raw_code = test["raw_code"].lower()
        for column in (
            "subtotal",
            "discount_total",
            "shipping_total",
            "grand_total",
        ):
            self.assertIn(f"{column} < 0", raw_code)


if __name__ == "__main__":
    unittest.main()
