from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import mimetypes
import re
from urllib.parse import quote, urlparse

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


ASSET_ROUTE_PREFIX = "/api/assets"


@dataclass(frozen=True)
class StoredObject:
    key: str
    bucket: str
    url: str
    content_type: str
    size: int


@dataclass(frozen=True)
class ObjectBytes:
    key: str
    data: bytes
    content_type: str


class ObjectStorageError(RuntimeError):
    pass


_client: Minio | None = None
_bucket_ready = False


def configured() -> bool:
    return settings.object_storage.configured


def status() -> dict:
    return {
        "configured": configured(),
        "endpoint": settings.object_storage.endpoint,
        "bucket": settings.object_storage.bucket,
        "region": settings.object_storage.region,
        "assetRoutePrefix": ASSET_ROUTE_PREFIX,
        "publicApiBaseUrl": settings.object_storage.public_api_base_url,
    }


def store_product_image(
    *,
    provider_id: str,
    keyword: str,
    source_product_id: str,
    data: bytes,
    content_type: str,
) -> StoredObject:
    if not data:
        raise ObjectStorageError("empty object data")

    normalized_content_type = _normalize_content_type(content_type)
    key = _product_image_key(
        provider_id=provider_id,
        keyword=keyword,
        source_product_id=source_product_id,
        content_type=normalized_content_type,
    )
    _ensure_bucket()
    _get_client().put_object(
        settings.object_storage.bucket,
        key,
        BytesIO(data),
        length=len(data),
        content_type=normalized_content_type,
    )
    return StoredObject(
        key=key,
        bucket=settings.object_storage.bucket,
        url=asset_url(key),
        content_type=normalized_content_type,
        size=len(data),
    )


def read_object(key: str) -> ObjectBytes:
    clean_key = _validate_key(key)
    _ensure_bucket()
    client = _get_client()
    try:
        stat = client.stat_object(settings.object_storage.bucket, clean_key)
        response = client.get_object(settings.object_storage.bucket, clean_key)
        try:
            data = response.read()
        finally:
            response.close()
            response.release_conn()
    except S3Error as exc:
        raise ObjectStorageError(str(exc)) from exc

    return ObjectBytes(
        key=clean_key,
        data=data,
        content_type=stat.content_type or "application/octet-stream",
    )


def asset_url(key: str) -> str:
    encoded_key = quote(_validate_key(key), safe="/")
    return f"{settings.object_storage.public_api_base_url}{ASSET_ROUTE_PREFIX}/{encoded_key}"


def _get_client() -> Minio:
    global _client
    if not configured():
        raise ObjectStorageError("object storage is not configured")
    if _client is None:
        endpoint, secure = _parse_endpoint(settings.object_storage.endpoint)
        _client = Minio(
            endpoint,
            access_key=settings.object_storage.access_key,
            secret_key=settings.object_storage.secret_key,
            secure=secure,
            region=settings.object_storage.region,
        )
    return _client


def _ensure_bucket() -> None:
    global _bucket_ready
    if _bucket_ready:
        return
    client = _get_client()
    bucket = settings.object_storage.bucket
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket, location=settings.object_storage.region)
    except S3Error as exc:
        if exc.code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
            raise ObjectStorageError(str(exc)) from exc
    _bucket_ready = True


def _parse_endpoint(endpoint: str) -> tuple[str, bool]:
    parsed = urlparse(endpoint)
    if parsed.scheme:
        return (parsed.netloc or parsed.path).rstrip("/"), parsed.scheme == "https"
    return endpoint.rstrip("/"), False


def _product_image_key(*, provider_id: str, keyword: str, source_product_id: str, content_type: str) -> str:
    extension = mimetypes.guess_extension(content_type) or ".bin"
    if extension == ".jpe":
        extension = ".jpg"
    return "/".join(
        [
            "product-images",
            _slug(provider_id),
            _slug(keyword),
            f"{_slug(source_product_id)}{extension}",
        ]
    )


def _normalize_content_type(value: str) -> str:
    content_type = value.split(";", 1)[0].strip().lower()
    if content_type in {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}:
        return "image/jpeg" if content_type == "image/jpg" else content_type
    return "application/octet-stream"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower()).strip("-._")
    return slug or "unknown"


def _validate_key(key: str) -> str:
    clean = key.strip()
    if not clean or clean.startswith("/") or any(part in {"", ".", ".."} for part in clean.split("/")):
        raise ObjectStorageError("invalid object key")
    return clean
