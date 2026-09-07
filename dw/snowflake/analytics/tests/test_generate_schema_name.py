import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DBT_EXECUTABLE = Path(sys.executable).with_name("dbt.exe")


class GenerateSchemaNameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.project_dir = Path(cls.temp_dir.name) / "project"
        cls.profiles_dir = Path(cls.temp_dir.name) / "profiles"
        cls.project_dir.mkdir()
        cls.profiles_dir.mkdir()

        (cls.project_dir / "dbt_project.yml").write_text(
            """
name: snowflake_analytics
version: "1.0.0"
config-version: 2
profile: snowflake_analytics
model-paths: ["models"]
macro-paths: ["macros"]
models:
  snowflake_analytics:
    silver:
      +schema: SILVER
    gold:
      +schema: GOLD
""".lstrip(),
            encoding="utf-8",
        )
        macro_dir = cls.project_dir / "macros"
        macro_dir.mkdir()
        shutil.copy2(
            PROJECT_DIR / "macros" / "generate_schema_name.sql",
            macro_dir,
        )

        for layer in ("silver", "gold"):
            model_dir = cls.project_dir / "models" / layer
            model_dir.mkdir(parents=True)
            (model_dir / f"{layer}_model.sql").write_text(
                "select 1 as id\n",
                encoding="utf-8",
            )

        base_model_dir = cls.project_dir / "models" / "base"
        base_model_dir.mkdir()
        (base_model_dir / "base_model.sql").write_text(
            "select 1 as id\n",
            encoding="utf-8",
        )

        (cls.profiles_dir / "profiles.yml").write_text(
            """
snowflake_analytics:
  target: prod
  outputs:
    prod:
      type: snowflake
      account: test_account
      user: test_user
      password: test_password
      role: test_role
      database: DATA_LAB
      warehouse: test_warehouse
      schema: DEFAULT_SCHEMA
      threads: 1
    dev:
      type: snowflake
      account: test_account
      user: test_user
      password: test_password
      role: test_role
      database: DATA_LAB
      warehouse: test_warehouse
      schema: DEV_SCHEMA
      threads: 1
""".lstrip(),
            encoding="utf-8",
        )

        cls.parse_results = {}
        cls.manifests = {}
        for target in ("prod", "dev"):
            target_path = Path(cls.temp_dir.name) / f"target-{target}"
            result = subprocess.run(
                [
                    str(DBT_EXECUTABLE),
                    "parse",
                    "--project-dir",
                    str(cls.project_dir),
                    "--profiles-dir",
                    str(cls.profiles_dir),
                    "--target",
                    target,
                    "--target-path",
                    str(target_path),
                    "--warn-error",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            cls.parse_results[target] = result
            if result.returncode == 0:
                cls.manifests[target] = json.loads(
                    (target_path / "manifest.json").read_text(encoding="utf-8")
                )

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def schema_for(self, target, model_name):
        nodes = self.manifests[target]["nodes"]
        return nodes[f"model.snowflake_analytics.{model_name}"]["schema"]

    def test_prod_uses_layer_schemas(self):
        self.assertEqual(self.schema_for("prod", "silver_model"), "SILVER")
        self.assertEqual(self.schema_for("prod", "gold_model"), "GOLD")

    def test_non_prod_uses_default_target_schema(self):
        self.assertEqual(self.schema_for("dev", "silver_model"), "DEV_SCHEMA")
        self.assertEqual(self.schema_for("dev", "gold_model"), "DEV_SCHEMA")

    def test_schema_is_never_null(self):
        self.assertEqual(self.schema_for("prod", "base_model"), "DEFAULT_SCHEMA")
        self.assertEqual(self.schema_for("dev", "base_model"), "DEV_SCHEMA")

    def test_parse_passes_with_warning_errors_configured(self):
        for target, result in self.parse_results.items():
            self.assertEqual(
                result.returncode,
                0,
                msg=f"{target} parse failed:\n{result.stdout}\n{result.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
