"""
Simple synchronous discovery service
Runs endpoint discovery without async/threading issues
"""
import logging
import requests
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Scan, Endpoint, ScanStatus, Vulnerability, VulnerabilitySeverity
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

class SimpleDiscoveryService:
    """Synchronous discovery service that works in threads"""
    
    @staticmethod
    def discover_endpoints(scan_id: str, target_url: str) -> dict:
        """
        Discover endpoints from target URL
        Returns dict with discovered endpoints
        """
        db = SessionLocal()
        try:
            scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
            if not scan:
                return {"success": False, "error": "Scan not found"}
            
            discovered_urls = set()
            discovered_urls.add(target_url)
            
            parsed_target = urlparse(target_url)
            
            # Phase 1: HTTP probe
            logger.info(f"[{scan_id}] HTTP probing {target_url}")
            try:
                response = requests.get(target_url, timeout=15, allow_redirects=True)
                logger.info(f"[{scan_id}] Got response: {response.status_code} from {response.url}")
                if response.url:
                    discovered_urls.add(response.url)
                
                # Extract links from HTML
                content_type = (response.headers.get("content-type") or "").lower()
                logger.info(f"[{scan_id}] Content-Type: {content_type}, Response size: {len(response.text)} bytes")
                if "text/html" in content_type and response.text:
                    links = re.findall(r'href=["\']([^"\']+)["\']', response.text, flags=re.IGNORECASE)
                    logger.info(f"[{scan_id}] Found {len(links)} href links in HTML")
                    for href in links:
                        absolute_url = urljoin(response.url or target_url, href)
                        parsed = urlparse(absolute_url)
                        if parsed.scheme in ("http", "https") and parsed.netloc == parsed_target.netloc:
                            cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
                            discovered_urls.add(cleaned)
                            
                logger.info(f"[{scan_id}] Discovered {len(discovered_urls)} unique URLs total")
            except Exception as e:
                logger.warning(f"[{scan_id}] HTTP probe error: {e}")
            
            # Phase 2: Persist endpoints to database
            persisted_count = 0
            logger.info(f"[{scan_id}] Persisting {len(discovered_urls)} discovered URLs to database")
            for endpoint_url in list(discovered_urls)[:100]:
                exists = db.query(Endpoint).filter(
                    Endpoint.scan_id == scan.id,
                    Endpoint.url == endpoint_url,
                    Endpoint.method == "GET",
                ).first()
                if not exists:
                    logger.info(f"[{scan_id}] Adding endpoint: {endpoint_url}")
                    db.add(Endpoint(
                        scan_id=scan.id,
                        url=endpoint_url,
                        method="GET",
                        endpoint_type="page",
                        discovery_method="http_probe",
                        requires_auth=False,
                    ))
                    persisted_count += 1
            
            db.commit()
            total_endpoints = db.query(Endpoint).filter(Endpoint.scan_id == scan.id).count()
            logger.info(f"[{scan_id}] Persisted {persisted_count} new endpoints, total=({total_endpoints})")
            
            # Update scan with results
            scan.endpoints_discovered = total_endpoints
            scan.current_phase = "phase_2_reconnaissance"
            scan.progress_percentage = 25
            scan.status = "running"
            db.commit()
            
            logger.info(f"[{scan_id}] Discovery complete: {total_endpoints} endpoints")
            
            return {
                "success": True,
                "endpoints_discovered": total_endpoints,
                "discovered_urls": list(discovered_urls)[:20]
            }
            
        except Exception as e:
            logger.error(f"[{scan_id}] Discovery failed: {e}")
            try:
                scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
                if scan:
                    scan.status = ScanStatus.FAILED.value
                    scan.error_message = str(e)
                    scan.completed_at = datetime.utcnow()
                    db.commit()
            except:
                pass
            return {"success": False, "error": str(e)}
        finally:
            db.close()
