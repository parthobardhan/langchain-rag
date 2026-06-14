# Maintainer Guide

Non-obvious invariants for the **langchain-rag-scaffold**. Read this before changing template, rules, or CI.

## Banned API list — checker is canonical

The banned LangChain APIs are defined once in [template/scripts/check_conventions.py](../template/scripts/check_conventions.py) (`BANNED_APIS`). Generated sections in these files are synced from the checker:

1. [.cursor/rules/langchain-conventions.mdc](../.cursor/rules/langchain-conventions.mdc) — advisory for agents (banned section only)
2. [.cursor/BUGBOT.md](../.cursor/BUGBOT.md) — review checklist (banned section only)

When adding or removing a banned pattern:

1. Edit `BANNED_APIS` in `template/scripts/check_conventions.py`
2. Run `python scripts/sync_conventions.py` to regenerate the marked sections
3. Commit the checker and synced docs together

CI runs `tests/test_conventions_sync.py`, which fails if generated sections are stale. Use `python scripts/sync_conventions.py --check` locally to verify before pushing.

## Checker consumers

The checker script is wired into four surfaces:

| Consumer | Location | Purpose |
|----------|----------|---------|
| Cursor hook | `.cursor/hooks/check_conventions_hook.py` | Agent self-corrects after edits |
| Unit test | `template/tests/unit/test_conventions.py` | `pytest tests/unit` gate in generated apps |
| CLI | `scripts/check_conventions.py` in generated apps | Manual and CI invocation |
| CI workflow | `template/.github/workflows/ci.yml` | PR/push gate in generated apps |

## Hook path duality

The hook resolves the checker at:

1. `scripts/check_conventions.py` (generated app layout)
2. `template/scripts/check_conventions.py` (scaffold repo layout)

`copy_cursor_guidance()` copies the entire `.cursor/` directory into generated apps and substitutes `{{package_name}}` / `{{app_name}}` in copied text files.

## Placeholder substitution

`create_app.py` runs `replace_placeholders()` on **every** template file and on copied `.cursor/` / `.cursor-plugin/` text files. Do not put literal `{{package_name}}` or `{{app_name}}` sequences in those files unless they should be substituted (including Python scripts and tests).

## Conditional `langchain-voyageai` pins

`template/pyproject.toml` pins Voyage differently by Python version:

- `<3.13`: `langchain-voyageai>=0.2.0`
- `>=3.13`: `langchain-voyageai>=0.1.3`

CI runs pytest on 3.11, 3.12, and 3.13 to exercise both branches. The weekly canary (`scripts/canary_latest_deps.sh`) catches upstream breakage against floor pins.

## `pyyaml` floor pin

`template/pyproject.toml` pins `pyyaml>=6.0.2`. On Python 3.13, pip can otherwise backtrack to PyYAML 6.0.x sdists while resolving `langchain-core`'s loose `pyyaml>=5.3.0` constraint; those older releases fail to build from source with current setuptools (`AttributeError: 'build_ext' object has no attribute 'cython_sources'`). PyYAML 6.0.2+ ships cp313 wheels.

## Test split

| Location | What it tests |
|----------|---------------|
| `langchain-rag-scaffold/tests/` | Scaffold bootstrap, template behavior, generated-app smoke test |
| `template/tests/` | Copied into generated apps; unit + integration tests for app code |

Scaffold tests use `copy_cursor=False` when they only need template layout. The smoke test (`tests/test_generated_app.py`) uses `copy_cursor=True` and installs the generated app in a venv.

## Propagating Cursor guidance

`copy_cursor_guidance()` copies:

- `.cursor/` → `<app>/.cursor/` (rules, skills, commands, hooks, BUGBOT.md)
- `.cursor-plugin/` → `<app>/.cursor-plugin/`

Placeholders in copied Cursor files are substituted the same way as template files.

Generated apps do not get scaffold-only files (`docs/maintainers.md`, scaffold `tests/`, etc.).

## Versioning

Bump [.cursor-plugin/plugin.json](../.cursor-plugin/plugin.json) `version` when shipping user-visible scaffold changes. Record the change in [CHANGELOG.md](../CHANGELOG.md).

## Dependency allowlist

Generated apps should only depend on the approved stack. `template/tests/unit/test_dependency_allowlist.py` parses `pyproject.toml` and fails if unknown dependencies are added. Update the allowlist in that test when intentionally adding a new approved dependency.

## LangChain docs MCP

The scaffold ships `.cursor/mcp.json` with the official LangChain docs MCP server (`docs-langchain`). It is copied into generated apps via `copy_cursor_guidance()`.

Use the docs MCP when:

1. **Triaging canary failures** — query what changed upstream when `scripts/canary_latest_deps.sh` breaks against floor pins
2. **Auditing `BANNED_APIS`** — check whether LangChain has deprecated or removed APIs that should be added to the checker

Encode any team decisions back into `BANNED_APIS` and run `python scripts/sync_conventions.py` — the MCP is for discovery; the checker remains the source of truth.
