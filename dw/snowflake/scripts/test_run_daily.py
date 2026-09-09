import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE_RUNNER = Path(__file__).with_name("run_daily.ps1")
SOURCE_DBT_PROJECT = SOURCE_RUNNER.parents[1] / "analytics" / "dbt_project.yml"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


class RunDailyIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.scripts_dir = self.root / "dw" / "snowflake" / "scripts"
        self.analytics_dir = self.root / "dw" / "snowflake" / "analytics"
        self.pipeline_dir = self.root / "pipelines" / "ecommerce_bronze"
        self.bin_dir = self.root / "bin"
        self.events_path = self.root / "events.log"
        self.bronze_arguments_path = self.root / "bronze_arguments.log"
        self.dbt_arguments_path = self.root / "dbt_arguments.log"

        self.scripts_dir.mkdir(parents=True)
        self.analytics_dir.mkdir(parents=True)
        self.pipeline_dir.mkdir(parents=True)
        self.bin_dir.mkdir(parents=True)
        shutil.copy2(SOURCE_RUNNER, self.scripts_dir / "run_daily.ps1")
        (self.pipeline_dir / "ecommerce_bronze_pipeline.py").write_text(
            "# Invoked through the test's python command stub.\n",
            encoding="utf-8",
        )
        self._write_stub(
            "python.cmd",
            "bronze",
            "BRONZE_EXIT_CODE",
            "BRONZE_ARGUMENTS",
        )
        self._write_stub("dbt.cmd", "dbt", "DBT_EXIT_CODE", "DBT_ARGUMENTS")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_stub(self, name, event, exit_variable, arguments_variable):
        (self.bin_dir / name).write_text(
            "\n".join(
                [
                    "@echo off",
                    f'echo {event}>>"%RUNNER_EVENTS%"',
                    f'echo %*>"%{arguments_variable}%"',
                    f"echo {event}-output",
                    f"exit /b %{exit_variable}%",
                ]
            ),
            encoding="utf-8",
        )

    def _run(self, *arguments, bronze_exit=0, dbt_exit=0):
        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{self.bin_dir}{os.pathsep}{env['PATH']}",
                "RUNNER_EVENTS": str(self.events_path),
                "BRONZE_EXIT_CODE": str(bronze_exit),
                "DBT_EXIT_CODE": str(dbt_exit),
                "BRONZE_ARGUMENTS": str(self.bronze_arguments_path),
                "DBT_ARGUMENTS": str(self.dbt_arguments_path),
            }
        )
        return subprocess.run(
            [
                POWERSHELL,
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(self.scripts_dir / "run_daily.ps1"),
                *arguments,
            ],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def _events(self):
        if not self.events_path.exists():
            return []
        return self.events_path.read_text(encoding="utf-8").splitlines()

    def _run_logs(self):
        return list((self.analytics_dir / "logs").glob("run_daily_*.log"))

    def test_happy_path_runs_bronze_before_dbt_and_records_steps(self):
        result = self._run()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._events(), ["bronze", "dbt"])
        self.assertEqual(
            self.bronze_arguments_path.read_text(encoding="utf-8").strip(),
            str(self.pipeline_dir / "ecommerce_bronze_pipeline.py"),
        )
        dbt_arguments = self.dbt_arguments_path.read_text(encoding="utf-8").strip()
        self.assertIn("build", dbt_arguments)
        self.assertIn(f"--project-dir {self.analytics_dir}", dbt_arguments)
        self.assertIn(f"--profiles-dir {self.analytics_dir}", dbt_arguments)
        self.assertNotIn("--warn-error", dbt_arguments)
        dbt_project = SOURCE_DBT_PROJECT.read_text(encoding="utf-8")
        self.assertIn("warn_error_options:", dbt_project)
        self.assertIn("error: all", dbt_project)
        logs = self._run_logs()
        self.assertEqual(len(logs), 1)
        log = logs[0].read_text(encoding="utf-8")
        self.assertIn("Starting Bronze extraction", log)
        self.assertIn("Starting dbt build", log)
        self.assertIn("Daily pipeline completed successfully", log)

    def test_bronze_failure_prevents_dbt_and_returns_nonzero(self):
        result = self._run(bronze_exit=17)

        self.assertEqual(result.returncode, 17)
        self.assertEqual(self._events(), ["bronze"])
        self.assertIn("Bronze extraction failed with exit code 17", result.stdout)

    def test_dbt_failure_returns_its_nonzero_exit_code(self):
        result = self._run(dbt_exit=23)

        self.assertEqual(result.returncode, 23)
        self.assertEqual(self._events(), ["bronze", "dbt"])
        self.assertIn("dbt build failed with exit code 23", result.stdout)

    def test_existing_lock_refuses_a_second_execution(self):
        lock_path = self.scripts_dir / "run_daily.lock"
        lock_path.write_text("existing run", encoding="utf-8")

        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self._events(), [])
        self.assertEqual(lock_path.read_text(encoding="utf-8"), "existing run")
        self.assertIn("already in progress", result.stdout)

    def test_lock_is_removed_after_success(self):
        result = self._run()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.scripts_dir / "run_daily.lock").exists())

    def test_lock_is_removed_after_failure(self):
        result = self._run(bronze_exit=9)

        self.assertEqual(result.returncode, 9)
        self.assertFalse((self.scripts_dir / "run_daily.lock").exists())

    def test_skip_extract_runs_only_dbt(self):
        result = self._run("-SkipExtract")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._events(), ["dbt"])
        self.assertIn("Bronze extraction skipped", result.stdout)


if __name__ == "__main__":
    unittest.main()
