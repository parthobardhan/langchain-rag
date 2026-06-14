"""Smoke test: a bootstrapped app installs and passes unit tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCAFFOLD_ROOT / "scripts"))

from create_app import create_app  # noqa: E402

pytestmark = pytest.mark.smoke


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def generated_app(tmp_path: Path) -> Path:
    return create_app("smoke-test-rag", "smoke_test_rag", tmp_path, copy_cursor=True)


def test_generated_app_installs_and_passes_unit_tests(generated_app: Path):
    if os.environ.get("SKIP_SMOKE_TESTS") == "1":
        pytest.skip("SKIP_SMOKE_TESTS=1")

    venv_dir = generated_app / ".venv"
    create_venv = _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=generated_app)
    assert create_venv.returncode == 0, create_venv.stderr

    if sys.platform == "win32":
        python = venv_dir / "Scripts" / "python.exe"
        pip = venv_dir / "Scripts" / "pip.exe"
    else:
        python = venv_dir / "bin" / "python"
        pip = venv_dir / "bin" / "pip"

    bootstrap_pip = _run(
        [str(pip), "install", "--upgrade", "pip", "setuptools", "wheel"],
        cwd=generated_app,
    )
    assert bootstrap_pip.returncode == 0, bootstrap_pip.stderr or bootstrap_pip.stdout

    install = _run(
        [str(pip), "install", "-e", ".[dev]"],
        cwd=generated_app,
        env={**os.environ, "PIP_PREFER_BINARY": "1"},
    )
    assert install.returncode == 0, install.stderr or install.stdout

    unit_tests = _run(
        [str(python), "-m", "pytest", "tests/unit", "-v"],
        cwd=generated_app,
    )
    assert unit_tests.returncode == 0, unit_tests.stdout + unit_tests.stderr

    checker = _run(
        [str(python), "scripts/check_conventions.py"],
        cwd=generated_app,
    )
    assert checker.returncode == 0, checker.stderr or checker.stdout


def test_copy_cursor_guidance_substitutes_placeholders(tmp_path: Path):
    dest = create_app("acme-docs-rag", "acme_docs_rag", tmp_path, copy_cursor=True)
    content = (dest / ".cursor" / "commands" / "first-contribution.md").read_text(
        encoding="utf-8"
    )
    assert "{{package_name}}" not in content
    assert "acme_docs_rag.ingestion.loader._load_pdf" in content


def test_generated_app_propagates_scaffold_guidance(generated_app: Path):
    assert (generated_app / ".gitignore").is_file()
    assert (generated_app / ".cursorignore").is_file()
    assert (generated_app / "AGENTS.md").is_file()
    assert (generated_app / ".cursor" / "hooks.json").is_file()
    assert (generated_app / ".cursor" / "hooks" / "check_conventions_hook.py").is_file()
    assert (generated_app / ".cursor" / "BUGBOT.md").is_file()
    assert (generated_app / ".cursor" / "commands" / "first-contribution.md").is_file()
    assert (generated_app / ".cursor" / "mcp.json").is_file()
    assert (generated_app / ".github" / "workflows" / "ci.yml").is_file()
