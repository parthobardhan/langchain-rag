"""Tests for the convention checker script."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = SCAFFOLD_ROOT / "template" / "scripts" / "check_conventions.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_conventions", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load checker from {CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_checker_flags_langchain_classic_import(tmp_path: Path):
    checker = _load_checker()
    bad_file = tmp_path / "src" / "app" / "bad.py"
    bad_file.parent.mkdir(parents=True)
    bad_file.write_text(
        "from langchain_classic.chains import LLMChain\n",
        encoding="utf-8",
    )

    violations = checker.scan_paths([tmp_path / "src"], root=tmp_path)
    assert violations
    assert "langchain_classic" in violations[0].message


def test_checker_passes_clean_file(tmp_path: Path):
    checker = _load_checker()
    good_file = tmp_path / "src" / "app" / "good.py"
    good_file.parent.mkdir(parents=True)
    good_file.write_text(
        "from langchain_openai import ChatOpenAI\n",
        encoding="utf-8",
    )

    violations = checker.scan_paths([tmp_path / "src"], root=tmp_path)
    assert violations == []


def test_checker_allows_asyncio_and_subprocess_run(tmp_path: Path):
    checker = _load_checker()
    good_file = tmp_path / "src" / "app" / "cli.py"
    good_file.parent.mkdir(parents=True)
    good_file.write_text(
        "import asyncio\n"
        "import subprocess\n"
        "\n"
        "asyncio.run(main())\n"
        "subprocess.run([sys.executable, \"scripts/check.py\"])\n",
        encoding="utf-8",
    )

    violations = checker.scan_paths([tmp_path / "src"], root=tmp_path)
    assert violations == []


def test_checker_allows_aliased_asyncio_and_subprocess_run(tmp_path: Path):
    checker = _load_checker()
    good_file = tmp_path / "src" / "app" / "cli.py"
    good_file.parent.mkdir(parents=True)
    good_file.write_text(
        "import asyncio as aio\n"
        "import subprocess as sp\n"
        "\n"
        "aio.run(main())\n"
        "sp.run([sys.executable, \"scripts/check.py\"])\n",
        encoding="utf-8",
    )

    violations = checker.scan_paths([tmp_path / "src"], root=tmp_path)
    assert violations == []


def test_checker_allows_non_chain_run_calls(tmp_path: Path):
    checker = _load_checker()
    good_file = tmp_path / "src" / "app" / "server.py"
    good_file.parent.mkdir(parents=True)
    good_file.write_text(
        "import uvicorn\n"
        "\n"
        "class App:\n"
        "    def run(self):\n"
        "        pass\n"
        "\n"
        "app = App()\n"
        "uvicorn.run(app)\n"
        "app.run()\n"
        "self.run()\n",
        encoding="utf-8",
    )

    violations = checker.scan_paths([tmp_path / "src"], root=tmp_path)
    assert violations == []


def test_checker_flags_chain_run(tmp_path: Path):
    checker = _load_checker()
    bad_file = tmp_path / "src" / "app" / "bad.py"
    bad_file.parent.mkdir(parents=True)
    bad_file.write_text('chain.run("hi")\n', encoding="utf-8")

    violations = checker.scan_paths([tmp_path / "src"], root=tmp_path)
    assert violations
    assert ".run()" in violations[0].message


def test_checker_ignores_run_in_string_literals(tmp_path: Path):
    checker = _load_checker()
    test_file = tmp_path / "tests" / "unit" / "test_checker.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        'bad_file.write_text(\'chain.run("hi")\\n\', encoding="utf-8")\n'
        'assert ".run()" in violations[0].message\n',
        encoding="utf-8",
    )

    violations = checker.scan_paths([tmp_path / "tests"], root=tmp_path)
    assert violations == []


def test_checker_ignores_banned_patterns_in_strings_and_docstrings(tmp_path: Path):
    checker = _load_checker()
    good_file = tmp_path / "src" / "app" / "docs.py"
    good_file.parent.mkdir(parents=True)
    good_file.write_text(
        '"""\n'
        "from langchain.chains import LLMChain\n"
        "from langchain_classic.chains import LLMChain\n"
        "initialize_agent(tools)\n"
        '"""\n'
        'EXAMPLE = "from langchain.memory import ConversationBufferMemory"\n'
        'CALL = "initialize_agent(tools)"\n',
        encoding="utf-8",
    )

    violations = checker.scan_paths([tmp_path / "src"], root=tmp_path)
    assert violations == []


def test_checker_flags_initialize_agent_call(tmp_path: Path):
    checker = _load_checker()
    bad_file = tmp_path / "src" / "app" / "bad.py"
    bad_file.parent.mkdir(parents=True)
    bad_file.write_text("agent = initialize_agent(tools, llm)\n", encoding="utf-8")

    violations = checker.scan_paths([tmp_path / "src"], root=tmp_path)
    assert violations
    assert "initialize_agent" in violations[0].message


def test_checker_ignores_initialize_agent_in_string_literals(tmp_path: Path):
    checker = _load_checker()
    test_file = tmp_path / "tests" / "unit" / "test_checker.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        'assert "initialize_agent(...)" in rule_bullets\n',
        encoding="utf-8",
    )

    violations = checker.scan_paths([tmp_path / "tests"], root=tmp_path)
    assert violations == []


def test_checker_passes_when_scanning_itself():
    checker = _load_checker()
    violations = checker.scan_paths([CHECKER_PATH], root=SCAFFOLD_ROOT)
    assert violations == []
