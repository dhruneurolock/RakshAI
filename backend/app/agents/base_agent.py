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
    
    Accepts an optional LLMService for Agentic RAG payload selection.
    When available, _simulate_sqli and _simulate_xss will use
    vector search + LLM reasoning to pick context-aware payloads
    instead of firing the same hardcoded list every time.
    """

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

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
            # Simulate katana with basic link extraction + JS API discovery
            try:
                resp = _requests.get(target, timeout=10, verify=False)
                import re
                links = set()
                from urllib.parse import urljoin, urlparse as _urlparse

                # Extract base domain for subdomain matching
                target_domain = _urlparse(target).netloc.split(":")[0]
                # Get the root domain (e.g., "demoblaze.com" from "www.demoblaze.com")
                domain_parts = target_domain.split(".")
                root_domain = ".".join(domain_parts[-2:]) if len(domain_parts) >= 2 else target_domain

                # 1. Standard HTML link extraction
                for match in re.finditer(r'(?:href|src|action)=["\']([^"\']+)["\']', resp.text):
                    url = urljoin(target, match.group(1))
                    parsed = _urlparse(url)
                    if root_domain in parsed.netloc:
                        links.add(url)

                # 2. JavaScript API endpoint extraction
                # Match fetch("url"), fetch('url'), $.ajax({url: "..."})
                js_patterns = [
                    r'fetch\s*\(\s*["\']([^"\']+)["\']',
                    r'\.open\s*\(\s*["\'][A-Z]+["\']\s*,\s*["\']([^"\']+)["\']',
                    r'axios\.[a-z]+\s*\(\s*["\']([^"\']+)["\']',
                    r'url\s*:\s*["\']([^"\']+)["\']',
                    r'["\']https?://[^"\']*' + re.escape(root_domain) + r'[^"\']*["\']',
                ]
                for pattern in js_patterns:
                    for match in re.finditer(pattern, resp.text):
                        raw_url = match.group(1) if match.lastindex else match.group(0).strip("\"'")
                        full_url = urljoin(target, raw_url)
                        parsed = _urlparse(full_url)
                        if root_domain in parsed.netloc and parsed.scheme in ("http", "https"):
                            links.add(full_url)

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

        elif tool_name == "security_headers":
            return await self._simulate_security_headers(target)

        return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

    # ── HTTP-based vulnerability detection simulators ────────────────

    async def _simulate_sqli(self, target: str) -> ToolResult:
        """Detect SQL injection by sending payloads via GET params AND POST body.
        
        Uses Agentic RAG (vector search → LLM selection) when llm_service is
        available to pick context-aware payloads.  Falls back to a hardcoded
        list otherwise.
        """
        import requests as _requests
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        FALLBACK_SQL_PAYLOADS = ["'", "' OR '1'='1", "1' OR '1'='1'--", "\" OR \"\"=\""]
        SQL_ERROR_PATTERNS = [
            "you have an error in your sql syntax",
            "warning: mysql", "unclosed quotation mark",
            "quoted string not properly terminated",
            "microsoft ole db provider", "odbc sql server driver",
            "pg_query", "syntax error at or near",
            "ora-01756", "sqlstate", "sql syntax",
            "mysql_fetch", "sqlite3", "jdbc.sqle",
            "sql command not properly ended",
            "internal server error",
        ]
        COMMON_PARAMS = ["id", "username", "search", "query", "name", "cat"]

        findings = []
        parsed = urlparse(target)

        logger.info(f"[sqli-sim] Testing {target}")

        # ── 1. Test existing query parameters ──
        params = parse_qs(parsed.query)
        if params:
            for param_name in params:
                # ── Agentic RAG payload selection ──
                sql_payloads = None
                if self.llm_service:
                    try:
                        import asyncio
                        sql_payloads = await self.llm_service.get_agentic_rag_payloads(
                            f"SQL injection payload for GET query parameter named '{param_name}' "
                            f"on URL {target}",
                            k_retrieve=10,
                            k_select=3,
                        )
                        if sql_payloads:
                            logger.info(f"[sqli-sim] Agentic RAG selected {len(sql_payloads)} payloads for param '{param_name}'")
                    except Exception as rag_err:
                        logger.warning(f"[sqli-sim] Agentic RAG failed for param '{param_name}': {rag_err}")
                if not sql_payloads:
                    sql_payloads = FALLBACK_SQL_PAYLOADS[:3]
                    logger.info(f"[sqli-sim] Using fallback payloads for param '{param_name}'")

                for payload in sql_payloads:
                    new_params = {k: v[0] if isinstance(v, list) else v for k, v in params.items()}
                    new_params[param_name] = payload
                    fuzzed_url = urlunparse(parsed._replace(query=urlencode(new_params)))
                    try:
                        resp = _requests.get(fuzzed_url, timeout=5, verify=False, allow_redirects=True)
                        body_lower = resp.text.lower()
                        for pattern in SQL_ERROR_PATTERNS:
                            if pattern in body_lower:
                                findings.append({"url": fuzzed_url, "parameter": param_name,
                                                 "payload": payload, "evidence": pattern,
                                                 "status_code": resp.status_code})
                                logger.info(f"[sqli-sim] FOUND via GET param '{param_name}' → {pattern}")
                                break
                        if resp.status_code == 500 and not findings:
                            findings.append({"url": fuzzed_url, "parameter": param_name,
                                             "payload": payload,
                                             "evidence": "HTTP 500 Internal Server Error",
                                             "status_code": 500})
                    except Exception:
                        continue
                if findings:
                    break

        # ── 2. Test POST body with common parameter names (JSON) ──
        if not findings:
            for param_name in COMMON_PARAMS:
                # ── Agentic RAG for POST params ──
                post_payloads = None
                if self.llm_service:
                    try:
                        post_payloads = await self.llm_service.get_agentic_rag_payloads(
                            f"SQL injection payload for POST JSON body parameter named '{param_name}'",
                            k_retrieve=10,
                            k_select=2,
                        )
                    except Exception:
                        pass
                if not post_payloads:
                    post_payloads = FALLBACK_SQL_PAYLOADS[:2]

                for payload in post_payloads:
                    try:
                        resp = _requests.post(target, json={param_name: payload}, timeout=5,
                                              verify=False, allow_redirects=True)
                        body_lower = resp.text.lower()
                        for pattern in SQL_ERROR_PATTERNS:
                            if pattern in body_lower:
                                findings.append({"url": target, "parameter": f"POST:{param_name}",
                                                 "payload": payload, "evidence": pattern,
                                                 "status_code": resp.status_code})
                                logger.info(f"[sqli-sim] FOUND via POST JSON '{param_name}' → {pattern}")
                                break
                        if resp.status_code == 500 and not findings:
                            findings.append({"url": target, "parameter": f"POST:{param_name}",
                                             "payload": payload,
                                             "evidence": "HTTP 500 Internal Server Error",
                                             "status_code": 500})
                    except Exception:
                        continue
                if findings:
                    break

        # ── 3. Test POST body with form-encoded data ──
        if not findings:
            for param_name in COMMON_PARAMS[:3]:
                try:
                    resp = _requests.post(target, data={param_name: "'"}, timeout=5,
                                          verify=False, allow_redirects=True)
                    body_lower = resp.text.lower()
                    for pattern in SQL_ERROR_PATTERNS:
                        if pattern in body_lower:
                            findings.append({"url": target, "parameter": f"FORM:{param_name}",
                                             "payload": "'", "evidence": pattern,
                                             "status_code": resp.status_code})
                            break
                except Exception:
                    continue

        logger.info(f"[sqli-sim] Completed {target}: {len(findings)} findings")

        if findings:
            output = "SQL injection is vulnerable\n" + json.dumps(findings, indent=2)
            return ToolResult(success=True, output=output)
        return ToolResult(success=True, output="No SQL injection found")

    async def _simulate_xss(self, target: str) -> ToolResult:
        """Detect XSS by injecting payloads via GET params, POST body, and checking headers.
        
        Uses Agentic RAG (vector search → LLM selection) when llm_service is
        available to pick context-aware payloads.  Falls back to a hardcoded
        list otherwise.
        """
        import requests as _requests
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        FALLBACK_XSS_PAYLOADS = [
            '<script>alert("XSS")</script>',
            '"><img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
        ]
        COMMON_PARAMS = ["q", "search", "query", "name", "input", "s"]

        findings = []
        parsed = urlparse(target)
        params = parse_qs(parsed.query)

        logger.info(f"[xss-sim] Testing {target}")

        # ── 1. Test existing query parameters ──
        if params:
            for param_name in params:
                # ── Agentic RAG payload selection ──
                xss_payloads = None
                if self.llm_service:
                    try:
                        xss_payloads = await self.llm_service.get_agentic_rag_payloads(
                            f"XSS Cross-Site Scripting payload for input parameter named '{param_name}' "
                            f"on URL {target}",
                            k_retrieve=10,
                            k_select=2,
                        )
                        if xss_payloads:
                            logger.info(f"[xss-sim] Agentic RAG selected {len(xss_payloads)} payloads for param '{param_name}'")
                    except Exception as rag_err:
                        logger.warning(f"[xss-sim] Agentic RAG failed for param '{param_name}': {rag_err}")
                if not xss_payloads:
                    xss_payloads = FALLBACK_XSS_PAYLOADS[:2]
                    logger.info(f"[xss-sim] Using fallback payloads for param '{param_name}'")

                for payload in xss_payloads:
                    new_params = {k: v[0] if isinstance(v, list) else v for k, v in params.items()}
                    new_params[param_name] = payload
                    fuzzed_url = urlunparse(parsed._replace(query=urlencode(new_params)))
                    try:
                        resp = _requests.get(fuzzed_url, timeout=5, verify=False, allow_redirects=True)
                        if payload in resp.text:
                            findings.append({"param": param_name, "payload": payload,
                                             "url": fuzzed_url,
                                             "evidence": f"Payload reflected in response (status {resp.status_code})"})
                            logger.info(f"[xss-sim] FOUND reflected XSS via GET param '{param_name}'")
                    except Exception:
                        continue
                if findings:
                    break

        # ── 2. Test common query parameter names ──
        if not findings:
            for param_name in COMMON_PARAMS:
                # ── Agentic RAG for common params ──
                common_payloads = None
                if self.llm_service:
                    try:
                        common_payloads = await self.llm_service.get_agentic_rag_payloads(
                            f"XSS payload for common search or input parameter named '{param_name}'",
                            k_retrieve=8,
                            k_select=1,
                        )
                    except Exception:
                        pass
                payload = common_payloads[0] if common_payloads else FALLBACK_XSS_PAYLOADS[0]

                try:
                    fuzzed_url = target.rstrip("/") + f"?{param_name}={payload}"
                    resp = _requests.get(fuzzed_url, timeout=5, verify=False, allow_redirects=True)
                    if payload in resp.text:
                        findings.append({"param": param_name, "payload": payload,
                                         "url": fuzzed_url,
                                         "evidence": f"Payload reflected in response (status {resp.status_code})"})
                        logger.info(f"[xss-sim] FOUND reflected XSS via GET '?{param_name}='")
                        break
                except Exception:
                    continue

        # ── 3. Test POST body parameters ──
        if not findings:
            for param_name in COMMON_PARAMS[:3]:
                payload = FALLBACK_XSS_PAYLOADS[0]
                try:
                    resp = _requests.post(target, json={param_name: payload},
                                          timeout=5, verify=False, allow_redirects=True)
                    if payload in resp.text:
                        findings.append({"param": f"POST:{param_name}", "payload": payload,
                                         "url": target,
                                         "evidence": f"Payload reflected in POST response (status {resp.status_code})"})
                        logger.info(f"[xss-sim] FOUND reflected XSS via POST '{param_name}'")
                        break
                except Exception:
                    continue
        logger.info(f"[xss-sim] Completed {target}: {len(findings)} findings")

        if findings:
            return ToolResult(success=True, output=json.dumps(findings))
        return ToolResult(success=True, output="[]")

    async def _simulate_idor(self, target: str, params: Dict[str, Any]) -> ToolResult:
        """Detect IDOR by testing sequential ID access without auth."""
        import requests as _requests
        import re

        findings = []
        logger.info(f"[idor-sim] Testing {target}")

        # ── 1. Test numeric IDs in URL path ──
        id_pattern = re.compile(r'/(\d+)(?:/|$|\?)')
        match = id_pattern.search(target)

        if match:
            original_id = int(match.group(1))
            test_ids = [original_id + i for i in range(1, 4)]

            try:
                base_resp = _requests.get(target, timeout=5, verify=False)
                base_status = base_resp.status_code
                base_len = len(base_resp.content)
            except Exception:
                return ToolResult(success=True, output="")

            for test_id in test_ids:
                try:
                    test_url = target.replace(f"/{original_id}", f"/{test_id}")
                    resp = _requests.get(test_url, timeout=5, verify=False)
                    if resp.status_code == 200 and abs(len(resp.content) - base_len) < base_len * 0.5:
                        findings.append({"original_id": original_id, "tested_id": test_id,
                                         "url": test_url, "status": resp.status_code})
                        break
                except Exception:
                    continue

        # ── 2. Test API endpoints with ID in POST body ──
        if not findings:
            for id_val in [1, 2, 3]:
                try:
                    resp = _requests.post(target, json={"id": str(id_val)},
                                          timeout=5, verify=False)
                    if resp.status_code == 200 and len(resp.content) > 50:
                        try:
                            data = resp.json()
                            # If we get different data for different IDs → potential IDOR
                            if isinstance(data, (dict, list)) and data:
                                findings.append({"tested_id": id_val, "url": target,
                                                 "status": resp.status_code,
                                                 "method": "POST body id parameter"})
                                break
                        except Exception:
                            pass
                except Exception:
                    continue

        logger.info(f"[idor-sim] Completed {target}: {len(findings)} findings")

        if findings:
            return ToolResult(success=True, output="IDOR_DETECTED\n" + json.dumps(findings, indent=2))
        return ToolResult(success=True, output="")

    async def _simulate_auth_bypass(self, target: str, params: Dict[str, Any]) -> ToolResult:
        """Detect auth bypass via path tricks, default creds, unauth API, and CORS."""
        import requests as _requests

        findings = []
        methods_to_test = params.get("methods", [
            "path_traversal", "verb_tampering", "header_injection",
            "default_credentials", "unauthenticated_api", "cors_misconfig"
        ])

        logger.info(f"[auth-sim] Testing {target} with methods: {methods_to_test}")

        for method in methods_to_test:
            try:
                if method == "path_traversal":
                    test_urls = [
                        target + "/./", target + "/%2e/",
                        target + "/..;/", target.replace("/api/", "/Api/")
                    ]
                    for test_url in test_urls:
                        try:
                            resp = _requests.get(test_url, timeout=5, verify=False)
                            if resp.status_code == 200 and len(resp.content) > 100:
                                findings.append({"method": "path_traversal",
                                                 "url": test_url, "status": resp.status_code})
                                break
                        except Exception:
                            continue

                elif method == "verb_tampering":
                    for verb in ["OPTIONS", "HEAD", "PUT", "DELETE"]:
                        try:
                            resp = _requests.request(verb, target, timeout=5, verify=False)
                            if resp.status_code == 200:
                                findings.append({"method": "verb_tampering", "verb": verb,
                                                 "url": target, "status": resp.status_code})
                                break
                        except Exception:
                            continue

                elif method == "header_injection":
                    bypass_headers = [
                        {"X-Forwarded-For": "127.0.0.1"},
                        {"X-Original-URL": "/admin"},
                        {"X-Custom-IP-Authorization": "127.0.0.1"},
                    ]
                    for headers in bypass_headers:
                        try:
                            resp = _requests.get(target, headers=headers, timeout=5, verify=False)
                            if resp.status_code == 200 and len(resp.content) > 100:
                                findings.append({"method": "header_injection",
                                                 "headers": headers, "url": target,
                                                 "status": resp.status_code})
                                break
                        except Exception:
                            continue

                elif method == "default_credentials":
                    default_creds = [
                        {"username": "admin", "password": "admin"},
                        {"username": "admin", "password": "password"},
                        {"username": "test", "password": "test"},
                    ]
                    for creds in default_creds:
                        try:
                            resp = _requests.post(target, json=creds, timeout=5, verify=False)
                            body_lower = resp.text.lower()
                            if resp.status_code == 200 and any(kw in body_lower for kw in [
                                '"auth_token"', '"token"', '"access_token"',
                                '"session"', '"success":true', '"success": true',
                                "dashboard", "logged in"
                            ]):
                                findings.append({
                                    "method": "default_credentials",
                                    "credentials": creds,
                                    "url": target,
                                    "status": resp.status_code,
                                    "evidence": "Login succeeded with default credentials"
                                })
                                logger.info(f"[auth-sim] FOUND default creds: {creds}")
                                break
                        except Exception:
                            continue

                elif method == "unauthenticated_api":
                    api_paths = ["/api/", "/api/v1/", "/api/users", "/api/admin", "/api/config"]
                    from urllib.parse import urlparse as _urlparse
                    parsed = _urlparse(target)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"

                    for api_path in api_paths:
                        try:
                            test_url = base_url + api_path
                            resp = _requests.get(test_url, timeout=5, verify=False)
                            if resp.status_code == 200 and len(resp.content) > 50:
                                try:
                                    data = resp.json()
                                    if isinstance(data, (dict, list)) and data:
                                        findings.append({
                                            "method": "unauthenticated_api",
                                            "url": test_url,
                                            "status": resp.status_code,
                                            "evidence": f"API returns data without auth ({len(resp.content)} bytes)"
                                        })
                                        logger.info(f"[auth-sim] FOUND unauthenticated API: {test_url}")
                                        break
                                except Exception:
                                    pass
                        except Exception:
                            continue

                elif method == "cors_misconfig":
                    try:
                        resp = _requests.get(target, headers={"Origin": "https://evil.com"},
                                             timeout=5, verify=False)
                        acao = resp.headers.get("Access-Control-Allow-Origin", "")
                        if acao == "*" or acao == "https://evil.com":
                            findings.append({
                                "method": "cors_misconfig",
                                "url": target,
                                "status": resp.status_code,
                                "evidence": f"CORS allows arbitrary origin: {acao}"
                            })
                            logger.info(f"[auth-sim] FOUND CORS misconfiguration: {acao}")
                    except Exception:
                        pass

            except Exception:
                continue

        logger.info(f"[auth-sim] Completed {target}: {len(findings)} findings")

        if findings:
            return ToolResult(success=True, output="BYPASS_SUCCESSFUL\n" + json.dumps(findings, indent=2))
        return ToolResult(success=True, output="")

    async def _simulate_security_headers(self, target: str) -> ToolResult:
        """Analyze HTTP response headers for missing security controls."""
        import requests as _requests

        logger.info(f"[headers-sim] Analyzing security headers for {target}")

        try:
            resp = _requests.get(target, timeout=10, verify=False, allow_redirects=True)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

        headers_lower = {k.lower(): v for k, v in resp.headers.items()}
        findings = []

        # ── Check each security header ──
        checks = [
            {
                "header": "content-security-policy",
                "severity": "MEDIUM",
                "title": "Missing Content-Security-Policy Header",
                "description": (
                    "The Content-Security-Policy (CSP) header is not set. "
                    "CSP helps prevent Cross-Site Scripting (XSS), clickjacking, "
                    "and other code injection attacks by specifying allowed content sources."
                ),
            },
            {
                "header": "strict-transport-security",
                "severity": "MEDIUM",
                "title": "Missing Strict-Transport-Security Header",
                "description": (
                    "The Strict-Transport-Security (HSTS) header is not set. "
                    "HSTS ensures browsers only communicate over HTTPS, "
                    "preventing protocol downgrade attacks and cookie hijacking."
                ),
            },
            {
                "header": "x-frame-options",
                "severity": "MEDIUM",
                "title": "Missing X-Frame-Options Header (Clickjacking)",
                "description": (
                    "The X-Frame-Options header is not set. This allows the page "
                    "to be embedded in iframes on malicious sites, enabling "
                    "clickjacking attacks where users unknowingly interact with hidden content."
                ),
            },
            {
                "header": "x-content-type-options",
                "severity": "LOW",
                "title": "Missing X-Content-Type-Options Header",
                "description": (
                    "The X-Content-Type-Options header is not set to 'nosniff'. "
                    "Without this, browsers may MIME-sniff responses, potentially "
                    "executing uploaded files as scripts."
                ),
            },
            {
                "header": "permissions-policy",
                "severity": "LOW",
                "title": "Missing Permissions-Policy Header",
                "description": (
                    "The Permissions-Policy (formerly Feature-Policy) header is not set. "
                    "This header controls which browser features and APIs can be used, "
                    "reducing the attack surface."
                ),
            },
        ]

        for check in checks:
            if check["header"] not in headers_lower:
                findings.append({
                    "type": "SECURITY_HEADER_MISSING",
                    "severity": check["severity"],
                    "header": check["header"],
                    "title": check["title"],
                    "description": check["description"],
                    "url": target,
                })

        # ── Check for server version disclosure ──
        server_header = headers_lower.get("server", "")
        x_powered = headers_lower.get("x-powered-by", "")

        if server_header and any(c.isdigit() for c in server_header):
            findings.append({
                "type": "SERVER_INFO_LEAK",
                "severity": "LOW",
                "header": "server",
                "title": f"Server Version Disclosure: {server_header}",
                "description": (
                    f"The server discloses its version: '{server_header}'. "
                    "Attackers can use this information to find known vulnerabilities "
                    "for this specific server version."
                ),
                "url": target,
            })

        if x_powered:
            findings.append({
                "type": "SERVER_INFO_LEAK",
                "severity": "LOW",
                "header": "x-powered-by",
                "title": f"Technology Disclosure via X-Powered-By: {x_powered}",
                "description": (
                    f"The X-Powered-By header reveals: '{x_powered}'. "
                    "This leaks technology stack information to attackers."
                ),
                "url": target,
            })

        # ── Check for insecure cookies ──
        for cookie_header in resp.headers.get("Set-Cookie", "").split(","):
            cookie_lower = cookie_header.lower()
            if cookie_header and "httponly" not in cookie_lower:
                findings.append({
                    "type": "INSECURE_COOKIE",
                    "severity": "LOW",
                    "header": "set-cookie",
                    "title": "Cookie Missing HttpOnly Flag",
                    "description": (
                        "A cookie is set without the HttpOnly flag, making it "
                        "accessible to JavaScript and vulnerable to XSS-based theft."
                    ),
                    "url": target,
                })
                break
            if cookie_header and "secure" not in cookie_lower and target.startswith("https"):
                findings.append({
                    "type": "INSECURE_COOKIE",
                    "severity": "LOW",
                    "header": "set-cookie",
                    "title": "Cookie Missing Secure Flag",
                    "description": (
                        "A cookie is set without the Secure flag on an HTTPS site, "
                        "allowing it to be sent over unencrypted HTTP connections."
                    ),
                    "url": target,
                })
                break

        logger.info(f"[headers-sim] Completed {target}: {len(findings)} issues found")

        if findings:
            return ToolResult(success=True,
                              output="SECURITY_HEADERS_ISSUES\n" + json.dumps(findings, indent=2))
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
        self.tool_sandbox = ToolSandbox(llm_service=self.llm_service)  # Pass LLM for Agentic RAG
        self.start_time = None
        
    async def initialize(self):
        """Initialize agent resources"""
        logger.info(f"Initializing {self.__class__.__name__} (ID: {self.agent_id})")
        self.llm_service = LLMService() if LLMService is not None else None
        self.storage_service = StorageService() if StorageService is not None else None
        
        # Update ToolSandbox with the initialized LLM service for Agentic RAG
        self.tool_sandbox.llm_service = self.llm_service
        
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
                    "evidence": v.response_evidence or ""
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
                    "evidence": v.response_evidence or ""
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
                    "evidence": v.response_evidence or ""
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
        if self.redis_client:
            try:
                if hasattr(self.redis_client, "aclose"):
                    await self.redis_client.aclose()
                else:
                    await self.redis_client.close()
            except Exception as e:
                logger.error(f"Failed to close redis client: {e}")
