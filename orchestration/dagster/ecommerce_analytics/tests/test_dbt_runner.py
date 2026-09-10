import subprocess
import unittest
from unittest.mock import patch

from orchestration.dagster.ecommerce_analytics.resources.dbt_runner import run_dbt_build


class DbtRunnerTest(unittest.TestCase):
    def test_run_dbt_build_invokes_build_with_project_profiles_and_select(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        with patch(
            "orchestration.dagster.ecommerce_analytics.resources.dbt_runner.subprocess.run",
            return_value=completed,
        ) as mock_run:
            run_dbt_build("path:models/silver")

        mock_run.assert_called_once()
        argv = mock_run.call_args.args[0]
        self.assertEqual(argv[0], "dbt")
        self.assertIn("build", argv)
        project_dir = argv[argv.index("--project-dir") + 1]
        profiles_dir = argv[argv.index("--profiles-dir") + 1]
        self.assertTrue(
            project_dir.replace("\\", "/").endswith("dw/snowflake/analytics"),
            project_dir,
        )
        self.assertEqual(project_dir, profiles_dir)
        self.assertEqual(argv[argv.index("--select") + 1], "path:models/silver")

    def test_run_dbt_build_raises_on_nonzero_exit(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=2, stdout="", stderr="dbt failed"
        )
        with patch(
            "orchestration.dagster.ecommerce_analytics.resources.dbt_runner.subprocess.run",
            return_value=completed,
        ):
            with self.assertRaises(Exception):
                run_dbt_build("path:models/gold")


if __name__ == "__main__":
    unittest.main()
