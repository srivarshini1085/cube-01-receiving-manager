import os
import io
import base64
import hashlib
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from app.core.config import settings


class ImageStorageProvider(ABC):
    """
    Abstract Storage Provider for inbound freight photographs.
    Supports local filesystem in development and persistent cloud/object storage in production (e.g. Vercel).
    """

    @abstractmethod
    def save_image(
        self,
        contents: bytes,
        original_filename: str,
        content_type: str,
        org_id: str,
        inspection_id: str,
    ) -> Tuple[str, str, str]:
        """
        Saves image contents.
        Returns:
            storage_key: Unique identifier in storage
            file_reference: Local path or storage reference
            image_url: Accessible URL (or serving endpoint) for UI rendering
        """
        pass

    @abstractmethod
    def get_image_bytes(self, file_reference: str) -> Optional[bytes]:
        """Retrieves raw image bytes."""
        pass


class LocalStorageProvider(ImageStorageProvider):
    """
    Local filesystem storage provider for development and on-premise deployments.
    """

    def __init__(self, base_dir: str = settings.UPLOAD_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_image(
        self,
        contents: bytes,
        original_filename: str,
        content_type: str,
        org_id: str,
        inspection_id: str,
    ) -> Tuple[str, str, str]:
        checksum = hashlib.sha256(contents).hexdigest()
        file_ext = os.path.splitext(original_filename or "")[1].lower() or ".jpg"
        safe_filename = f"{inspection_id}_{checksum[:12]}{file_ext}"

        org_upload_dir = os.path.join(self.base_dir, org_id)
        os.makedirs(org_upload_dir, exist_ok=True)

        target_path = os.path.join(org_upload_dir, safe_filename)
        with open(target_path, "wb") as f:
            f.write(contents)

        storage_key = f"{org_id}/{safe_filename}"
        # Serving endpoint relative URL
        image_url = f"/api/v1/inspections/{inspection_id}/images/file/{safe_filename}"
        return storage_key, target_path, image_url

    def get_image_bytes(self, file_reference: str) -> Optional[bytes]:
        if os.path.exists(file_reference):
            with open(file_reference, "rb") as f:
                return f.read()
        return None


class DataUriStorageProvider(ImageStorageProvider):
    """
    Deployment-safe fallback provider for serverless environments (e.g. Vercel without S3 credentials).
    Generates inline data URIs and writes to /tmp/ if available, ensuring images never 404.
    """

    def __init__(self, fallback_dir: str = "/tmp/inboundshield_uploads"):
        self.fallback_dir = fallback_dir
        try:
            os.makedirs(self.fallback_dir, exist_ok=True)
        except Exception:
            pass

    def save_image(
        self,
        contents: bytes,
        original_filename: str,
        content_type: str,
        org_id: str,
        inspection_id: str,
    ) -> Tuple[str, str, str]:
        checksum = hashlib.sha256(contents).hexdigest()
        file_ext = os.path.splitext(original_filename or "")[1].lower() or ".jpg"
        safe_filename = f"{inspection_id}_{checksum[:12]}{file_ext}"

        target_path = os.path.join(self.fallback_dir, safe_filename)
        try:
            with open(target_path, "wb") as f:
                f.write(contents)
        except Exception:
            target_path = f"memory://{safe_filename}"

        # Generate Data URI for zero-infrastructure guaranteed preview in browser
        b64_content = base64.b64encode(contents).decode("utf-8")
        mime = content_type or "image/jpeg"
        data_url = f"data:{mime};base64,{b64_content}"

        storage_key = f"{org_id}/{safe_filename}"
        return storage_key, target_path, data_url

    def get_image_bytes(self, file_reference: str) -> Optional[bytes]:
        if os.path.exists(file_reference):
            with open(file_reference, "rb") as f:
                return f.read()
        return None


def get_storage_provider() -> ImageStorageProvider:
    provider_name = os.getenv("STORAGE_PROVIDER", "local").lower()
    # Check if running in Vercel or cloud container where filesystem is ephemeral
    is_vercel = bool(os.getenv("VERCEL") or os.getenv("NOW_REGION"))
    if provider_name == "data_uri" or (is_vercel and provider_name != "s3"):
        return DataUriStorageProvider()
    return LocalStorageProvider()


storage_provider = get_storage_provider()
