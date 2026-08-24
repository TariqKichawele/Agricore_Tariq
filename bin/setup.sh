#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> AgriCore setup"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required" >&2
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  echo "==> Starting local PostgreSQL (Docker)"
  if ! docker compose up -d postgres; then
    echo "Warning: Docker daemon not available. Start Docker Desktop and re-run: docker compose up -d postgres"
  fi
else
  echo "Warning: docker not found. Start PostgreSQL yourself using DATABASE_URL in backend/.env"
fi

echo "==> Python virtualenv"
python3 -m venv "$ROOT/backend/.venv"
# shellcheck disable=SC1091
source "$ROOT/backend/.venv/bin/activate"
python -m pip install --upgrade pip
pip install -r "$ROOT/backend/requirements.txt"

if [ ! -f "$ROOT/backend/.env" ]; then
  JWT_SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
  sed "s/CHANGE_ME_JWT_SECRET/${JWT_SECRET}/" "$ROOT/backend/.env.example" > "$ROOT/backend/.env"
  echo "Created backend/.env with a generated JWT_SECRET_KEY"
else
  echo "backend/.env already exists — leaving it unchanged"
fi

echo "==> Frontend npm packages"
if [ ! -f "$ROOT/frontend/.env" ]; then
  cp "$ROOT/frontend/.env.example" "$ROOT/frontend/.env"
  echo "Created frontend/.env from .env.example"
fi
npm install --prefix "$ROOT/frontend"

echo ""
echo "Setup complete."
echo "  Backend:  cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --app-dir ."
echo "  Frontend: cd frontend && npm run dev"
echo "Fill AWS_* in backend/.env before Slice 4 (S3 uploads)."
