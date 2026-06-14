# Changelog

All notable changes to the **langchain-rag-scaffold** are documented here. Version numbers match [.cursor-plugin/plugin.json](.cursor-plugin/plugin.json).

## [Unreleased]

### Added

- LangChain docs MCP server (`docs-langchain`) in `.cursor/mcp.json`, propagated to generated apps; referenced in rules, skill, commands, Bugbot checklist, and maintainer guide

### Changed

- Pin `pyyaml>=6.0.2` in generated apps to avoid pip backtracking to PyYAML 6.0 sdists that fail to build on Python 3.13
- Banned API list is canonical in `template/scripts/check_conventions.py`; `scripts/sync_conventions.py` generates matching sections in `.cursor/rules/langchain-conventions.mdc` and `.cursor/BUGBOT.md` (CI-enforced via `tests/test_conventions_sync.py`)

## [0.1.0] - 2026-06-10

### Added

- Deterministic convention checker (`template/scripts/check_conventions.py`) with Cursor hook, pytest gate, and CI integration
- Generated-app smoke test (`tests/test_generated_app.py`)
- GitHub Actions CI matrix (Python 3.11–3.13) and weekly dependency canary
- Bugbot review checklist (`.cursor/BUGBOT.md`)
- Maintainer guide (`docs/maintainers.md`)
- Template `.gitignore` and `.cursorignore` for secrets safety
- Dependency allowlist unit test for generated apps
- `AGENTS.md` boundary guidance at scaffold and template roots
- `/first-contribution` command for onboarding (PDF loader TDD walkthrough)
