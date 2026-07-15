#!/usr/bin/env bash
# Standalone launcher: runs ulam straight from this repo checkout, no `pip install`.
# Uses the project's uv-managed .venv (created via `uv venv .venv`) for the
# one third-party dependency (pantograph); everything else is stdlib.
set -euo pipefail
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PY="$DIR/.venv/bin/python3"
if [[ ! -x "$PY" ]]; then
    echo "error: $PY not found. Run: uv venv .venv && uv pip install --python .venv/bin/python pantograph" >&2
    exit 1
fi
export PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "$PY" -m ulam "$@"
