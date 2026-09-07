import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")
EXPECTED_TABLES = {
    "users",
    "addresses",
    "categories",
    "products",
    "product_variants",
    "product_images",
    "inventory",
    "carriers",
    "carts",
    "cart_items",
    "orders",
    "order_items",
    "order_status_history",
    "payments",
    "shipments",
    "inventory_movements",
}


class EcommerceSourcesTest(unittest.TestCase):
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

        common_args = [
            "--project-dir",
            str(PROJECT_DIR),
            "--profiles-dir",
            str(cls.profiles_dir),
            "--target-path",
            str(cls.target_dir),
        ]
        cls.parse_result = subprocess.run(
            [str(DBT_EXECUTABLE), "parse", *common_args],
            capture_output=True,
            text=True,
            check=False,
        )
        cls.ls_result = subprocess.run(
            [
                str(DBT_EXECUTABLE),
                "ls",
                *common_args,
                "--resource-type",
                "source",
                "--output",
                "json",
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

    def test_all_pipeline_tables_are_declared_once(self):
        self.assertEqual(
            self.ls_result.returncode,
            0,
            msg=f"{self.ls_result.stdout}\n{self.ls_result.stderr}",
        )
        listed_sources = [
            json.loads(line)
            for line in self.ls_result.stdout.splitlines()
            if line.startswith("{")
        ]
        self.assertEqual(len(listed_sources), 16)
        self.assertEqual({source["name"] for source in listed_sources}, EXPECTED_TABLES)

    def test_sources_resolve_to_bronze(self):
        sources = self.manifest["sources"].values()
        self.assertEqual({source["database"] for source in sources}, {"DATA_LAB"})
        self.assertEqual({source["schema"] for source in sources}, {"BRONZE"})

    def test_each_source_has_a_description_and_availability_test(self):
        sources = self.manifest["sources"]
        tests = self.manifest["nodes"].values()
        tested_source_ids = {
            dependency
            for test in tests
            if test["resource_type"] == "test"
            for dependency in test["depends_on"]["nodes"]
            if dependency.startswith("source.")
        }

        self.assertTrue(all(source["description"] for source in sources.values()))
        self.assertEqual(tested_source_ids, set(sources))

    def test_parse_passes_with_warnings_as_errors(self):
        self.assertEqual(
            self.parse_result.returncode,
            0,
            msg=f"{self.parse_result.stdout}\n{self.parse_result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
