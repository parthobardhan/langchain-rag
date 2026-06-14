"""Ensure pyproject.toml only declares approved dependencies."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

# Approved runtime dependencies for generated RAG apps.
APPROVED_DEPENDENCIES = {
    "langchain",
    "langchain-core",
    "langchain-openai",
    "langchain-voyageai",
    "langchain-mongodb",
    "langchain-text-splitters",
    "pymongo",
    "python-dotenv",
    "pydantic-settings",
    "pyyaml",
    "typer",
}

_MARKER_PATTERN = re.compile(r";.*$")


def _base_package_name(specifier: str) -> str:
    cleaned = _MARKER_PATTERN.sub("", specifier).strip()
    match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", cleaned)
    if not match:
        raise ValueError(f"Could not parse dependency specifier: {specifier!r}")
    return match.group(1).lower().replace("_", "-")


def test_runtime_dependencies_are_allowlisted():
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    dependencies = data.get("project", {}).get("dependencies", [])
    assert dependencies, "expected project.dependencies in pyproject.toml"

    declared = {_base_package_name(item) for item in dependencies}
    unknown = sorted(declared - APPROVED_DEPENDENCIES)
    assert unknown == [], f"Unapproved dependencies: {unknown}"
