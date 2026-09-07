import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")
MODEL_ID = "model.snowflake_analytics.stg_order_status_history"


class StgOrderStatusHistoryTest(unittest.TestCase):
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

    def test_model_preserves_history_and_normalizes_changed_at(self):
        self.assertEqual(
            self.parse_result.returncode,
            0,
            msg=f"{self.parse_result.stdout}\n{self.parse_result.stderr}",
        )
        model = self.manifest["nodes"][MODEL_ID]
        self.assertEqual(model["config"]["materialized"], "view")
        self.assertEqual(
            model["depends_on"]["nodes"],
            ["source.snowflake_analytics.ecommerce.order_status_history"],
        )
        self.assertIn(
            "convert_timezone('utc', changed_at) as changed_at_utc",
            model["raw_code"].lower(),
        )

    def test_history_id_is_unique_and_not_null(self):
        tests = {
            node["test_metadata"]["name"]
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node.get("attached_node") == MODEL_ID
            and node["column_name"] == "history_id"
        }
        self.assertEqual(tests, {"not_null", "unique"})

    def test_order_relationship_and_status_domain_are_enforced(self):
        tests = [
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node.get("attached_node") == MODEL_ID
        ]
        relationship = next(
            node
            for node in tests
            if node["column_name"] == "order_id"
            and node["test_metadata"]["name"] == "relationships"
        )
        self.assertIn(
            "model.snowflake_analytics.stg_orders",
            relationship["depends_on"]["nodes"],
        )
        self.assertIn(
            "not_null",
            {
                node["test_metadata"]["name"]
                for node in tests
                if node["column_name"] == "order_id"
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


if __name__ == "__main__":
    unittest.main()
