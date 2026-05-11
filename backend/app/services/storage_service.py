"""
MinIO Object Storage Service
Stores PoC screenshots, HTTP traces, and evidence files
"""

import logging
import os
import io
import socket
from typing import Dict, Any, Optional, BinaryIO
from pathlib import Path
from datetime import timedelta

try:
    from minio import Minio  # type: ignore
    from minio.error import S3Error  # type: ignore
except ImportError:
    Minio = None
    S3Error = None

try:
    import urllib3  # type: ignore
except ImportError:
    urllib3 = None

logger = logging.getLogger(__name__)


class StorageService:
    """
    MinIO (S3-compatible) object storage for evidence files
    
    Buckets:
    - rakshaidb-screenshots: PoC screenshots
    - rakshaidb-traces: HTTP request/response logs
    - rakshaidb-reports: Generated PDF/Word/Excel reports
    - rakshaidb-raw: Raw tool outputs
    """
    
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "rakshaidb")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "rakshaidb_minio_pass")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        self.client: Optional[Any] = None
        self.buckets = [
            "rakshaidb-screenshots",
            "rakshaidb-traces",
            "rakshaidb-reports",
            "rakshaidb-raw"
        ]
        
    async def initialize(self):
        """Initialize MinIO client and create buckets"""
        try:
            if Minio is None:
                logger.warning("MinIO dependency not installed; using local storage fallback")
                self.client = None
                return

            # Fast pre-check so we do not block report generation for long retries.
            host, port = self._parse_endpoint(self.endpoint)
            if not self._is_port_open(host, port, timeout=1.0):
                logger.warning(f"MinIO unavailable at {self.endpoint}; using local storage fallback")
                self.client = None
                return

            minio_kwargs = {
                "access_key": self.access_key,
                "secret_key": self.secret_key,
                "secure": self.secure,
            }

            # Use short HTTP timeouts and no retries to keep startup responsive.
            if urllib3 is not None:
                minio_kwargs["http_client"] = urllib3.PoolManager(
                    timeout=urllib3.Timeout(connect=1.0, read=2.0),
                    retries=False,
                )

            self.client = Minio(self.endpoint, **minio_kwargs)

            # Create buckets if they don't exist (best effort)
            for bucket in self.buckets:
                try:
                    if not self.client.bucket_exists(bucket):
                        self.client.make_bucket(bucket)
                        logger.info(f"Created bucket: {bucket}")
                except Exception as e:
                    logger.warning(f"Could not check/create bucket {bucket}: {e}")

            logger.info(f"Initialized MinIO storage at {self.endpoint}")

        except Exception as e:
            logger.error(f"Failed to initialize MinIO: {e}")
            # Continue without storage - will fall back to local files
            self.client = None

    def _parse_endpoint(self, endpoint: str) -> tuple[str, int]:
        """Parse MinIO endpoint into host and port."""
        if ":" not in endpoint:
            return endpoint, 443 if self.secure else 80

        host, port_str = endpoint.rsplit(":", 1)
        try:
            return host, int(port_str)
        except ValueError:
            return host, 443 if self.secure else 80

    def _is_port_open(self, host: str, port: int, timeout: float = 1.0) -> bool:
        """Fast TCP check for service availability."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False
    
    async def upload_screenshot(
        self,
        scan_id: str,
        finding_id: str,
        screenshot_data: bytes,
        filename: str = "screenshot.png"
    ) -> str:
        """
        Upload PoC screenshot
        
        Args:
            scan_id: Scan identifier
            finding_id: Finding identifier
            screenshot_data: PNG image bytes
            filename: Filename
            
        Returns:
            Object URL
        """
        if not self.client:
            return await self._save_local(screenshot_data, f"{scan_id}/{finding_id}/{filename}")
        
        try:
            object_name = f"{scan_id}/{finding_id}/{filename}"
            
            self.client.put_object(
                bucket_name="rakshaidb-screenshots",
                object_name=object_name,
                data=io.BytesIO(screenshot_data),
                length=len(screenshot_data),
                content_type="image/png"
            )
            
            # Generate presigned URL (valid for 7 days)
            url = self.client.presigned_get_object(
                bucket_name="rakshaidb-screenshots",
                object_name=object_name,
                expires=timedelta(days=7)
            )
            
            logger.info(f"Uploaded screenshot: {object_name}")
            return url
            
        except S3Error as e:
            logger.error(f"Failed to upload screenshot: {e}")
            return await self._save_local(screenshot_data, f"{scan_id}/{finding_id}/{filename}")
    
    async def upload_http_trace(
        self,
        scan_id: str,
        finding_id: str,
        trace_data: Dict[str, Any]
    ) -> str:
        """Upload HTTP request/response trace"""
        if not self.client:
            import json
            return await self._save_local(
                json.dumps(trace_data, indent=2).encode(),
                f"{scan_id}/{finding_id}/http_trace.json"
            )
        
        try:
            import json
            object_name = f"{scan_id}/{finding_id}/http_trace.json"
            trace_json = json.dumps(trace_data, indent=2).encode()
            
            self.client.put_object(
                bucket_name="rakshaidb-traces",
                object_name=object_name,
                data=io.BytesIO(trace_json),
                length=len(trace_json),
                content_type="application/json"
            )
            
            url = self.client.presigned_get_object(
                bucket_name="rakshaidb-traces",
                object_name=object_name,
                expires=timedelta(days=7)
            )
            
            return url
            
        except S3Error as e:
            logger.error(f"Failed to upload HTTP trace: {e}")
            return ""
    
    async def upload_report(
        self,
        scan_id: str,
        report_data: bytes,
        format: str = "pdf"
    ) -> str:
        """
        Upload generated report
        
        Args:
            scan_id: Scan identifier
            report_data: Report file bytes
            format: File format (pdf, docx, xlsx)
            
        Returns:
            Object URL
        """
        if not self.client:
            return await self._save_local(report_data, f"{scan_id}/report.{format}")
        
        try:
            object_name = f"{scan_id}/report.{format}"
            
            content_types = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
            
            self.client.put_object(
                bucket_name="rakshaidb-reports",
                object_name=object_name,
                data=io.BytesIO(report_data),
                length=len(report_data),
                content_type=content_types.get(format, "application/octet-stream")
            )
            
            url = self.client.presigned_get_object(
                bucket_name="rakshaidb-reports",
                object_name=object_name,
                expires=timedelta(days=30)
            )
            
            logger.info(f"Uploaded report: {object_name}")
            return url
            
        except S3Error as e:
            logger.error(f"Failed to upload report: {e}")
            return ""
    
    async def upload_raw_output(
        self,
        scan_id: str,
        tool_name: str,
        output_data: bytes
    ) -> str:
        """Upload raw tool output for debugging"""
        if not self.client:
            return await self._save_local(output_data, f"{scan_id}/raw/{tool_name}.txt")
        
        try:
            object_name = f"{scan_id}/raw/{tool_name}_{id(output_data)}.txt"
            
            self.client.put_object(
                bucket_name="rakshaidb-raw",
                object_name=object_name,
                data=io.BytesIO(output_data),
                length=len(output_data),
                content_type="text/plain"
            )
            
            return object_name
            
        except S3Error as e:
            logger.error(f"Failed to upload raw output: {e}")
            return ""
    
    async def _save_local(self, data: bytes, path: str) -> str:
        """Fallback: save file locally"""
        try:
            local_dir = Path("/app/storage") / Path(path).parent
            local_dir.mkdir(parents=True, exist_ok=True)
            
            local_file = local_dir / Path(path).name
            local_file.write_bytes(data)
            
            logger.info(f"Saved locally: {local_file}")
            return str(local_file)
            
        except Exception as e:
            logger.error(f"Failed to save locally: {e}")
            return ""


# Singleton instance
_storage_service = None

async def get_storage_service() -> StorageService:
    """Get global storage service instance"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
        await _storage_service.initialize()
    return _storage_service
