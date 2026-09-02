from pathlib import Path
from typing import NoReturn
from uuid import UUID, uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
PRESIGN_EXPIRES_SECONDS = 3600

_ALLOWED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".heic",
}
_ALLOWED_CONTENT_TYPES = {"text/plain", "application/pdf", "application/x-pdf"}


def _client():
    if not settings.s3_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="S3 is not configured",
        )
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def _raise_s3_error(exc: Exception) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Could not store the report file in S3",
    ) from exc


def validate_upload(filename: str | None, content_type: str | None) -> tuple[str, str]:
    name = Path(filename or "").name
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File name is required")
    suffix = Path(name).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allowed files: images, .txt, and .pdf",
        )
    ctype = (content_type or "").split(";")[0].strip().lower()
    if suffix in {".txt"}:
        allowed = ctype in _ALLOWED_CONTENT_TYPES or ctype.startswith("text/")
    elif suffix == ".pdf":
        allowed = ctype in _ALLOWED_CONTENT_TYPES or ctype == "application/octet-stream"
    else:
        allowed = ctype.startswith("image/") or ctype == "application/octet-stream"
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allowed files: images, .txt, and .pdf",
        )
    return name, ctype or "application/octet-stream"


def object_key(job_id: UUID, filename: str) -> str:
    safe = Path(filename).name.replace(" ", "_")
    return f"service-reports/{job_id}/{uuid4().hex}_{safe}"


def upload_report_file(job_id: UUID, upload: UploadFile, body: bytes) -> str:
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 10 MB limit",
        )
    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    filename, content_type = validate_upload(upload.filename, upload.content_type)
    key = object_key(job_id, filename)
    try:
        _client().put_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError) as exc:
        _raise_s3_error(exc)
    return key


def delete_object(key: str) -> None:
    try:
        _client().delete_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
    except (BotoCoreError, ClientError):
        return


def presigned_get_url(key: str) -> str:
    try:
        return _client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
            ExpiresIn=PRESIGN_EXPIRES_SECONDS,
        )
    except (BotoCoreError, ClientError) as exc:
        _raise_s3_error(exc)
