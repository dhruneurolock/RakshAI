"""
Orchestrator Service (LAYER 2)

Responsibilities:
1. Scope validation
2. Policy enforcement
3. Rate limiting
4. Target isolation
5. Manage concurrent scans
6. Trigger CoordinatorAgent
7. Monitor resource usage
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import os
import re
import json
import uuid
from pathlib import Path
from urllib.parse import urlparse, urljoin, parse_qsl

import yaml
from sqlalchemy.orm import Session

from app.agents import CoordinatorAgent
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.models import Scan, Endpoint, ScanStatus, Vulnerability, VulnerabilitySeverity, Report

logger = logging.getLogger(__name__)


class OrchestratorService:
    """
    Orchestrator service for managing scans at enterprise level
    
    This is the entry point for all scan operations and enforces:
    - Scope validation (prevent scanning out-of-scope targets)
    - Policy enforcement (respect enterprise policies)
    - Rate limiting (prevent DoS on target systems)
    - Resource management (control concurrent scans)
    """
    
    # Configuration
    MAX_CONCURRENT_SCANS = 5
    RATE_LIMIT_DELAY = 2  # seconds between requests
    DEFAULT_TIMEOUT = 3600  # 1 hour
    
    def __init__(self):
        self.settings = get_settings()
        self.active_scans = {}
        self.scan_queue = []
        self.rate_limiters = {}
    
    async def start_scan(
        self,
        scan_id: str,
        target_url: str,
        scan_type: str,
        user_id: str,
        policy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a new scan with full enterprise validation
        
        Args:
            scan_id: Unique scan identifier
            target_url: Target URL to scan
            scan_type: Type of scan (quick, full, targeted)
            user_id: User initiating the scan
            policy: Optional enterprise policy overrides
            
        Returns:
            Dict with scan start result
        """
        try:
            logger.info(f"Orchestrator: Starting scan {scan_id} for {target_url}")
            
            # Phase 1: Scope validation
            if not await self._validate_scope(target_url):
                return {
                    "success": False,
                    "error": "SCOPE_VIOLATION",
                    "message": f"Target {target_url} is not in authorized scope"
                }
            
            # Phase 2: Policy enforcement
            effective_policy = await self._get_effective_policy(user_id, scan_type, policy)
            
            if not await self._check_policy_compliance(target_url, effective_policy):
                return {
                    "success": False,
                    "error": "POLICY_VIOLATION",
                    "message": "Target violates enterprise policy"
                }
            
            # Phase 3: Rate limiting check
            if not await self._check_rate_limit(target_url):
                return {
                    "success": False,
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many scans for this target. Please wait."
                }
            
            # Phase 4: Resource availability
            if len(self.active_scans) >= self.MAX_CONCURRENT_SCANS:
                # Queue the scan
                self.scan_queue.append({
                    "scan_id": scan_id,
                    "target_url": target_url,
                    "scan_type": scan_type,
                    "user_id": user_id,
                    "policy": effective_policy,
                    "queued_at": datetime.utcnow()
                })
                
                return {
                    "success": True,
                    "status": "QUEUED",
                    "message": f"Scan queued. Position: {len(self.scan_queue)}",
                    "queue_position": len(self.scan_queue)
                }
            
            # Phase 5: Launch scan
            result = await self._launch_scan(
                scan_id,
                target_url,
                scan_type,
                user_id,
                effective_policy
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Orchestrator error for scan {scan_id}: {e}")
            return {
                "success": False,
                "error": "ORCHESTRATOR_ERROR",
                "message": str(e)
            }
    
    async def _validate_scope(self, target_url: str) -> bool:
        """
        Validate that target is in authorized scope
        
        Checks:
        1. Not a public service (Google, GitHub, etc.)
        2. In organization's allowed domains
        3. Not blacklisted
        """
        parsed = urlparse(target_url)
        hostname = parsed.hostname
        
        # Blacklist check (prevent scanning critical infrastructure)
        # Only block exact domains, not subdomains like google-gruyere.appspot.com
        blacklist = [
            "www.google.com", "www.facebook.com", "www.amazon.com",
            "www.microsoft.com", "www.github.com", "www.stackoverflow.com",
        ]
        
        # Also block localhost/loopback
        if hostname in ("localhost", "127.0.0.1", "::1"):
            logger.warning(f"Scope violation: {hostname} is localhost")
            return False
        
        if hostname in blacklist:
            logger.warning(f"Scope violation: {hostname} is blacklisted")
            return False
        
        # Whitelist check (in production, check against org's domains)
        # For now, allow all non-blacklisted targets
        
        return True
    
    async def _get_effective_policy(
        self,
        user_id: str,
        scan_type: str = "full",
        policy_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get effective policy for scan"""
        
        # Default policy
        default_policy = {
            "max_depth": 3,
            "max_endpoints": 100,
            "max_attacks": 50,
            "timeout": self.DEFAULT_TIMEOUT,
            "allowed_attacks": ["IDOR", "XSS", "SQLI", "AUTH_BYPASS"],
            "forbidden_attacks": ["DOS", "RESOURCE_EXHAUSTION"],
            "time_window": {
                "allowed_hours": list(range(0, 24)),  # All hours
                "forbidden_days": []  # No forbidden days
            },
            "rate_limit": {
                "requests_per_second": 10,
                "concurrent_requests": 5
            }
        }
        
        # In production, load user's policy from database
        # user_policy = await self.db.get_user_policy(user_id)
        
        # Merge with override (override takes precedence)
        if policy_override:
            default_policy.update(policy_override)
            
        # Apply scan_type specific limits
        if scan_type == "single_page":
            default_policy["max_depth"] = 0
            default_policy["max_endpoints"] = 1
        elif scan_type == "quick":
            default_policy["max_depth"] = 1
            default_policy["max_endpoints"] = 10
        
        return default_policy
    
    async def _check_policy_compliance(
        self,
        target_url: str,
        policy: Dict[str, Any]
    ) -> bool:
        """Check if scan complies with policy"""
        
        # Check time window
        now = datetime.utcnow()
        current_hour = now.hour
        current_weekday = now.weekday()
        
        time_window = policy.get("time_window", {})
        allowed_hours = time_window.get("allowed_hours", list(range(24)))
        forbidden_days = time_window.get("forbidden_days", [])
        
        if current_hour not in allowed_hours:
            logger.warning(f"Policy violation: Current hour {current_hour} not in allowed hours")
            return False
        
        if current_weekday in forbidden_days:
            logger.warning(f"Policy violation: Today (day {current_weekday}) is forbidden")
            return False
        
        # Check target isn't production (in production, check domain)
        if "production" in target_url or "prod" in target_url:
            logger.warning(f"Policy violation: Production environments forbidden")
            return False
        
        return True
    
    async def _check_rate_limit(self, target_url: str) -> bool:
        """Check rate limiting for target"""
        
        # Get or create rate limiter for this target
        if target_url not in self.rate_limiters:
            self.rate_limiters[target_url] = {
                "last_scan": None,
                "scan_count": 0,
                "window_start": datetime.utcnow()
            }
        
        limiter = self.rate_limiters[target_url]
        now = datetime.utcnow()
        
        # Reset window if more than 1 hour has passed
        if now - limiter["window_start"] > timedelta(hours=1):
            limiter["scan_count"] = 0
            limiter["window_start"] = now
        
        # Check if too many scans in current window (max 5 per hour)
        if limiter["scan_count"] >= 5:
            logger.warning(f"Rate limit exceeded for {target_url}")
            return False
        
        # Check minimum delay between scans (2 minutes)
        if limiter["last_scan"]:
            time_since_last = now - limiter["last_scan"]
            if time_since_last < timedelta(minutes=2):
                logger.warning(f"Rate limit: Too soon since last scan of {target_url}")
                return False
        
        # Update rate limiter
        limiter["scan_count"] += 1
        limiter["last_scan"] = now
        
        return True
    
    async def _launch_scan(
        self,
        scan_id: str,
        target_url: str,
        scan_type: str,
        user_id: str,
        policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Launch scan via CoordinatorAgent"""
        
        try:
            # Store in active scans
            self.active_scans[scan_id] = {
                "started_at": datetime.utcnow(),
                "target_url": target_url,
                "scan_type": scan_type,
                "user_id": user_id,
                "policy": policy
            }

            db = SessionLocal()
            try:
                scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
                if not scan:
                    raise Exception("Scan not found in database")
                coordinator_scan_id = str(scan.id)
            finally:
                db.close()
            
            try:
                coordinator = CoordinatorAgent(agent_id=f"coordinator-{scan_id[:8]}")
            except TypeError:
                coordinator = CoordinatorAgent(scan_id)

            self.active_scans[scan_id]["coordinator"] = coordinator
            
            # Launch coordinator as an asyncio task
            task = asyncio.create_task(self._run_coordinator(coordinator_scan_id, coordinator, scan_id))
            self.active_scans[scan_id]["task"] = task
            
            logger.info(f"Scan {scan_id} launched successfully via Agentic Pipeline")
            
            return {
                "success": True,
                "status": "INITIALIZING",
                "scan_id": scan_id,
                "message": "Scan started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to launch scan {scan_id}: {e}")
            return {
                "success": False,
                "error": "LAUNCH_FAILED",
                "message": str(e)
            }

    async def _run_coordinator(self, coordinator_scan_id: str, coordinator: CoordinatorAgent, scan_uuid: str) -> None:
        """Run coordinator agent and handle completion"""
        
        try:
            await coordinator.initialize()
            
            # Run the coordinator with an unlimited timeout for LLM strategy generation
            result = await asyncio.wait_for(coordinator.run(coordinator_scan_id), timeout=None)
            
            logger.info(f"Coordinator completed for scan {scan_uuid}: {result}")
            
        except Exception as e:
            logger.error(f"Coordinator error for scan {scan_uuid}: {e}")
            # Mark scan as failed in the database
            db = SessionLocal()
            try:
                scan = db.query(Scan).filter(Scan.scan_id == scan_uuid).first()
                if scan:
                    scan.status = ScanStatus.FAILED.value
                    scan.current_phase = "failed"
                    scan.error_message = str(e)
                    scan.completed_at = datetime.utcnow()
                    db.commit()
            except Exception as db_e:
                logger.error(f"Failed to update scan {scan_uuid} to FAILED state: {db_e}")
            finally:
                db.close()
            
        finally:
            try:
                await coordinator.cleanup()
            except Exception as cleanup_e:
                logger.error(f"Error during coordinator cleanup for {scan_uuid}: {cleanup_e}")

            # Remove from active scans
            if scan_uuid in self.active_scans:
                del self.active_scans[scan_uuid]
            
            # Process queue if available
            await self._process_queue()
    
    async def _process_queue(self) -> None:
        """Process queued scans if resources available"""
        
        if not self.scan_queue:
            return
        
        if len(self.active_scans) >= self.MAX_CONCURRENT_SCANS:
            return
        
        # Get next scan from queue
        next_scan = self.scan_queue.pop(0)
        
        logger.info(f"Processing queued scan {next_scan['scan_id']}")
        
        # Launch it
        await self._launch_scan(
            next_scan["scan_id"],
            next_scan["target_url"],
            next_scan["scan_type"],
            next_scan["user_id"],
            next_scan["policy"]
        )
    
    async def stop_scan(self, scan_id: str) -> Dict[str, Any]:
        """Stop an active scan"""
        
        if scan_id not in self.active_scans:
            return {
                "success": False,
                "error": "SCAN_NOT_FOUND",
                "message": f"Scan {scan_id} is not active"
            }
        
        try:
            # Remove from active scans
            scan_data = self.active_scans.pop(scan_id)
            
            # Cancel the task if it's running
            if "task" in scan_data and not scan_data["task"].done():
                scan_data["task"].cancel()
            
            logger.info(f"Scan {scan_id} stopped by user")
            
            # Update DB
            db = SessionLocal()
            try:
                scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
                if scan:
                    scan.status = ScanStatus.CANCELLED.value
                    scan.current_phase = "cancelled"
                    scan.completed_at = datetime.utcnow()
                    db.commit()
            finally:
                db.close()
            
            return {
                "success": True,
                "message": "Scan stopped successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "STOP_FAILED",
                "message": str(e)
            }
    
    def get_active_scans(self) -> List[Dict[str, Any]]:
        """Get list of active scans"""
        
        return [
            {
                "scan_id": scan_id,
                "target_url": data["target_url"],
                "started_at": data["started_at"].isoformat(),
                "scan_type": data["scan_type"],
                "user_id": data["user_id"]
            }
            for scan_id, data in self.active_scans.items()
        ]
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status"""
        
        return {
            "queued_scans": len(self.scan_queue),
            "active_scans": len(self.active_scans),
            "available_slots": self.MAX_CONCURRENT_SCANS - len(self.active_scans),
            "queue": [
                {
                    "scan_id": scan["scan_id"],
                    "target_url": scan["target_url"],
                    "queued_at": scan["queued_at"].isoformat()
                }
                for scan in self.scan_queue
            ]
        }


# Singleton instance
_orchestrator = None

def get_orchestrator() -> OrchestratorService:
    """Get orchestrator service instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorService()
    return _orchestrator
