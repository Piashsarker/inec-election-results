"""Cloud storage service for result sheet images.

Provides an async S3-compatible storage backend.  Works with:
  - Cloudflare R2  (recommended — zero egress, free 10 GB)
  - AWS S3
  - Any S3-compatible store (Backblaze B2, MinIO, …)

When S3_BUCKET is not configured the service falls back to local
filesystem storage so development works without cloud credentials.

Deduplication
-------------
``object_exists(key)`` checks whether an object key is already in the
bucket before uploading, allowing callers to skip duplicate downloads.

Requirements: 2.1, 2.3
"""
from __future__ import annotations

import hashlib
import logging
import mimetypes
from pathlib import Path
from typing import Any

logger = logging.getLogger("inec_agent.storage")


class StorageService:
    """Async storage service that saves images to S3 / Cloudflare R2.

    Usage
    -----
    service = StorageService.from_settings(settings)

    # Upload a file already on disk
    url = await service.upload_file(local_path, object_key)

    # Upload raw bytes directly
    url = await service.upload_bytes(data, object_key, content_type="image/jpeg")

    The returned *url* is:
      - A public HTTPS URL when the bucket is publicly accessible, OR
      - A pre-signed URL valid for 7 days when the bucket is private.
    """

    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        region: str = "auto",
        public_url_base: str | None = None,
        use_local_fallback: bool = False,
        local_path: str = "./data/result_sheets",
    ):
        """Initialise the storage service.

        Args:
            bucket: S3 bucket / R2 bucket name
            endpoint_url: Custom endpoint for R2 / MinIO / B2
                          e.g. "https://<account_id>.r2.cloudflarestorage.com"
            access_key_id: AWS / R2 access key ID
            secret_access_key: AWS / R2 secret access key
            region: AWS region or "auto" for R2
            public_url_base: Optional public CDN base URL.
                             If set, returned URLs look like
                             "{public_url_base}/{object_key}".
                             If not set, pre-signed URLs are generated.
            use_local_fallback: If True, fall back to local FS when bucket is empty
            local_path: Local path used when falling back
        """
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region
        self.public_url_base = public_url_base.rstrip("/") if public_url_base else None
        self.use_local_fallback = use_local_fallback
        self.local_path = Path(local_path)

        self._cloud_enabled = bool(bucket and access_key_id and secret_access_key)

        if self._cloud_enabled:
            logger.info(
                f"StorageService: cloud storage enabled "
                f"(bucket={bucket}, endpoint={endpoint_url or 'AWS S3'})"
            )
        else:
            logger.warning(
                "StorageService: S3 credentials not configured — "
                "falling back to local filesystem storage"
            )
            self.local_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_settings(cls, settings: Any) -> StorageService:
        """Create a StorageService from app Settings.

        Args:
            settings: App Settings object with a `.storage` sub-config

        Returns:
            Configured StorageService instance
        """
        s = settings.storage
        return cls(
            bucket=s.bucket,
            endpoint_url=s.endpoint_url or None,
            access_key_id=s.access_key_id or None,
            secret_access_key=s.secret_access_key or None,
            region=s.region,
            public_url_base=s.public_url_base or None,
            use_local_fallback=True,
            local_path=settings.scraping.storage_path,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def object_exists(self, object_key: str) -> bool:
        """Check whether an object already exists in the bucket.

        Uses a lightweight HeadObject call — no data is transferred.

        Args:
            object_key: Key to check inside the bucket

        Returns:
            True if the object exists, False otherwise
        """
        if not self._cloud_enabled:
            return (self.local_path / object_key).exists()

        try:
            import aiobotocore.session  # type: ignore[import]

            session = aiobotocore.session.get_session()
            async with session.create_client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
            ) as client:
                await client.head_object(Bucket=self.bucket, Key=object_key)
                return True
        except Exception:
            # ClientError with 404 means key doesn't exist
            return False

    @staticmethod
    def content_hash(data: bytes) -> str:
        """Return the SHA-256 hex digest of ``data``.

        Used to detect byte-for-byte identical images even when their
        URLs or filenames differ.
        """
        return hashlib.sha256(data).hexdigest()

    async def upload_file(
        self,
        local_path: str | Path,
        object_key: str,
        skip_if_exists: bool = True,
    ) -> tuple[str, bool]:
        """Upload a file from disk to cloud storage.

        Args:
            local_path: Path to the local file
            object_key: Destination key inside the bucket
            skip_if_exists: If True, return existing URL without re-uploading

        Returns:
            Tuple of (url, was_skipped).
            ``was_skipped`` is True when the file already existed in storage.
        """
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"File not found: {local_path}")

        if skip_if_exists and await self.object_exists(object_key):
            logger.info(f"Skipping upload — already exists: {object_key}")
            url = self._build_url(object_key)
            return url, True

        data = local_path.read_bytes()
        content_type = self._guess_content_type(local_path.name)
        url = await self.upload_bytes(data, object_key, content_type, skip_if_exists=False)
        return url, False

    async def upload_bytes(
        self,
        data: bytes,
        object_key: str,
        content_type: str = "application/octet-stream",
        skip_if_exists: bool = True,
    ) -> str:
        """Upload raw bytes to cloud storage.

        Args:
            data: File content
            object_key: Destination key inside the bucket
            content_type: MIME type of the content
            skip_if_exists: If True, skip upload when the key already exists

        Returns:
            URL to access the uploaded file
        """
        if skip_if_exists and await self.object_exists(object_key):
            logger.info(f"Skipping upload — already exists: {object_key}")
            return self._build_url(object_key)

        if not self._cloud_enabled:
            return self._save_locally(data, object_key)

        try:
            return await self._upload_to_s3(data, object_key, content_type)
        except Exception as exc:
            logger.error(f"Cloud upload failed for {object_key}: {exc}")
            if self.use_local_fallback:
                logger.warning("Falling back to local filesystem")
                return self._save_locally(data, object_key)
            raise

    async def get_presigned_url(self, object_key: str, expires_in: int = 604800) -> str:
        """Generate a pre-signed URL for a stored object.

        Args:
            object_key: Key of the object in the bucket
            expires_in: URL expiry in seconds (default 7 days)

        Returns:
            Pre-signed URL string
        """
        if not self._cloud_enabled:
            # Local files — return relative path
            return f"/data/result_sheets/{object_key}"

        try:
            import aiobotocore.session  # type: ignore[import]

            session = aiobotocore.session.get_session()
            async with session.create_client(
                "s3",
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
            ) as client:
                url: str = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": object_key},
                    ExpiresIn=expires_in,
                )
                return url
        except Exception as exc:
            logger.error(f"Failed to generate pre-signed URL for {object_key}: {exc}")
            raise

    def is_cloud_enabled(self) -> bool:
        """Return True if cloud storage is configured."""
        return self._cloud_enabled

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_url(self, object_key: str) -> str:
        """Build a URL for an already-uploaded object without a network call.

        Returns a public URL when public_url_base is set, otherwise a
        placeholder that callers can swap for a pre-signed URL on demand.
        """
        if self.public_url_base:
            return f"{self.public_url_base}/{object_key}"
        if self._cloud_enabled:
            # Return a deterministic endpoint URL — callers should call
            # get_presigned_url() if they need a publicly accessible link.
            return f"{self.endpoint_url}/{self.bucket}/{object_key}"
        return str(self.local_path / object_key)

    async def _upload_to_s3(
        self, data: bytes, object_key: str, content_type: str
    ) -> str:
        """Perform the actual upload via aiobotocore."""
        import aiobotocore.session  # type: ignore[import]

        session = aiobotocore.session.get_session()
        async with session.create_client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        ) as client:
            await client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=data,
                ContentType=content_type,
            )

        logger.info(f"Uploaded {len(data):,} bytes → s3://{self.bucket}/{object_key}")

        # Return public URL or pre-signed URL
        if self.public_url_base:
            return f"{self.public_url_base}/{object_key}"

        # Generate short-lived pre-signed URL (7 days)
        return await self.get_presigned_url(object_key)

    def _save_locally(self, data: bytes, object_key: str) -> str:
        """Save bytes to the local fallback path.

        Mirrors the object_key directory structure under local_path.
        """
        dest = self.local_path / object_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        logger.info(f"Saved locally: {dest} ({len(data):,} bytes)")
        # Return a relative path that can be served or referenced later
        return str(dest)

    @staticmethod
    def _guess_content_type(filename: str) -> str:
        """Guess MIME type from filename."""
        mime, _ = mimetypes.guess_type(filename)
        return mime or "application/octet-stream"
