#!/usr/bin/env bash
# Bootstrap a fresh app and verify it works with the latest resolvable floor pins.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKDIR="$(mktemp -d)"
APP_DIR="${WORKDIR}/canary-rag-app"

cleanup() {
  rm -rf "${WORKDIR}"
}
trap cleanup EXIT

cd "${ROOT}"

python3 scripts/create_app.py canary-rag-app --package canary_rag_app --output-dir "${WORKDIR}"

cd "${APP_DIR}"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

pytest tests/unit -v
python scripts/check_conventions.py

echo "Canary passed: generated app installs and unit tests pass with latest deps."
