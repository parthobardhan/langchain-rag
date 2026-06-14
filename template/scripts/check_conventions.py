#!/usr/bin/env python3
"""Check LangChain RAG app source for banned APIs and deprecated patterns."""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SCAN_DIRS = ("src", "tests")

CHAIN_RUN_MESSAGE = "deprecated API: .run() (use chain.invoke() with LCEL)"
INITIALIZE_AGENT_MESSAGE = (
    "deprecated API: initialize_agent() (use LCEL agent patterns)"
)
ALLOWED_RUN_MODULES = frozenset({"asyncio", "subprocess"})


@dataclass(frozen=True)
class BannedAPI:
    patterns: tuple[re.Pattern[str], ...]
    message: str
    category: str  # "broken-import" | "deprecated"
    rule_bullets: tuple[str, ...]
    bugbot_item: str


BANNED_APIS: tuple[BannedAPI, ...] = (
    BannedAPI(
        patterns=(re.compile(r"^\s*from\s+langchain\.chains\s+import\b", re.MULTILINE),),
        message="broken import: langchain.chains (removed in v0.3+; use LCEL)",
        category="broken-import",
        rule_bullets=("`from langchain.chains import LLMChain`",),
        bugbot_item="No `from langchain.chains import ...`",
    ),
    BannedAPI(
        patterns=(re.compile(r"^\s*from\s+langchain\.chat_models\s+import\b", re.MULTILINE),),
        message="broken import: langchain.chat_models (use langchain_openai.ChatOpenAI)",
        category="broken-import",
        rule_bullets=("`from langchain.chat_models import ChatOpenAI`",),
        bugbot_item="No `from langchain.chat_models import ...`",
    ),
    BannedAPI(
        patterns=(re.compile(r"^\s*from\s+langchain\.memory\s+import\b", re.MULTILINE),),
        message="broken import: langchain.memory (use RunnableWithMessageHistory)",
        category="broken-import",
        rule_bullets=("`from langchain.memory import ConversationBufferMemory`",),
        bugbot_item="No `from langchain.memory import ...`",
    ),
    BannedAPI(
        patterns=(
            re.compile(r"^\s*from\s+langchain_classic\b", re.MULTILINE),
            re.compile(r"^\s*import\s+langchain_classic\b", re.MULTILINE),
        ),
        message="deprecated shim: langchain_classic (use LCEL imports from langchain_core / langchain_openai)",
        category="deprecated",
        rule_bullets=(
            "`from langchain_classic.chains import LLMChain`",
            "`from langchain_classic.memory import ConversationBufferMemory`",
        ),
        bugbot_item="No `langchain_classic` imports",
    ),
    BannedAPI(
        patterns=(),
        message=CHAIN_RUN_MESSAGE,
        category="deprecated",
        rule_bullets=("`chain.run(...)` — deprecated method",),
        bugbot_item="No `.run()` on chains — use `.invoke()` with LCEL",
    ),
    BannedAPI(
        patterns=(),
        message=INITIALIZE_AGENT_MESSAGE,
        category="deprecated",
        rule_bullets=("`initialize_agent(...)` — deprecated",),
        bugbot_item="No `initialize_agent(...)`",
    ),
)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def _is_python_source(path: Path) -> bool:
    return path.suffix == ".py" and path.is_file()


def _collect_module_aliases(tree: ast.AST) -> dict[str, str]:
    """Map local names from `import` statements to their top-level module."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            local = alias.asname or alias.name.split(".")[0]
            root = alias.name.split(".")[0]
            aliases[local] = root
    return aliases


def _run_call_receiver_name(node: ast.AST) -> str | None:
    """Return the root name for obj.run() calls, e.g. chain, asyncio, subprocess."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _run_call_receiver_name(node.value)
    return None


def _is_allowed_run_receiver(name: str | None, aliases: dict[str, str]) -> bool:
    if name is None:
        return False
    module = aliases.get(name, name)
    return module in ALLOWED_RUN_MODULES


def _scan_chain_run_calls(
    tree: ast.AST, path: Path, aliases: dict[str, str]
) -> list[Violation]:
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "run":
            continue
        receiver = _run_call_receiver_name(func.value)
        if _is_allowed_run_receiver(receiver, aliases):
            continue
        violations.append(
            Violation(path=path, line=func.lineno, message=CHAIN_RUN_MESSAGE)
        )
    return violations


def _scan_initialize_agent_calls(tree: ast.AST, path: Path) -> list[Violation]:
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "initialize_agent":
            violations.append(
                Violation(path=path, line=func.lineno, message=INITIALIZE_AGENT_MESSAGE)
            )
    return violations


def _scan_ast_violations(source: str, path: Path) -> list[Violation]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    aliases = _collect_module_aliases(tree)
    violations: list[Violation] = []
    violations.extend(_scan_chain_run_calls(tree, path, aliases))
    violations.extend(_scan_initialize_agent_calls(tree, path))
    return violations


def scan_text(text: str, path: Path) -> list[Violation]:
    violations: list[Violation] = []
    for api in BANNED_APIS:
        for pattern in api.patterns:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append(Violation(path=path, line=line, message=api.message))
    violations.extend(_scan_ast_violations(text, path))
    return violations


def scan_file(path: Path) -> list[Violation]:
    if not _is_python_source(path):
        return []
    text = path.read_text(encoding="utf-8")
    return scan_text(text, path)


def iter_python_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if _is_python_source(root) else []
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts and ".venv" not in path.parts
    )


def scan_paths(paths: list[Path], *, root: Path | None = None) -> list[Violation]:
    project_root = root or Path.cwd()
    violations: list[Violation] = []
    seen: set[Path] = set()

    for raw_path in paths:
        path = raw_path if raw_path.is_absolute() else project_root / raw_path
        path = path.resolve()
        for file_path in iter_python_files(path):
            if file_path in seen:
                continue
            seen.add(file_path)
            violations.extend(scan_file(file_path))

    return sorted(violations, key=lambda item: (str(item.path), item.line, item.message))


def scan_default_dirs(root: Path | None = None) -> list[Violation]:
    project_root = root or Path.cwd()
    existing = [project_root / name for name in DEFAULT_SCAN_DIRS if (project_root / name).exists()]
    if not existing:
        return []
    return scan_paths(existing, root=project_root)


def format_violations(violations: list[Violation]) -> str:
    return "\n".join(violation.format() for violation in violations)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail on LangChain convention violations in src/ and tests/."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to scan (default: src/ and tests/)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root for relative paths (default: current directory)",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if args.paths:
        violations = scan_paths([Path(p) for p in args.paths], root=root)
    else:
        violations = scan_default_dirs(root)

    if violations:
        print(format_violations(violations), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
