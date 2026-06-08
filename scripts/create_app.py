#!/usr/bin/env python3
"""Bootstrap a new RAG app from the langchain-rag template."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SCAFFOLD_ROOT / "template"
CURSOR_DIR = SCAFFOLD_ROOT / ".cursor"
PLUGIN_DIR = SCAFFOLD_ROOT / ".cursor-plugin"

SKIP_COPY = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"}

_VALID_PACKAGE_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_package_name(package_name: str) -> str:
    """Ensure package name is a valid Python / PEP 508 identifier."""
    if not _VALID_PACKAGE_NAME.fullmatch(package_name):
        raise ValueError(
            f"Invalid package name '{package_name}': "
            "must start with a letter or underscore and contain only letters, digits, and underscores"
        )
    return package_name


def validate_app_name(app_name: str) -> str:
    """Ensure app_name is a single safe directory name (no path components)."""
    name = app_name.strip()
    if not name:
        raise ValueError("App name cannot be empty")
    if name in {".", ".."}:
        raise ValueError(
            f"Invalid app name {app_name!r}: must be a single directory name"
        )
    path = Path(name)
    if path.name != name or ".." in path.parts or len(path.parts) != 1:
        raise ValueError(
            f"Invalid app name {app_name!r}: must be a single directory name "
            "(no slashes or parent references)"
        )
    return name


def resolve_app_dest(output_parent: Path, app_name: str) -> Path:
    """Return the resolved destination path, ensuring it stays under output_parent."""
    safe_name = validate_app_name(app_name)
    parent = output_parent.resolve()
    dest = (parent / safe_name).resolve()
    try:
        dest.relative_to(parent)
    except ValueError as exc:
        raise ValueError(
            f"Invalid app name {app_name!r}: destination {dest} is outside {parent}"
        ) from exc
    return dest


def package_name_from_app_name(app_name: str) -> str:
    """Convert app directory name to a valid Python package name."""
    name = re.sub(r"[^a-zA-Z0-9]+", "_", app_name.strip()).strip("_").lower()
    if not name or name[0].isdigit():
        raise ValueError(f"Invalid app name '{app_name}': cannot derive package name")
    return validate_package_name(name)


def replace_placeholders(content: str, package_name: str, app_name: str) -> str:
    return (
        content.replace("{{package_name}}", package_name)
        .replace("{{app_name}}", app_name)
    )


def copy_tree(src: Path, dst: Path, package_name: str, app_name: str) -> None:
    for item in src.rglob("*"):
        if any(part in SKIP_COPY for part in item.parts):
            continue
        rel = item.relative_to(src)
        rel_str = str(rel).replace("{{package_name}}", package_name)
        target = dst / rel_str

        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        text = item.read_text(encoding="utf-8")
        target.write_text(
            replace_placeholders(text, package_name, app_name),
            encoding="utf-8",
        )


def create_app(
    app_name: str,
    package_name: str,
    output_parent: Path,
    *,
    copy_cursor: bool = True,
) -> Path:
    """Bootstrap a new RAG app. Returns the destination directory."""
    validate_package_name(package_name)
    dest = resolve_app_dest(output_parent, app_name)
    if dest.exists():
        raise FileExistsError(f"destination already exists: {dest}")

    dest.mkdir(parents=True)
    try:
        copy_tree(TEMPLATE_DIR, dest, package_name, app_name)
        if copy_cursor:
            copy_cursor_guidance(dest)
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    return dest


def copy_cursor_guidance(dst: Path) -> None:
    """Copy Cursor rules, skills, and commands into the generated app."""
    if not CURSOR_DIR.exists():
        return
    dest_cursor = dst / ".cursor"
    if dest_cursor.exists():
        shutil.rmtree(dest_cursor)
    shutil.copytree(CURSOR_DIR, dest_cursor)

    if PLUGIN_DIR.exists():
        dest_plugin = dst / ".cursor-plugin"
        if dest_plugin.exists():
            shutil.rmtree(dest_plugin)
        shutil.copytree(PLUGIN_DIR, dest_plugin)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a new LangChain RAG app from the scaffold template."
    )
    parser.add_argument(
        "app_name",
        help="Directory name for the new app (e.g. acme-docs-rag)",
    )
    parser.add_argument(
        "--package",
        dest="package_name",
        help="Python package name (default: derived from app_name)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Parent directory for the new app (default: parent of scaffold repo)",
    )
    args = parser.parse_args()

    if not TEMPLATE_DIR.is_dir():
        print(f"Error: template not found at {TEMPLATE_DIR}", file=sys.stderr)
        return 1

    try:
        app_name = validate_app_name(args.app_name)
        package_name = validate_package_name(
            args.package_name or package_name_from_app_name(app_name)
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output_parent = args.output_dir or SCAFFOLD_ROOT.parent
    dest_path = resolve_app_dest(output_parent, app_name)

    print(f"Creating RAG app at {dest_path}")
    print(f"  Package name: {package_name}")

    try:
        dest = create_app(app_name, package_name, output_parent)
    except (FileExistsError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(
        f"""
Done! Next steps:

  cd {dest}
  python -m venv .venv && source .venv/bin/activate
  pip install -e ".[dev]"
  cp .env.example .env    # add MONGODB_URI, VOYAGE_API_KEY, OPENAI_API_KEY

  python -m {package_name}.cli ingest data/sample/
  python -m {package_name}.cli query "What is in the sample docs?"

See README.md for the full workflow.
"""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
