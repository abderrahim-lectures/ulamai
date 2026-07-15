#!/usr/bin/env bash
# Standalone launcher: runs ulam straight from this repo checkout, no `pip install`.
# Uses the project's uv-managed .venv (created via `uv venv .venv`) for the
# dojo backend's third-party deps (lean-dojo-v2, PyPantograph); everything
# else is stdlib.
set -euo pipefail
DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PY="$DIR/.venv/bin/python3"
if [[ ! -x "$PY" ]]; then
    echo "error: $PY not found. Run: uv venv .venv && uv pip install --python .venv/bin/python -e . lean-dojo-v2 git+https://github.com/stanford-centaur/PyPantograph" >&2
    exit 1
fi
if [[ -f "$DIR/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$DIR/.env"
    set +a
fi
export PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}"
exec "$PY" -m ulam "$@"
