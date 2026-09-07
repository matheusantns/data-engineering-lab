import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")
MODEL_ID = "model.snowflake_analytics.stg_products"


class StgProductsTest(unittest.TestCase):
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

    def test_model_parses_as_silver_view_from_products_source(self):
        self.assertEqual(
            self.parse_result.returncode,
            0,
            msg=f"{self.parse_result.stdout}\n{self.parse_result.stderr}",
        )
        model = self.manifest["nodes"][MODEL_ID]
        self.assertEqual(model["config"]["materialized"], "view")
        self.assertEqual(
            model["depends_on"]["nodes"],
            ["source.snowflake_analytics.ecommerce.products"],
        )

    def test_product_id_and_slug_are_unique_and_not_null(self):
        tests_by_column = {
            column: {
                node["test_metadata"]["name"]
                for node in self.manifest["nodes"].values()
                if node["resource_type"] == "test"
                and node.get("attached_node") == MODEL_ID
                and node["column_name"] == column
            }
            for column in ("product_id", "slug")
        }
        self.assertEqual(
            tests_by_column,
            {
                "product_id": {"not_null", "unique"},
                "slug": {"not_null", "unique"},
            },
        )

    def test_category_id_references_categories(self):
        relationship_tests = [
            node
            for node in self.manifest["nodes"].values()
            if node["resource_type"] == "test"
            and node["test_metadata"]["name"] == "relationships"
            and node.get("attached_node") == MODEL_ID
            and node["column_name"] == "category_id"
        ]
        self.assertEqual(len(relationship_tests), 1)
        self.assertIn(
            "model.snowflake_analytics.stg_categories",
            relationship_tests[0]["depends_on"]["nodes"],
        )
        self.assertEqual(
            relationship_tests[0]["test_metadata"]["kwargs"]["field"],
            "category_id",
        )

    def test_attributes_are_preserved_and_timestamps_use_utc(self):
        raw_code = self.manifest["nodes"][MODEL_ID]["raw_code"].lower()
        self.assertIn("\n    attributes,", raw_code)
        self.assertNotIn("cast(attributes", raw_code)
        for source_name in ("created_at", "updated_at", "deleted_at"):
            self.assertIn(
                f"convert_timezone('utc', {source_name}) as {source_name}_utc",
                raw_code,
            )


if __name__ == "__main__":
    unittest.main()
