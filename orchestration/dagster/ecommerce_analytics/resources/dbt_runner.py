import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_DBT_PROJECT_DIR = _REPO_ROOT / "dw" / "snowflake" / "analytics"


def run_dbt_build(select: str) -> None:
    project_dir = str(_DBT_PROJECT_DIR)
    argv = [
        "dbt",
        "build",
        "--project-dir",
        project_dir,
        "--profiles-dir",
        project_dir,
        "--select",
        select,
    ]
    result = subprocess.run(argv, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"dbt build failed with exit code {result.returncode} "
            f"(select={select!r})"
        )
