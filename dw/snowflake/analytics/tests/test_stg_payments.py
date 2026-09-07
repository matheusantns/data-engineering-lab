import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")
MODEL_ID = "model.snowflake_analytics.stg_payments"


class StgPaymentsTest(unittest.TestCase):
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

    def test_model_preserves_payment_contract_and_utc_timestamp(self):
        self.assertEqual(
            self.parse_result.returncode,
            0,
            msg=f"{self.parse_result.stdout}\n{self.parse_result.stderr}",
        )
        model = self.manifest["nodes"][MODEL_ID]
        self.assertEqual(model["config"]["materialized"], "view")
        self.assertEqual(
            model["depends_on"]["nodes"],
            ["source.snowflake_analytics.ecommerce.payments"],
        )
        self.assertIn(
            "convert_timezone('utc', created_at) as created_at_utc",
            model["raw_code"].lower(),
        )

    def test_payment_id_and_order_relationship_are_enforced(self):
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
                if node["column_name"] == "payment_id"
            },
            {"not_null", "unique"},
        )
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

    def test_closed_domains_and_required_currency_are_enforced(self):
        tests = [
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node.get("attached_node") == MODEL_ID
        ]
        accepted = {
            node["column_name"]: node["test_metadata"]["kwargs"]["values"]
            for node in tests
            if node["test_metadata"]["name"] == "accepted_values"
        }
        self.assertEqual(
            accepted,
            {
                "provider": ["card", "paypal", "bank_transfer"],
                "status": [
                    "pending",
                    "authorized",
                    "captured",
                    "failed",
                    "refunded",
                ],
            },
        )
        self.assertIn(
            "not_null",
            {
                node["test_metadata"]["name"]
                for node in tests
                if node["column_name"] == "currency"
            },
        )

    def test_amount_is_nonnegative(self):
        amount_test = next(
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node["name"] == "assert_stg_payments_amount_nonnegative"
        )
        self.assertIn("where amount < 0", amount_test["raw_code"].lower())


if __name__ == "__main__":
    unittest.main()
