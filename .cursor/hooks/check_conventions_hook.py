#!/usr/bin/env python3
"""afterFileEdit hook: run convention checks on edited Python files."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def find_project_root_from_cwd() -> Path:
    cwd = Path.cwd().resolve()
    for directory in (cwd, *cwd.parents):
        if (directory / "pyproject.toml").exists():
            return directory
    return cwd


def _project_roots_from_path_hint(hint: Path) -> list[Path]:
    try:
        start = hint.resolve()
    except OSError:
        return []
    if start.is_file():
        start = start.parent
    roots: list[Path] = []
    for directory in (start, *start.parents):
        if (directory / "pyproject.toml").exists():
            roots.append(directory)
    return roots


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def project_root_candidates(payload: dict) -> list[Path]:
    candidates: list[Path] = []

    workspace_roots = payload.get("workspace_roots")
    if isinstance(workspace_roots, list):
        for value in workspace_roots:
            if isinstance(value, str) and value:
                candidates.append(Path(value))

    for raw_path in edited_paths(payload):
        candidates.extend(_project_roots_from_path_hint(raw_path))

    candidates.append(find_project_root_from_cwd())
    return _dedupe_paths(candidates)


def resolve_project_root(payload: dict) -> Path | None:
    for candidate in project_root_candidates(payload):
        if resolve_checker_script(candidate) is not None:
            return candidate
    for candidate in project_root_candidates(payload):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return None


def resolve_checker_script(project_root: Path) -> Path | None:
    candidates = (
        project_root / "scripts" / "check_conventions.py",
        project_root / "template" / "scripts" / "check_conventions.py",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def edited_paths(payload: dict) -> list[Path]:
    paths: list[Path] = []
    for key in ("file_path", "path", "filePath"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            paths.append(Path(value))

    edits = payload.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if not isinstance(edit, dict):
                continue
            for key in ("file_path", "path", "filePath"):
                value = edit.get(key)
                if isinstance(value, str) and value:
                    paths.append(Path(value))

    return paths


def _scan_dir_roots(project_root: Path) -> list[Path]:
    roots: list[Path] = []
    for parts in (("src",), ("tests",), ("template", "src"), ("template", "tests")):
        candidate = project_root.joinpath(*parts)
        if candidate.is_dir():
            roots.append(candidate.resolve())
    return roots


def should_scan(path: Path, project_root: Path) -> bool:
    if path.suffix != ".py":
        return False
    try:
        resolved = path.resolve()
        for scan_root in _scan_dir_roots(project_root):
            if scan_root in resolved.parents or resolved == scan_root:
                return True
    except OSError:
        return False
    return False


def run_checker(checker: Path, target: Path, project_root: Path) -> str | None:
    result = subprocess.run(
        [sys.executable, str(checker), str(target), "--root", str(project_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return None
    return result.stderr.strip() or result.stdout.strip()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    project_root = resolve_project_root(payload)
    if project_root is None:
        return 0

    checker = resolve_checker_script(project_root)
    if checker is None:
        return 0

    messages: list[str] = []
    seen: set[Path] = set()
    for raw_path in edited_paths(payload):
        path = raw_path if raw_path.is_absolute() else project_root / raw_path
        if path in seen or not should_scan(path, project_root):
            continue
        seen.add(path)
        output = run_checker(checker, path, project_root)
        if output:
            messages.append(output)

    if messages:
        context = (
            "LangChain convention violations detected after file edit. "
            "Fix these before continuing:\n" + "\n".join(messages)
        )
        print(json.dumps({"additional_context": context}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
