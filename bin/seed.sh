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

if [ ! -f "app/seed.py" ]; then
  echo "Seed data is not implemented yet (Slice 8)."
  echo "After Slice 1, this script will run: alembic upgrade head && python -m app.seed"
  exit 0
fi

if [ -d "alembic" ]; then
  alembic upgrade head
fi

python -m app.seed
