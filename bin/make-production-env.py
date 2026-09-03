#!/usr/bin/env python3
"""Build backend/.env.production from local backend/.env + deploy/aws.env."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import dotenv_values  # noqa: E402

KEYS = [
    "DATABASE_URL",
    "JWT_SECRET_KEY",
    "JWT_ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "CORS_ORIGINS",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION",
    "AWS_S3_BUCKET",
    "BOOTSTRAP_ADMIN_EMAIL",
    "BOOTSTRAP_ADMIN_PASSWORD",
    "BOOTSTRAP_ADMIN_NAME",
]


def load_aws_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip().strip('"')
    return values


def main() -> None:
    local_env = ROOT / "backend" / ".env"
    aws_env_path = ROOT / "deploy" / "aws.env"
    out_path = ROOT / "backend" / ".env.production"

    if not local_env.exists():
        raise SystemExit("backend/.env is missing")
    if not aws_env_path.exists():
        raise SystemExit("deploy/aws.env is missing")

    local = {k: (v or "").strip() for k, v in dotenv_values(local_env).items()}
    aws = load_aws_env(aws_env_path)

    password = local.get("RDS_PASSWORD") or ""
    user = aws.get("RDS_USERNAME", "agricore")
    host = aws.get("RDS_ENDPOINT", "")
    port = aws.get("RDS_PORT", "5432")
    db_name = aws.get("RDS_DB_NAME", "agricore")
    if not password:
        raise SystemExit("Set RDS_PASSWORD in backend/.env (RDS master password)")
    if not host:
        raise SystemExit("RDS_ENDPOINT missing from deploy/aws.env")

    database_url = (
        f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{db_name}"
    )

    cors = (aws.get("CLOUDFRONT_URL") or "").rstrip("/")
    if not cors.startswith("https://"):
        raise SystemExit("CLOUDFRONT_URL in deploy/aws.env must be https://...")

    values = {key: local.get(key, "") for key in KEYS}
    values["DATABASE_URL"] = database_url
    values["CORS_ORIGINS"] = cors
    values["AWS_REGION"] = aws.get("AWS_REGION") or values.get("AWS_REGION") or "us-east-1"
    values.setdefault("JWT_ALGORITHM", "HS256")
    values.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "480")

    missing = [
        key
        for key in (
            "JWT_SECRET_KEY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_S3_BUCKET",
        )
        if not values.get(key)
    ]
    if missing:
        raise SystemExit(f"Fill these in backend/.env: {', '.join(missing)}")

    lines = [f"{key}={values[key]}" for key in KEYS]
    out_path.write_text("\n".join(lines) + "\n")
    print(f"Wrote {out_path} (RDS host {host}, CORS {cors})")


if __name__ == "__main__":
    main()
