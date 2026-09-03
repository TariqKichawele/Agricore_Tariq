#!/usr/bin/env python3
"""Build the Vite app, upload to S3, and invalidate CloudFront."""

from __future__ import annotations

import mimetypes
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import boto3
from dotenv import dotenv_values

DIST = ROOT / "frontend" / "dist"


def load_aws_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (ROOT / "deploy" / "aws.env").read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip().strip('"')
    return values


def content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed:
        return guessed
    suffix = path.suffix.lower()
    mapping = {
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".css": "text/css",
        ".html": "text/html",
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".map": "application/json",
    }
    return mapping.get(suffix, "application/octet-stream")


def cache_control(path: Path) -> str:
    if path.name in {"index.html"} or path.suffix == ".html":
        return "no-cache"
    return "public, max-age=31536000, immutable"


def main() -> None:
    aws = load_aws_env()
    local = dotenv_values(ROOT / "backend" / ".env")
    bucket = aws["FRONTEND_S3_BUCKET"]
    dist_id = aws["CLOUDFRONT_DISTRIBUTION_ID"]
    session_kwargs = {
        "aws_access_key_id": (local.get("AWS_ACCESS_KEY_ID") or "").strip(),
        "aws_secret_access_key": (local.get("AWS_SECRET_ACCESS_KEY") or "").strip(),
        "region_name": aws.get("AWS_REGION") or "us-east-1",
    }
    if not session_kwargs["aws_access_key_id"]:
        raise SystemExit("AWS keys missing in backend/.env")

    env_file = ROOT / "frontend" / ".env"
    env_file.write_text("VITE_API_BASE_URL=/api/v1\nVITE_API_HEALTH_URL=/health\n")

    subprocess.run(["npm", "ci"], cwd=ROOT / "frontend", check=True)
    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not DIST.exists():
        raise SystemExit("frontend/dist missing after build")

    s3 = boto3.client("s3", **session_kwargs)
    uploaded = 0
    for path in DIST.rglob("*"):
        if not path.is_file():
            continue
        key = str(path.relative_to(DIST)).replace("\\", "/")
        extra = {
            "ContentType": content_type(path),
            "CacheControl": cache_control(path),
        }
        s3.upload_file(str(path), bucket, key, ExtraArgs=extra)
        uploaded += 1
    print(f"Uploaded {uploaded} files to s3://{bucket}")

    cf = boto3.client("cloudfront", **session_kwargs)
    cf.create_invalidation(
        DistributionId=dist_id,
        InvalidationBatch={
            "Paths": {"Quantity": 1, "Items": ["/*"]},
            "CallerReference": str(uuid.uuid4()),
        },
    )
    print(f"Invalidated CloudFront {dist_id}")
    print(aws["CLOUDFRONT_URL"])


if __name__ == "__main__":
    main()
