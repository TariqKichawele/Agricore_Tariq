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

echo "==> Loading Prairie Crest mock data"
python -m app.seed --reset
