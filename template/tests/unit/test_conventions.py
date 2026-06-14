"""Ensure generated app source follows LangChain conventions."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKER_PATH = PROJECT_ROOT / "scripts" / "check_conventions.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_conventions", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load checker from {CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_no_convention_violations_in_src():
    checker = _load_checker()
    violations = checker.scan_default_dirs(PROJECT_ROOT)
    assert violations == [], checker.format_violations(violations)
