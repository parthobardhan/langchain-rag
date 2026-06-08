"""Tests for the bootstrap script."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCAFFOLD_ROOT / "scripts"))

from create_app import (  # noqa: E402
    create_app,
    package_name_from_app_name,
    validate_package_name,
)


def test_package_name_from_app_name_converts_hyphens():
    assert package_name_from_app_name("acme-docs-rag") == "acme_docs_rag"


def test_package_name_from_app_name_rejects_digit_prefix():
    with pytest.raises(ValueError, match="cannot derive package name"):
        package_name_from_app_name("123-app")


@pytest.mark.parametrize(
    "name",
    ["acme_docs_rag", "_private", "my_app2"],
)
def test_validate_package_name_accepts_valid_names(name: str):
    assert validate_package_name(name) == name


@pytest.mark.parametrize(
    "name",
    ["acme-docs-rag", "1bad", "", "has space", "bad-name"],
)
def test_validate_package_name_rejects_invalid_names(name: str):
    with pytest.raises(ValueError, match="Invalid package name"):
        validate_package_name(name)


def test_bootstrap_hyphenated_app_name_uses_valid_project_name(tmp_path: Path):
    dest = create_app("acme-docs-rag", "acme_docs_rag", tmp_path, copy_cursor=False)

    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "acme_docs_rag"' in pyproject
    assert 'name = "acme-docs-rag"' not in pyproject
    assert '"acme_docs_rag" = "acme_docs_rag.cli:app"' in pyproject
    assert (dest / "src" / "acme_docs_rag" / "cli.py").is_file()


def test_bootstrap_derives_package_name_from_app_name(tmp_path: Path):
    package_name = package_name_from_app_name("my-cool-rag")
    dest = create_app("my-cool-rag", package_name, tmp_path, copy_cursor=False)

    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "my_cool_rag"' in pyproject
