"""Tests for the afterFileEdit convention-check hook."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = SCAFFOLD_ROOT / ".cursor" / "hooks" / "check_conventions_hook.py"
CHECKER_SRC = SCAFFOLD_ROOT / "template" / "scripts" / "check_conventions.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("check_conventions_hook", HOOK_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load hook from {HOOK_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def hook():
    return _load_hook()


def test_edited_paths_reads_top_level_file_path(hook):
    payload = {"file_path": "/app/src/foo.py"}
    assert hook.edited_paths(payload) == [Path("/app/src/foo.py")]


def test_edited_paths_reads_nested_edits(hook):
    payload = {
        "edits": [
            {"path": "src/a.py"},
            {"filePath": "tests/b.py"},
        ]
    }
    paths = hook.edited_paths(payload)
    assert Path("src/a.py") in paths
    assert Path("tests/b.py") in paths


def test_should_scan_accepts_src_and_tests_python(hook, tmp_path: Path):
    project_root = tmp_path
    src_file = project_root / "src" / "app" / "mod.py"
    test_file = project_root / "tests" / "unit" / "test_mod.py"
    src_file.parent.mkdir(parents=True)
    test_file.parent.mkdir(parents=True)
    src_file.write_text("", encoding="utf-8")
    test_file.write_text("", encoding="utf-8")

    assert hook.should_scan(src_file, project_root) is True
    assert hook.should_scan(test_file, project_root) is True


def test_should_scan_rejects_non_python_and_outside_dirs(hook, tmp_path: Path):
    project_root = tmp_path
    md_file = project_root / "src" / "readme.md"
    outside = project_root / "scripts" / "tool.py"
    md_file.parent.mkdir(parents=True)
    outside.parent.mkdir(parents=True)
    md_file.write_text("# doc", encoding="utf-8")
    outside.write_text("print('ok')\n", encoding="utf-8")

    assert hook.should_scan(md_file, project_root) is False
    assert hook.should_scan(outside, project_root) is False


def test_should_scan_accepts_template_src_and_tests(hook, tmp_path: Path):
    project_root = tmp_path
    template_src = project_root / "template" / "src" / "app" / "mod.py"
    template_test = project_root / "template" / "tests" / "unit" / "test_mod.py"
    template_src.parent.mkdir(parents=True)
    template_test.parent.mkdir(parents=True)
    template_src.write_text("", encoding="utf-8")
    template_test.write_text("", encoding="utf-8")

    assert hook.should_scan(template_src, project_root) is True
    assert hook.should_scan(template_test, project_root) is True


def _bootstrap_fake_app(tmp_path: Path, *, bad: bool) -> tuple[Path, Path]:
    app_root = tmp_path / "fake-rag-app"
    app_root.mkdir()
    (app_root / "pyproject.toml").write_text('[project]\nname = "fake"\n', encoding="utf-8")
    (app_root / "scripts").mkdir()
    shutil.copy2(CHECKER_SRC, app_root / "scripts" / "check_conventions.py")

    target = app_root / "src" / "app" / "module.py"
    target.parent.mkdir(parents=True)
    if bad:
        target.write_text(
            "from langchain_classic.chains import LLMChain\n",
            encoding="utf-8",
        )
    else:
        target.write_text(
            "from langchain_openai import ChatOpenAI\n",
            encoding="utf-8",
        )
    return app_root, target


def _run_hook(app_root: Path, target: Path) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"file_path": str(target)})
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload,
        cwd=app_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_hook_reports_violations_on_bad_edit(tmp_path: Path):
    app_root, target = _bootstrap_fake_app(tmp_path, bad=True)
    result = _run_hook(app_root, target)

    assert result.returncode == 0
    assert result.stdout.strip()
    output = json.loads(result.stdout)
    assert "additional_context" in output
    assert "langchain_classic" in output["additional_context"]


def test_hook_reports_violations_when_cwd_is_not_project_root(tmp_path: Path):
    app_root, target = _bootstrap_fake_app(tmp_path, bad=True)
    payload = json.dumps(
        {
            "file_path": str(target),
            "workspace_roots": [str(app_root)],
        }
    )
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip()
    output = json.loads(result.stdout)
    assert "additional_context" in output
    assert "langchain_classic" in output["additional_context"]


def test_resolve_project_root_uses_workspace_roots(hook, tmp_path: Path):
    app_root = tmp_path / "fake-rag-app"
    app_root.mkdir()
    (app_root / "pyproject.toml").write_text('[project]\nname = "fake"\n', encoding="utf-8")
    (app_root / "scripts").mkdir()
    shutil.copy2(CHECKER_SRC, app_root / "scripts" / "check_conventions.py")

    payload = {
        "file_path": str(app_root / "src" / "app" / "module.py"),
        "workspace_roots": [str(app_root)],
    }
    assert hook.resolve_project_root(payload) == app_root.resolve()


def test_resolve_project_root_uses_edited_file_path(hook, tmp_path: Path):
    app_root = tmp_path / "fake-rag-app"
    app_root.mkdir()
    (app_root / "pyproject.toml").write_text('[project]\nname = "fake"\n', encoding="utf-8")
    (app_root / "scripts").mkdir()
    shutil.copy2(CHECKER_SRC, app_root / "scripts" / "check_conventions.py")
    target = app_root / "src" / "app" / "module.py"
    target.parent.mkdir(parents=True)
    target.write_text("print('ok')\n", encoding="utf-8")

    payload = {"file_path": str(target)}
    assert hook.resolve_project_root(payload) == app_root.resolve()


def test_hook_silent_on_clean_edit(tmp_path: Path):
    app_root, target = _bootstrap_fake_app(tmp_path, bad=False)
    result = _run_hook(app_root, target)

    assert result.returncode == 0
    if result.stdout.strip():
        output = json.loads(result.stdout)
        assert "additional_context" not in output
