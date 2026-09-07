import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")
MODEL_ID = "model.snowflake_analytics.stg_users"


class StgUsersTest(unittest.TestCase):
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

    def test_model_parses_as_silver_view_from_users_source(self):
        self.assertEqual(
            self.parse_result.returncode,
            0,
            msg=f"{self.parse_result.stdout}\n{self.parse_result.stderr}",
        )
        model = self.manifest["nodes"][MODEL_ID]
        self.assertEqual(model["config"]["materialized"], "view")
        self.assertEqual(
            model["depends_on"]["nodes"],
            ["source.snowflake_analytics.ecommerce.users"],
        )

    def test_user_id_is_unique_and_not_null(self):
        tests = {
            node["test_metadata"]["name"]
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and MODEL_ID in node["depends_on"]["nodes"]
            and node["column_name"] == "user_id"
        }
        self.assertEqual(tests, {"not_null", "unique"})

    def test_timestamps_are_normalized_to_utc(self):
        raw_code = self.manifest["nodes"][MODEL_ID]["raw_code"].lower()
        for source_name in ("created_at", "updated_at", "deleted_at"):
            self.assertIn(
                f"convert_timezone('utc', {source_name}) as {source_name}_utc",
                raw_code,
            )

    def test_password_hash_is_absent_from_the_model(self):
        raw_code = self.manifest["nodes"][MODEL_ID]["raw_code"].lower()
        self.assertNotIn("password_hash", raw_code)


if __name__ == "__main__":
    unittest.main()
