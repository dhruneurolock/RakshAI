"""
Graph Database Abstraction Layer
Previously used PostgreSQL, now fully backed by PostgreSQL to simplify deployment
and prevent missing data issues caused by Cypher synchronization.
"""

import logging
from typing import Dict, Any, List, Optional
import json

from app.core.database import SessionLocal
from app.models.models import Scan, Endpoint, Vulnerability

logger = logging.getLogger(__name__)


class GraphDatabase:
    """
    PostgreSQL-backed "Graph" Database manager.
    Maintains the same API signatures as the old PostgreSQL implementation
    to ensure seamless integration with the existing agents.
    """

    def __init__(self):
        self._connected = False
        logger.info("GraphDatabase initialized (PostgreSQL Backend)")

    async def connect(self):
        """Mock connection - PostgreSQL is handled via SessionLocal"""
        self._connected = True
        logger.info("✅ Connected to PostgreSQL Graph backend")

    async def ensure_connected(self):
        """Ensure connection is alive"""
        self._connected = True
        return True

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def create_indexes(self):
        """Indexes are managed by SQLAlchemy models"""
        pass

    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute is no longer used since Cypher queries are removed.
        Returns empty list to prevent crashes if accidentally called.
        """
        logger.warning(f"execute() called with query: {query}")
        return []

    def _resolve_scan(self, db, scan_id: str) -> Optional[Scan]:
        """Helper to resolve UUID vs Integer scan IDs"""
        if str(scan_id).isdigit():
            return db.query(Scan).filter(Scan.id == int(scan_id)).first()
        return db.query(Scan).filter(Scan.scan_id == scan_id).first()

    async def create_scan_node(self, scan_id: str, metadata: Dict[str, Any]) -> None:
        """Create or update a Scan in PostgreSQL"""
        db = SessionLocal()
        try:
            scan = self._resolve_scan(db, scan_id)
            if scan:
                scan.target_url = metadata.get("target_url", scan.target_url)
                if "status" in metadata:
                    scan.current_phase = metadata["status"]
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create scan node: {e}")
        finally:
            db.close()

    async def add_endpoint(self, scan_id: str, endpoint: Dict[str, Any]) -> None:
        """Add discovered endpoint (Already handled by ReconAgent _persist_endpoints_to_db)"""
        pass

    async def create_attack_node(self, scan_id: str, attack: Dict[str, Any]) -> None:
        """Create attack node (Now managed dynamically via Scan.strategy in Executor)"""
        pass

    async def update_attack_status(
        self,
        attack_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update attack node status (No longer needed)"""
        pass

    async def get_unexplored_endpoints(
        self,
        scan_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get endpoints not yet targeted by attacks"""
        # This was unused in the current pipeline, but implemented for API parity
        db = SessionLocal()
        try:
            scan = self._resolve_scan(db, scan_id)
            if not scan:
                return []
            
            endpoints = db.query(Endpoint).filter(Endpoint.scan_id == scan.id).limit(limit).all()
            return [
                {
                    "url": ep.url,
                    "method": ep.method,
                    "params": ep.parameters or {}
                }
                for ep in endpoints
            ]
        finally:
            db.close()

    async def get_scan_endpoints(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get all endpoints discovered for a specific scan."""
        db = SessionLocal()
        try:
            scan = self._resolve_scan(db, scan_id)
            if not scan:
                return []
            
            endpoints = db.query(Endpoint).filter(Endpoint.scan_id == scan.id).all()
            return [
                {
                    "url": ep.url,
                    "method": ep.method,
                    "params": ep.parameters or {}
                }
                for ep in endpoints
            ]
        except Exception as e:
            logger.error(f"Failed to get scan endpoints: {e}")
            return []
        finally:
            db.close()

    async def get_scan_statistics(self, scan_id: str) -> Dict[str, int]:
        """Get scan progress statistics"""
        db = SessionLocal()
        try:
            scan = self._resolve_scan(db, scan_id)
            if not scan:
                return {"endpoints": 0, "attacks": 0, "findings": 0}
            
            endpoint_count = db.query(Endpoint).filter(Endpoint.scan_id == scan.id).count()
            finding_count = db.query(Vulnerability).filter(Vulnerability.scan_id == scan.id).count()
            
            # Estimate attacks from strategy if available
            attack_count = 0
            if scan.strategy and isinstance(scan.strategy, dict):
                attack_count = scan.strategy.get("total_attacks", 0)
                
            return {
                "endpoints": endpoint_count,
                "attacks": attack_count,
                "findings": finding_count
            }
        except Exception as e:
            logger.error(f"Failed to get scan statistics: {e}")
            return {"endpoints": 0, "attacks": 0, "findings": 0}
        finally:
            db.close()

    async def close(self):
        """Close database connection"""
        self._connected = False
        logger.info("Closed GraphDatabase mock connection")


async def get_graph_db() -> GraphDatabase:
    """Get a PostgreSQL-backed graph database instance"""
    db = GraphDatabase()
    await db.connect()
    return db

