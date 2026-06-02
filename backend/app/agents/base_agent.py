"""
Base Agent Class
All specialized agents inherit from this class
"""

import logging
import json
import asyncio
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from app.core.database import get_db
from app.core.redis_client import get_redis
try:
    from app.services.llm_service import LLMService
except Exception:
    LLMService = None
try:
    from app.services.storage_service import StorageService
except Exception:
    StorageService = None
from app.core.graph_db import get_graph_db

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Tool Sandbox — safe wrapper for external tool execution
# ─────────────────────────────────────────────────────────────────

@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    output: str = ""
    error: str = ""
    exit_code: int = 0


class ToolSandbox:
    """
    Sandboxed tool executor.
    
    In production this would run tools inside Docker containers.
    For local dev, it runs tools via subprocess or simulates them
    with HTTP requests when the actual binary isn't available.
    """

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Execute a security tool safely.
        
        Supported tools: httpx, katana, nuclei, sqlmap, dalfox,
                         idor_tester, auth_bypass_tester
        """
        logger.info(f"ToolSandbox: executing {tool_name} with params: {list(params.keys())}")
        
        try:
            # Check if the tool binary exists on the system
            binary = self._find_binary(tool_name)
            
            if binary:
                return await self._run_binary(binary, tool_name, params)
            else:
                # Fallback: simulate with HTTP requests for web tools
                return await self._simulate_tool(tool_name, params)
                
        except Exception as e:
            logger.error(f"ToolSandbox: {tool_name} failed: {e}")
            return ToolResult(success=False, error=str(e))

    def _find_binary(self, tool_name: str) -> Optional[str]:
        """Check if a tool binary exists on the system PATH"""
        import shutil
        return shutil.which(tool_name)

    async def _run_binary(self, binary: str, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """Run an actual tool binary"""
        try:
            cmd = self._build_command(binary, tool_name, params)
            logger.info(f"ToolSandbox: running command: {' '.join(cmd[:5])}...")
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            timeout = params.get("timeout", 60)
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            
            return ToolResult(
                success=proc.returncode == 0,
                output=stdout.decode("utf-8", errors="replace"),
                error=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0
            )
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"{tool_name} timed out")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _build_command(self, binary: str, tool_name: str, params: Dict[str, Any]) -> list:
        """Build command-line arguments for a tool"""
        cmd = [binary]
        
        if tool_name == "httpx":
            cmd.extend(["-u", params.get("target", "")])
            if params.get("json"):
                cmd.append("-json")
            if params.get("tech_detect"):
                cmd.append("-tech-detect")
            if params.get("status_code"):
                cmd.append("-status-code")
                
        elif tool_name == "katana":
            cmd.extend(["-u", params.get("url", "")])
            if params.get("depth"):
                cmd.extend(["-d", str(params["depth"])])
            if params.get("json"):
                cmd.append("-jsonl")
                
        elif tool_name == "nuclei":
            cmd.extend(["-u", params.get("target", "")])
            if params.get("severity"):
                cmd.extend(["-severity", params["severity"]])
            cmd.append("-jsonl")
            
        elif tool_name == "sqlmap":
            cmd.extend(["-u", params.get("url", ""), "--batch", "--level=1"])
            
        elif tool_name == "dalfox":
            cmd.extend(["url", params.get("url", "")])
            
        return cmd

    async def _simulate_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """
        Simulate tool output using HTTP requests when binary not available.
        This provides basic discovery without requiring tool installation.
        """
        import requests as _requests
        
        target = params.get("target", params.get("url", ""))
        if not target:
            return ToolResult(success=False, error=f"{tool_name}: no target URL provided")
        
        if tool_name in ("httpx",):
            # Simulate httpx with a simple HTTP GET
            try:
                resp = _requests.get(target, timeout=10, verify=False, allow_redirects=True)
                result = {
                    "url": str(resp.url),
                    "status_code": resp.status_code,
                    "title": "",
                    "webserver": resp.headers.get("Server", ""),
                    "tech": [],
                    "content_length": len(resp.content)
                }
                # Extract title
                if "<title>" in resp.text.lower():
                    start = resp.text.lower().index("<title>") + 7
                    end = resp.text.lower().index("</title>", start)
                    result["title"] = resp.text[start:end].strip()
                # Detect tech from headers
                tech = []
                for h, v in resp.headers.items():
                    hl = h.lower()
                    if hl == "x-powered-by":
                        tech.append(v)
                    elif hl == "server":
                        tech.append(v)
                result["tech"] = tech
                return ToolResult(success=True, output=json.dumps(result))
            except Exception as e:
                return ToolResult(success=False, error=str(e))
                
        elif tool_name in ("katana",):
            # Simulate katana with basic link extraction
            try:
                resp = _requests.get(target, timeout=10, verify=False)
                import re
                links = set()
                from urllib.parse import urljoin
                for match in re.finditer(r'(?:href|src|action)=["\']([^"\']+)["\']', resp.text):
                    url = urljoin(target, match.group(1))
                    if target.split("/")[2] in url:  # same domain
                        links.add(url)
                
                output_lines = []
                for link in list(links)[:50]:
                    output_lines.append(json.dumps({"url": link, "method": "GET", "source": "link"}))
                return ToolResult(success=True, output="\n".join(output_lines))
            except Exception as e:
                return ToolResult(success=False, error=str(e))
                
        elif tool_name in ("nuclei",):
            # Nuclei requires actual binary — return empty results
            return ToolResult(success=True, output="", error="nuclei binary not found, skipped")
            
        elif tool_name == "sqlmap":
            # Simulate SQL injection detection via HTTP payloads
            return await self._simulate_sqli(target)

        elif tool_name == "dalfox":
            # Simulate XSS detection via reflected payload checks
            return await self._simulate_xss(target)

        elif tool_name == "idor_tester":
            # Simulate IDOR detection via ID enumeration
            return await self._simulate_idor(target, params)

        elif tool_name == "auth_bypass_tester":
            # Simulate auth bypass detection
            return await self._simulate_auth_bypass(target, params)

        return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

    # ── HTTP-based vulnerability detection simulators ────────────────

    async def _simulate_sqli(self, target: str) -> ToolResult:
        """Detect SQL injection by sending payloads and checking for SQL error patterns."""
        import requests as _requests
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        SQL_PAYLOADS = ["'", "' OR '1'='1", "1' OR '1'='1'--", "'; DROP TABLE users--", "1 AND 1=1"]
        SQL_ERROR_PATTERNS = [
            "you have an error in your sql syntax",
            "warning: mysql",
            "unclosed quotation mark",
            "quoted string not properly terminated",
            "microsoft ole db provider",
            "odbc sql server driver",
            "pg_query",
            "syntax error at or near",
            "ora-01756",
            "sqlstate",
            "sql syntax",
            "mysql_fetch",
            "sqlite3",
            "jdbc.sqle",
            "sql command not properly ended",
        ]

        findings = []
        parsed = urlparse(target)
        params = parse_qs(parsed.query)

        # If URL has query params, fuzz each one
        targets_to_test = []
        if params:
            for param_name in params:
                for payload in SQL_PAYLOADS:
                    new_params = {k: v[0] if isinstance(v, list) else v for k, v in params.items()}
                    new_params[param_name] = payload
                    fuzzed_url = urlunparse(parsed._replace(query=urlencode(new_params)))
                    targets_to_test.append((fuzzed_url, param_name, payload))
        else:
            # Try appending payloads to the URL path
            for payload in SQL_PAYLOADS[:2]:
                fuzzed_url = target.rstrip("/") + "/" + payload
                targets_to_test.append((fuzzed_url, "path", payload))

        for fuzzed_url, param_name, payload in targets_to_test[:10]:  # limit
            try:
                resp = _requests.get(fuzzed_url, timeout=10, verify=False, allow_redirects=True)
                body_lower = resp.text.lower()

                for pattern in SQL_ERROR_PATTERNS:
                    if pattern in body_lower:
                        findings.append({
                            "url": fuzzed_url,
                            "parameter": param_name,
                            "payload": payload,
                            "evidence": pattern,
                            "status_code": resp.status_code,
                        })
                        break
            except Exception:
                continue

        if findings:
            output = "SQL injection is vulnerable\n" + json.dumps(findings, indent=2)
            return ToolResult(success=True, output=output)
        return ToolResult(success=True, output="No SQL injection found")

    async def _simulate_xss(self, target: str) -> ToolResult:
        """Detect reflected XSS by injecting payloads and checking for reflection."""
        import requests as _requests
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        XSS_PAYLOADS = [
            '<script>alert("XSS")</script>',
            '"><img src=x onerror=alert(1)>',
            "'-alert(1)-'",
            '<svg onload=alert(1)>',
            '"><svg/onload=alert(1)>',
        ]

        findings = []
        parsed = urlparse(target)
        params = parse_qs(parsed.query)

        targets_to_test = []
        if params:
            for param_name in params:
                for payload in XSS_PAYLOADS:
                    new_params = {k: v[0] if isinstance(v, list) else v for k, v in params.items()}
                    new_params[param_name] = payload
                    fuzzed_url = urlunparse(parsed._replace(query=urlencode(new_params)))
                    targets_to_test.append((fuzzed_url, param_name, payload))
        else:
            # Try common search params
            for param_name in ["q", "search", "query", "s", "input", "name"]:
                for payload in XSS_PAYLOADS[:2]:
                    fuzzed_url = target.rstrip("/") + f"?{param_name}={payload}"
                    targets_to_test.append((fuzzed_url, param_name, payload))

        for fuzzed_url, param_name, payload in targets_to_test[:12]:  # limit
            try:
                resp = _requests.get(fuzzed_url, timeout=10, verify=False, allow_redirects=True)
                # Check if payload is reflected in the response body
                if payload in resp.text:
                    findings.append({
                        "param": param_name,
                        "payload": payload,
                        "url": fuzzed_url,
                        "evidence": f"Payload reflected in response body (status {resp.status_code})",
                    })
            except Exception:
                continue

        if findings:
            output = json.dumps(findings)
            return ToolResult(success=True, output=output)
        return ToolResult(success=True, output="[]")

    async def _simulate_idor(self, target: str, params: Dict[str, Any]) -> ToolResult:
        """Detect IDOR by testing sequential ID access without auth."""
        import requests as _requests
        import re

        findings = []

        # Extract numeric IDs from the URL and try adjacent values
        id_pattern = re.compile(r'/(\d+)(?:/|$|\?)')
        match = id_pattern.search(target)

        if match:
            original_id = int(match.group(1))
            test_ids = [original_id + i for i in range(1, 6)]  # test 5 adjacent IDs

            try:
                base_resp = _requests.get(target, timeout=10, verify=False)
                base_status = base_resp.status_code
                base_len = len(base_resp.content)
            except Exception:
                return ToolResult(success=True, output="")

            for test_id in test_ids:
                try:
                    test_url = target.replace(f"/{original_id}", f"/{test_id}")
                    resp = _requests.get(test_url, timeout=10, verify=False)

                    # If we get 200 with similar-length content for different IDs → IDOR
                    if resp.status_code == 200 and abs(len(resp.content) - base_len) < base_len * 0.5:
                        findings.append({
                            "original_id": original_id,
                            "tested_id": test_id,
                            "url": test_url,
                            "status": resp.status_code,
                        })
                except Exception:
                    continue

        if findings:
            return ToolResult(success=True, output="IDOR_DETECTED\n" + json.dumps(findings, indent=2))
        return ToolResult(success=True, output="")

    async def _simulate_auth_bypass(self, target: str, params: Dict[str, Any]) -> ToolResult:
        """Detect auth bypass by testing access without credentials and with path tricks."""
        import requests as _requests

        findings = []
        methods_to_test = params.get("methods", ["path_traversal", "verb_tampering", "header_injection"])

        for method in methods_to_test:
            try:
                if method == "path_traversal":
                    # Try accessing without auth by using path traversal
                    test_urls = [
                        target + "/./",
                        target + "/%2e/",
                        target + "/..;/",
                        target.replace("/api/", "/Api/"),
                    ]
                    for test_url in test_urls:
                        try:
                            resp = _requests.get(test_url, timeout=10, verify=False)
                            if resp.status_code == 200 and len(resp.content) > 100:
                                findings.append({
                                    "method": "path_traversal",
                                    "url": test_url,
                                    "status": resp.status_code,
                                })
                        except Exception:
                            continue

                elif method == "verb_tampering":
                    # Try different HTTP methods
                    for verb in ["OPTIONS", "HEAD", "TRACE"]:
                        try:
                            resp = _requests.request(verb, target, timeout=10, verify=False)
                            if resp.status_code == 200:
                                findings.append({
                                    "method": "verb_tampering",
                                    "verb": verb,
                                    "url": target,
                                    "status": resp.status_code,
                                })
                        except Exception:
                            continue

                elif method == "header_injection":
                    # Try X-Forwarded-For and other header bypasses
                    bypass_headers = [
                        {"X-Forwarded-For": "127.0.0.1"},
                        {"X-Original-URL": "/admin"},
                        {"X-Rewrite-URL": "/admin"},
                    ]
                    for headers in bypass_headers:
                        try:
                            resp = _requests.get(target, headers=headers, timeout=10, verify=False)
                            if resp.status_code == 200 and len(resp.content) > 100:
                                findings.append({
                                    "method": "header_injection",
                                    "headers": headers,
                                    "url": target,
                                    "status": resp.status_code,
                                })
                        except Exception:
                            continue
            except Exception:
                continue

        if findings:
            return ToolResult(success=True, output="BYPASS_SUCCESSFUL\n" + json.dumps(findings, indent=2))
        return ToolResult(success=True, output="")


# ─────────────────────────────────────────────────────────────────
# Base Agent
# ─────────────────────────────────────────────────────────────────

class BaseAgent(ABC):
    """
    Base class for all RakshAI agents
    
    Responsibilities:
    - Event-driven communication via message bus
    - State management
    - Logging and monitoring
    - Error handling and recovery
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.llm_service = None  # Lazy load
        self.storage_service = None
        self.graph_db = None
        self.redis_client = None
        self.tool_sandbox = ToolSandbox()  # Always available
        self.start_time = None
        
    async def initialize(self):
        """Initialize agent resources"""
        logger.info(f"Initializing {self.__class__.__name__} (ID: {self.agent_id})")
        self.llm_service = LLMService() if LLMService is not None else None
        self.storage_service = StorageService() if StorageService is not None else None
        
        # Lazy-load graph_db: only connect when actually needed at runtime
        try:
            self.graph_db = await get_graph_db()
        except Exception as e:
            logger.warning(f"Graph DB not available: {e} (will retry on first use)")
            self.graph_db = None
        
        try:
            self.redis_client = await get_redis()
        except Exception as e:
            logger.warning(f"Redis not available: {e} (will retry on first use)")
            self.redis_client = None
        
        self.start_time = datetime.utcnow()
        
    async def emit_progress(self, scan_id: str, *args):
        """
        Emit progress event to message bus.
        
        Supports two call patterns:
          - emit_progress(scan_id, event_dict)           — BaseAgent style
          - emit_progress(scan_id, agent, phase, details) — Agent style
        """
        try:
            if len(args) == 1 and isinstance(args[0], dict):
                # BaseAgent style: emit_progress(scan_id, {event_dict})
                event = args[0]
            elif len(args) >= 3:
                # Agent style: emit_progress(scan_id, "recon", "started", {details})
                event = {
                    "agent": args[0],
                    "phase": args[1],
                    **(args[2] if isinstance(args[2], dict) else {"message": str(args[2])})
                }
            elif len(args) == 2:
                # emit_progress(scan_id, "recon", "started")
                event = {"agent": args[0], "phase": args[1]}
            else:
                event = {"args": str(args)}

            if self.redis_client:
                await self.redis_client.publish(
                    f"scan:{scan_id}:progress",
                    json.dumps({
                        "agent": self.agent_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "event": event
                    })
                )
        except Exception as e:
            logger.error(f"Failed to emit progress: {e}")
    
    async def log_action(self, scan_id: str, action: str, details: Dict[str, Any]):
        """Log agent action to database"""
        try:
            if self.redis_client:
                # Store in Redis for real-time access
                await self.redis_client.lpush(
                    f"scan:{scan_id}:log",
                    json.dumps({
                        "agent": self.agent_id,
                        "action": action,
                        "details": details,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    @abstractmethod
    async def run(self, scan_id: str, **kwargs) -> Dict[str, Any]:
        """
        Main agent execution method - must be implemented by subclasses
        
        Args:
            scan_id: Scan identifier
            **kwargs: Agent-specific parameters
            
        Returns:
            Dict containing agent execution results
        """
        pass
    
    async def _get_scan_details(self, scan_id: str) -> Dict[str, Any]:
        """Fetch scan details from PostgreSQL (Initial metadata)."""
        from app.models.models import Scan
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            # We first try to get the UUID if the passed ID is numeric
            if str(scan_id).isdigit():
                scan = db.query(Scan).filter(Scan.id == int(scan_id)).first()
            else:
                scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
                
            if not scan:
                return {}
            return {
                "scan_id": scan.scan_id,
                "target_url": scan.target_url,
                "policy": scan.policy or {},
                "status": scan.status
            }
        finally:
            db.close()

    def _resolve_scan_pk(self, db, scan_id: str) -> Optional[int]:
        """Resolve a scan UUID string to its integer primary key.

        ``Vulnerability.scan_id`` is an Integer FK pointing at ``scans.id``,
        so we must never compare it directly against the UUID string stored
        in ``scans.scan_id``.
        """
        from app.models.models import Scan
        if str(scan_id).isdigit():
            return int(scan_id)
        scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
        return scan.id if scan else None

    async def _get_finding(self, scan_id: str, finding_id: str) -> Dict[str, Any]:
        """Fetch a specific finding from PostgreSQL."""
        from app.models.models import Vulnerability
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            # If finding_id is numeric, it's SQL PK. If UUID, it's finding_id string.
            if str(finding_id).isdigit():
                v = db.query(Vulnerability).filter(Vulnerability.id == int(finding_id)).first()
            else:
                scan_pk = self._resolve_scan_pk(db, scan_id)
                v = db.query(Vulnerability).filter(Vulnerability.scan_id == scan_pk).first() if scan_pk else None

            if v:
                return {
                    "finding_id": str(v.id),
                    "type": v.vulnerability_type,
                    "severity": str(v.severity),
                    "url": v.endpoint.url if v.endpoint else "",
                    "evidence": v.evidence or ""
                }
        finally:
            db.close()
        return {}

    async def _get_unvalidated_findings(self, scan_id: str) -> List[Dict[str, Any]]:
        """Fetch all UNVALIDATED findings from PostgreSQL."""
        from app.models.models import Vulnerability
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            scan_pk = self._resolve_scan_pk(db, scan_id)
            if not scan_pk:
                return []
            findings = db.query(Vulnerability).filter(
                Vulnerability.scan_id == scan_pk,
                Vulnerability.status == "UNVALIDATED"
            ).all()
            return [
                {
                    "finding_id": str(v.id),
                    "type": v.vulnerability_type,
                    "severity": str(v.severity),
                    "url": v.endpoint.url if v.endpoint else "",
                    "evidence": v.evidence or ""
                }
                for v in findings
            ]
        finally:
            db.close()
        return []

    async def _get_validated_findings(self, scan_id: str) -> List[Dict[str, Any]]:
        """Fetch all VALIDATED findings from PostgreSQL."""
        from app.models.models import Vulnerability
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            scan_pk = self._resolve_scan_pk(db, scan_id)
            if not scan_pk:
                return []
            findings = db.query(Vulnerability).filter(
                Vulnerability.scan_id == scan_pk,
                Vulnerability.status == "VALIDATED"
            ).all()
            return [
                {
                    "finding_id": str(v.id),
                    "type": v.vulnerability_type,
                    "severity": str(v.severity),
                    "url": v.endpoint.url if v.endpoint else "",
                    "evidence": v.evidence or ""
                }
                for v in findings
            ]
        finally:
            db.close()
        return []

    async def handle_error(self, scan_id: str, *args):
        """
        Centralized error handling.
        
        Supports two call patterns:
          - handle_error(scan_id, exception)              — BaseAgent style
          - handle_error(scan_id, agent_name, exception)  — Agent style
        """
        if len(args) == 1:
            error = args[0]
        elif len(args) >= 2:
            error = args[-1]  # Last arg is always the exception
        else:
            error = Exception("Unknown error")

        logger.error(
            f"{self.__class__.__name__} error in scan {scan_id}: {error}",
            exc_info=True
        )
        
        await self.emit_progress(scan_id, {
            "status": "ERROR",
            "error": str(error),
            "agent": self.agent_id
        })
        
    async def cleanup(self):
        """Cleanup agent resources"""
        logger.info(f"Cleaning up {self.__class__.__name__}")
        # Close connections, release resources
        if self.graph_db:
            await self.graph_db.close()
