#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/backend"

if [ ! -d ".venv" ]; then
  echo "Run bin/setup.sh first (missing backend/.venv)" >&2
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Applying migrations"
alembic upgrade head

if [ ! -f "app/seed.py" ]; then
  echo "Full mock seed lands in Slice 8."
  echo "Start the API once to create the bootstrap admin (see README)."
  exit 0
fi

python -m app.seed
