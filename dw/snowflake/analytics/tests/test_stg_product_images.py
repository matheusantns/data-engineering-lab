import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")
MODEL_ID = "model.snowflake_analytics.stg_product_images"
GRAIN_TEST_PATH = "tests/assert_stg_product_images_product_sort_unique.sql"


class StgProductImagesTest(unittest.TestCase):
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

    def test_model_parses_as_silver_view_from_images_source(self):
        self.assertEqual(
            self.parse_result.returncode,
            0,
            msg=f"{self.parse_result.stdout}\n{self.parse_result.stderr}",
        )
        model = self.manifest["nodes"][MODEL_ID]
        self.assertEqual(model["config"]["materialized"], "view")
        self.assertEqual(
            model["depends_on"]["nodes"],
            ["source.snowflake_analytics.ecommerce.product_images"],
        )

    def test_image_id_is_unique_and_not_null(self):
        tests = {
            node["test_metadata"]["name"]
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node.get("attached_node") == MODEL_ID
            and node["column_name"] == "image_id"
        }
        self.assertEqual(tests, {"not_null", "unique"})

    def test_product_id_references_products(self):
        relationship_tests = [
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node.get("test_metadata", {}).get("name") == "relationships"
            and node.get("attached_node") == MODEL_ID
            and node["column_name"] == "product_id"
        ]
        self.assertEqual(len(relationship_tests), 1)
        self.assertIn(
            "model.snowflake_analytics.stg_products",
            relationship_tests[0]["depends_on"]["nodes"],
        )

    def test_product_sort_order_is_unique_and_timestamp_uses_utc(self):
        grain_tests = [
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and Path(node["original_file_path"]).as_posix() == GRAIN_TEST_PATH
        ]
        self.assertEqual(len(grain_tests), 1)
        self.assertIn(MODEL_ID, grain_tests[0]["depends_on"]["nodes"])
        grain_sql = grain_tests[0]["raw_code"].lower()
        self.assertIn("group by product_id, sort_order", grain_sql)
        self.assertIn("having count(*) > 1", grain_sql)

        raw_code = self.manifest["nodes"][MODEL_ID]["raw_code"].lower()
        self.assertIn(
            "convert_timezone('utc', created_at) as created_at_utc",
            raw_code,
        )


if __name__ == "__main__":
    unittest.main()
