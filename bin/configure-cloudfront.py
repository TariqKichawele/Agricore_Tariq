#!/usr/bin/env python3
"""Point CloudFront at the EC2 API and rewrite SPA routes to index.html."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import boto3
from botocore.exceptions import ClientError
from dotenv import dotenv_values

CACHING_DISABLED = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
ALL_VIEWER_EXCEPT_HOST = "33f36d7e-f396-46d9-90e0-52428a34d9dc"
FUNCTION_NAME = "agricore-spa-rewrite"
API_ORIGIN_ID = "agricore-api"

ALLOWED_METHODS = {
    "Quantity": 7,
    "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
    "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]},
}


def load_aws_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (ROOT / "deploy" / "aws.env").read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip().strip('"')
    return values


def credentials() -> dict[str, str]:
    local = dotenv_values(ROOT / "backend" / ".env")
    aws = load_aws_env()
    return {
        "aws_access_key_id": (local.get("AWS_ACCESS_KEY_ID") or "").strip(),
        "aws_secret_access_key": (local.get("AWS_SECRET_ACCESS_KEY") or "").strip(),
        "region_name": aws.get("AWS_REGION") or "us-east-1",
    }


def ensure_function(cf, code: str) -> str:
    encoded = code.encode("utf-8")
    config = {"Comment": "SPA fallback to index.html", "Runtime": "cloudfront-js-2.0"}
    try:
        created = cf.create_function(Name=FUNCTION_NAME, FunctionConfig=config, FunctionCode=encoded)
        etag = created["ETag"]
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "FunctionAlreadyExists":
            raise
        desc = cf.describe_function(Name=FUNCTION_NAME)
        updated = cf.update_function(
            Name=FUNCTION_NAME,
            IfMatch=desc["ETag"],
            FunctionConfig=config,
            FunctionCode=encoded,
        )
        etag = updated["ETag"]
    published = cf.publish_function(Name=FUNCTION_NAME, IfMatch=etag)
    return published["FunctionSummary"]["FunctionMetadata"]["FunctionARN"]


def origin_exists(config: dict, origin_id: str) -> bool:
    return any(item["Id"] == origin_id for item in config["Origins"]["Items"])


def behavior_exists(config: dict, pattern: str) -> bool:
    items = (config.get("CacheBehaviors") or {}).get("Items") or []
    return any(item.get("PathPattern") == pattern for item in items)


def api_behavior(origin_id: str, default_behavior: dict) -> dict:
    behavior = {
        "PathPattern": "",
        "TargetOriginId": origin_id,
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": ALLOWED_METHODS,
        "Compress": True,
        "SmoothStreaming": False,
        "FieldLevelEncryptionId": "",
        "TrustedSigners": {"Enabled": False, "Quantity": 0},
        "TrustedKeyGroups": {"Enabled": False, "Quantity": 0},
        "LambdaFunctionAssociations": {"Quantity": 0, "Items": []},
        "FunctionAssociations": {"Quantity": 0, "Items": []},
    }
    if "GrpcConfig" in default_behavior:
        behavior["GrpcConfig"] = {"Enabled": False}
    if "CachePolicyId" in default_behavior:
        behavior["CachePolicyId"] = CACHING_DISABLED
        behavior["OriginRequestPolicyId"] = ALL_VIEWER_EXCEPT_HOST
    else:
        behavior["ForwardedValues"] = {
            "QueryString": True,
            "Cookies": {"Forward": "all"},
            "Headers": {"Quantity": 1, "Items": ["*"]},
            "QueryStringCacheKeys": {"Quantity": 0},
        }
        behavior["MinTTL"] = 0
        behavior["DefaultTTL"] = 0
        behavior["MaxTTL"] = 0
    return behavior


def main() -> None:
    aws = load_aws_env()
    dist_id = aws["CLOUDFRONT_DISTRIBUTION_ID"]
    origin_domain = aws["EC2_PUBLIC_DNS"]
    creds = credentials()
    if not creds["aws_access_key_id"] or not creds["aws_secret_access_key"]:
        raise SystemExit("AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY missing in backend/.env")

    cf = boto3.client("cloudfront", **creds)
    spa_arn = ensure_function(cf, (ROOT / "deploy" / "spa-rewrite.js").read_text())

    resp = cf.get_distribution_config(Id=dist_id)
    etag = resp["ETag"]
    config = resp["DistributionConfig"]
    changed = False

    config["Enabled"] = True
    if config.get("DefaultRootObject") != "index.html":
        config["DefaultRootObject"] = "index.html"
        changed = True

    if not origin_exists(config, API_ORIGIN_ID):
        config["Origins"]["Items"].append(
            {
                "Id": API_ORIGIN_ID,
                "DomainName": origin_domain,
                "OriginPath": "",
                "CustomHeaders": {"Quantity": 0, "Items": []},
                "CustomOriginConfig": {
                    "HTTPPort": 8000,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only",
                    "OriginSslProtocols": {"Quantity": 1, "Items": ["TLSv1.2"]},
                    "OriginReadTimeout": 60,
                    "OriginKeepaliveTimeout": 5,
                },
                "ConnectionAttempts": 3,
                "ConnectionTimeout": 10,
            }
        )
        config["Origins"]["Quantity"] = len(config["Origins"]["Items"])
        changed = True

    default = config["DefaultCacheBehavior"]
    desired_fn = {
        "Quantity": 1,
        "Items": [{"FunctionARN": spa_arn, "EventType": "viewer-request"}],
    }
    if default.get("FunctionAssociations") != desired_fn:
        default["FunctionAssociations"] = desired_fn
        changed = True

    if "CacheBehaviors" not in config or config["CacheBehaviors"] is None:
        config["CacheBehaviors"] = {"Quantity": 0, "Items": []}
    if "Items" not in config["CacheBehaviors"] or config["CacheBehaviors"]["Items"] is None:
        config["CacheBehaviors"]["Items"] = []

    for pattern in ("/api/*", "/health"):
        if behavior_exists(config, pattern):
            continue
        item = api_behavior(API_ORIGIN_ID, default)
        item["PathPattern"] = pattern
        config["CacheBehaviors"]["Items"].append(item)
        changed = True
    config["CacheBehaviors"]["Quantity"] = len(config["CacheBehaviors"]["Items"])

    if not changed:
        print(f"CloudFront {dist_id} already has API origin and behaviors")
        return

    cf.update_distribution(Id=dist_id, IfMatch=etag, DistributionConfig=config)
    print(f"Updated CloudFront {dist_id}. Waiting until Deployed (often 5–15 minutes)...")
    waiter = cf.get_waiter("distribution_deployed")
    waiter.wait(Id=dist_id, WaiterConfig={"Delay": 30, "MaxAttempts": 40})
    print("CloudFront status: Deployed")


if __name__ == "__main__":
    main()
