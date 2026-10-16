#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$project_dir"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import simshelf, fastapi, uvicorn' >/dev/null 2>&1; then
  .venv/bin/python -m pip install -e .
fi
exec .venv/bin/python -m simshelf --workspace "${SIMSHELF_HOME:-$project_dir/.simshelf}" ui "$@"
