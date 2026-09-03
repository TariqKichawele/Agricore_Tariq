#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
chmod +x "$ROOT/bin/"*.sh "$ROOT/bin/"*.py || true

echo "==> 1/3 API on EC2"
"$ROOT/bin/deploy-backend.sh" "$@"

echo "==> 2/3 CloudFront API origin + SPA routing"
# Prefer venv boto3 if setup.sh has been run
PYTHON="$ROOT/backend/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Run ./bin/setup.sh first so backend/.venv has boto3" >&2
  exit 1
fi
"$PYTHON" "$ROOT/bin/configure-cloudfront.py"

echo "==> 3/3 Frontend to S3"
"$PYTHON" "$ROOT/bin/deploy-frontend.py"

# shellcheck disable=SC1091
source "$ROOT/deploy/aws.env"
echo ""
echo "Live URL: ${CLOUDFRONT_URL}"
echo "Health:   ${CLOUDFRONT_URL}/health"
echo "If the UI is a blank page for a few minutes, CloudFront is still deploying."
