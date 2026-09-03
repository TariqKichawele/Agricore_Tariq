#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/deploy/aws.env"

SEED=0
if [[ "${1:-}" == "--seed" ]]; then
  SEED=1
fi

KEY="${AGRICORE_SSH_KEY:-}"
if [[ -z "$KEY" ]]; then
  for candidate in "$HOME/.ssh/agricore-key.pem" "$HOME/Downloads/agricore-key.pem"; do
    if [[ -f "$candidate" ]]; then
      KEY="$candidate"
      break
    fi
  done
fi
if [[ -z "$KEY" || ! -f "$KEY" ]]; then
  echo "SSH key not found. Set AGRICORE_SSH_KEY to agricore-key.pem" >&2
  exit 1
fi
chmod 400 "$KEY" 2>/dev/null || true

SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes)
SCP=(scp -i "$KEY" -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes)
HOST="${EC2_SSH_USER}@${EC2_PUBLIC_DNS}"
REMOTE="${EC2_REMOTE_DIR:-/opt/agricore}"

if [[ ! -f "$ROOT/backend/.env.production" ]]; then
  echo "==> Building backend/.env.production"
  PYTHON="$ROOT/backend/.venv/bin/python"
  if [[ ! -x "$PYTHON" ]]; then
    PYTHON=python3
  fi
  "$PYTHON" "$ROOT/bin/make-production-env.py"
fi

echo "==> Preparing ${HOST}:${REMOTE}"
"${SSH[@]}" "$HOST" "sudo mkdir -p ${REMOTE}/backend && sudo chown -R ${EC2_SSH_USER}:${EC2_SSH_USER} ${REMOTE}"

echo "==> Installing packages on EC2"
"${SSH[@]}" "$HOST" 'sudo dnf install -y python3.11 python3.11-pip python3.11-devel gcc rsync >/dev/null'

echo "==> Syncing backend"
rsync -az --delete \
  -e "ssh -i ${KEY} -o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes" \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.env' \
  --exclude '.env.production' \
  "$ROOT/backend/" "$HOST:${REMOTE}/backend/"

"${SCP[@]}" "$ROOT/backend/.env.production" "$HOST:${REMOTE}/backend/.env"
"${SCP[@]}" "$ROOT/deploy/agricore-api.service" "$HOST:/tmp/agricore-api.service"

echo "==> Python venv, migrations, systemd"
"${SSH[@]}" "$HOST" "export SEED=${SEED}; export REMOTE=${REMOTE}; bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail
cd "$REMOTE/backend"
rm -rf .venv
python3.11 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
alembic upgrade head
if [[ "${SEED}" == "1" ]]; then
  python -m app.seed --reset
fi
sudo cp /tmp/agricore-api.service /etc/systemd/system/agricore-api.service
sudo systemctl daemon-reload
sudo systemctl enable agricore-api
sudo systemctl restart agricore-api
sleep 2
systemctl is-active agricore-api
curl -fsS http://127.0.0.1:8000/health
echo
REMOTE_SCRIPT

echo "API on EC2: http://${EC2_PUBLIC_DNS}:8000/health"
echo "After CloudFront is configured: ${CLOUDFRONT_URL}/health"
