"""
Exploit Execution Agent

Responsibilities:
1. Execute planned attacks via Tool Sandbox
2. Session management (cookies, tokens, headers)
3. Parameter fuzzing
4. Capture raw outputs
5. Upload results to MinIO
6. Create Finding nodes in PostgreSQL
7. Handle authentication context
"""

from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime

from .base_agent import BaseAgent


class ExploitExecutionAgent(BaseAgent):
    """Agent responsible for executing security tests and exploits"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.session_data = {}
        self.findings = []
    
    async def run(self, scan_id: str, attack_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Execute attacks
        
        Args:
            scan_id: Scan identifier
            attack_id: Specific attack to execute (if None, executes all)
            
        Returns:
            Dict with execution results
        """
        try:
            await self.emit_progress(scan_id, "executor", "started", {
                "message": "Starting attack execution"
            })
            
            # Phase 1: Get planned attacks from graph
            if attack_id:
                attacks = [await self._get_attack_node(scan_id, attack_id)]
            else:
                attacks = await self._get_planned_attacks(scan_id)
            
            if not attacks:
                return {
                    "success": False,
                    "error": "No attacks planned",
                    "attacks_executed": 0
                }
            
            # Phase 2: Setup session (get auth if needed)
            await self.emit_progress(scan_id, "executor", "session_setup", {
                "message": "Setting up session context"
            })
            await self._setup_session(scan_id)
            
            # Phase 3: Execute attacks sequentially
            total_findings = 0
            
            for i, attack in enumerate(attacks, 1):
                await self.emit_progress(scan_id, "executor", "executing", {
                    "message": f"Executing attack {i}/{len(attacks)}",
                    "attack_type": attack.get("type")
                })
                
                result = await self._execute_attack(scan_id, attack)
                
                if result.get("findings"):
                    total_findings += len(result["findings"])
                    self.findings.extend(result["findings"])
            
            # Phase 4: Upload all raw outputs
            await self.emit_progress(scan_id, "executor", "uploading", {
                "message": "Uploading execution results"
            })
            await self._upload_results(scan_id)
            
            result_summary = {
                "success": True,
                "attacks_executed": len(attacks),
                "findings_discovered": total_findings,
                "attack_types": list(set([a.get("type") for a in attacks]))
            }
            
            await self.emit_progress(scan_id, "executor", "completed", result_summary)
            await self.log_action(scan_id, "execution_completed", result_summary)
            
            return result_summary
            
        except Exception as e:
            await self.handle_error(scan_id, "executor", e)
            raise
    
    async def _get_planned_attacks(self, scan_id: str) -> List[Dict[str, Any]]:
        """
        Build attack list from PostgreSQL strategy + endpoints.
        
        The previous implementation relied on AttackNode records, but
        those were silently failing to create because the Cypher MATCH on
        Endpoint URL didn't find matching nodes. Now we read the strategy
        JSON and discovered endpoints directly from PostgreSQL.
        """
        from app.models.models import Scan, Endpoint
        from app.core.database import SessionLocal
        import logging
        _log = logging.getLogger(__name__)

        db = SessionLocal()
        try:
            # Resolve scan
            if str(scan_id).isdigit():
                scan = db.query(Scan).filter(Scan.id == int(scan_id)).first()
            else:
                scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()

            if not scan:
                _log.warning(f"[executor] Scan {scan_id} not found")
                return []

            # Get all discovered endpoints
            endpoints = db.query(Endpoint).filter(Endpoint.scan_id == scan.id).all()
            if not endpoints:
                _log.warning(f"[executor] No endpoints found for scan {scan_id}")
                return []

            _log.info(f"[executor] Building attacks from {len(endpoints)} endpoints")

            # Categorize endpoints for attack planning
            # Cap per-type to avoid sending thousands of HTTP requests
            MAX_SQLI = 5
            MAX_XSS = 5
            MAX_IDOR = 3
            MAX_AUTH = 2  # auth bypass is expensive (default creds, API probing)

            attacks = []
            attack_idx = 0
            seen_sqli_urls = set()
            seen_xss_urls = set()
            seen_auth_urls = set()
            idor_count = 0

            for ep in endpoints:
                url = ep.url or ""
                method = ep.method or "GET"
                ep_type = ep.endpoint_type or "page"
                url_lower = url.lower()

                # SQL Injection — prioritize forms/params, cap total
                if url not in seen_sqli_urls and len(seen_sqli_urls) < MAX_SQLI:
                    seen_sqli_urls.add(url)
                    attacks.append({
                        "attack_id": f"{scan_id}_attack_{attack_idx}",
                        "type": "SQLI",
                        "target_url": url,
                        "priority": 80 if ("?" in url or method == "POST" or ep_type == "form") else 60,
                        "tools": ["sqlmap"],
                        "sequence": 3,
                    })
                    attack_idx += 1

                # XSS — cap total
                if url not in seen_xss_urls and len(seen_xss_urls) < MAX_XSS:
                    seen_xss_urls.add(url)
                    attacks.append({
                        "attack_id": f"{scan_id}_attack_{attack_idx}",
                        "type": "XSS",
                        "target_url": url,
                        "priority": 70,
                        "tools": ["dalfox"],
                        "sequence": 4,
                    })
                    attack_idx += 1

                # IDOR — test endpoints with numeric IDs in path OR API endpoints
                if idor_count < MAX_IDOR and (any(seg.isdigit() for seg in url.split("/")) or "/api" in url_lower):
                    attacks.append({
                        "attack_id": f"{scan_id}_attack_{attack_idx}",
                        "type": "IDOR",
                        "target_url": url,
                        "priority": 85,
                        "tools": ["idor_tester"],
                        "sequence": 2,
                    })
                    attack_idx += 1
                    idor_count += 1

                # Auth bypass — only test a few endpoints (expensive)
                if url not in seen_auth_urls and len(seen_auth_urls) < MAX_AUTH:
                    seen_auth_urls.add(url)
                    attacks.append({
                        "attack_id": f"{scan_id}_attack_{attack_idx}",
                        "type": "AUTH_BYPASS",
                        "target_url": url,
                        "priority": 95 if any(x in url_lower for x in ["/login", "/auth", "/admin", "/api/"]) else 50,
                        "tools": ["auth_bypass_tester"],
                        "sequence": 1,
                    })
                    attack_idx += 1

            # ── Security Headers — test the base target URL once ──
            from urllib.parse import urlparse as _up
            base_parsed = _up(endpoints[0].url if endpoints else "")
            base_target = f"{base_parsed.scheme}://{base_parsed.netloc}" if base_parsed.netloc else ""
            if base_target:
                attacks.append({
                    "attack_id": f"{scan_id}_attack_{attack_idx}",
                    "type": "SECURITY_HEADERS",
                    "target_url": base_target,
                    "priority": 40,
                    "tools": ["security_headers"],
                    "sequence": 5,
                })
                attack_idx += 1

            # Sort by priority (highest first)
            attacks.sort(key=lambda a: a["priority"], reverse=True)

            _log.info(f"[executor] Built {len(attacks)} attacks from {len(endpoints)} endpoints")
            return attacks

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[executor] Failed to build attack list: {e}")
            return []
        finally:
            db.close()
    
    async def _get_attack_node(self, scan_id: str, attack_id: str) -> Dict[str, Any]:
        """Get specific attack node"""
        # Simplified - would query PostgreSQL for specific attack
        return {"attack_id": attack_id, "type": "UNKNOWN"}
    
    async def _setup_session(self, scan_id: str) -> None:
        """Setup session context (cookies, tokens)"""
        # This would:
        # 1. Check if authentication is required
        # 2. Perform login if needed
        # 3. Store session data (cookies, JWT tokens)
        
        self.session_data = {
            "cookies": {},
            "headers": {},
            "tokens": {}
        }
    
    async def _execute_attack(self, scan_id: str, attack: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single attack"""
        attack_type = attack.get("type")
        target = attack.get("target_url")
        tools = attack.get("tools", [])
        
        import logging
        _log = logging.getLogger(__name__)
        _log.info(f"[executor] Executing {attack_type} against {target}")
        
        if not target:
            _log.warning(f"[executor] Skipping {attack_type}: no target_url")
            return {"success": False, "error": "No target URL", "findings": []}
        
        try:
            # Route to appropriate attack handler
            if attack_type == "SQLI":
                return await self._execute_sqli(scan_id, attack)
            elif attack_type == "XSS":
                return await self._execute_xss(scan_id, attack)
            elif attack_type == "IDOR":
                return await self._execute_idor(scan_id, attack)
            elif attack_type == "AUTH_BYPASS":
                return await self._execute_auth_bypass(scan_id, attack)
            elif attack_type == "SECURITY_HEADERS":
                return await self._execute_security_headers(scan_id, attack)
            else:
                return await self._execute_generic(scan_id, attack)
                
        except Exception as e:
            await self.log_action(scan_id, f"attack_execution_error_{attack_type}", {
                "error": str(e),
                "attack_id": attack.get("attack_id")
            })
            return {"success": False, "error": str(e), "findings": []}
    
    async def _execute_sqli(self, scan_id: str, attack: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL injection test"""
        target_url = attack.get("target_url")
        
        try:
            result = await self.tool_sandbox.execute("sqlmap", {
                "url": target_url,
                "batch": True,
                "level": 3,
                "risk": 2,
                "threads": 5,
                "random_agent": True,
                "timeout": None
            })
            
            if result.success:
                # Parse SQLMap output for findings
                findings = self._parse_sqlmap_output(result.output, target_url)
                
                # Create finding nodes in PostgreSQL
                for finding in findings:
                    await self._create_finding(scan_id, attack, finding)
                
                return {
                    "success": True,
                    "findings": findings,
                    "raw_output": result.output
                }
            else:
                return {"success": False, "error": result.error, "findings": []}
                
        except Exception as e:
            return {"success": False, "error": str(e), "findings": []}
    
    async def _execute_xss(self, scan_id: str, attack: Dict[str, Any]) -> Dict[str, Any]:
        """Execute XSS test"""
        target_url = attack.get("target_url")
        
        try:
            # Use dalfox for XSS scanning
            result = await self.tool_sandbox.execute("dalfox", {
                "url": target_url,
                "blind": True,
                "mining_dict": True,
                "output": "json",
                "timeout": None
            })
            
            if result.success:
                findings = self._parse_dalfox_output(result.output, target_url)
                
                for finding in findings:
                    await self._create_finding(scan_id, attack, finding)
                
                return {
                    "success": True,
                    "findings": findings,
                    "raw_output": result.output
                }
            else:
                return {"success": False, "error": result.error, "findings": []}
                
        except Exception as e:
            return {"success": False, "error": str(e), "findings": []}
    
    async def _execute_idor(self, scan_id: str, attack: Dict[str, Any]) -> Dict[str, Any]:
        """Execute IDOR test"""
        target_url = attack.get("target_url")
        
        try:
            # Use custom IDOR tester
            result = await self.tool_sandbox.execute("idor_tester", {
                "url": target_url,
                "session": self.session_data.get("cookies", {}),
                "id_range": 100,
                "method": "GET"
            })
            
            if result.success:
                findings = self._parse_idor_output(result.output, target_url)
                
                for finding in findings:
                    await self._create_finding(scan_id, attack, finding)
                
                return {
                    "success": True,
                    "findings": findings,
                    "raw_output": result.output
                }
            else:
                return {"success": False, "error": result.error, "findings": []}
                
        except Exception as e:
            return {"success": False, "error": str(e), "findings": []}
    
    async def _execute_auth_bypass(self, scan_id: str, attack: Dict[str, Any]) -> Dict[str, Any]:
        """Execute authentication bypass test"""
        target_url = attack.get("target_url")
        
        try:
            result = await self.tool_sandbox.execute("auth_bypass_tester", {
                "url": target_url,
                "methods": ["path_traversal", "verb_tampering", "header_injection"]
            })
            
            if result.success:
                findings = self._parse_auth_bypass_output(result.output, target_url)
                
                for finding in findings:
                    await self._create_finding(scan_id, attack, finding)
                
                return {
                    "success": True,
                    "findings": findings,
                    "raw_output": result.output
                }
            else:
                return {"success": False, "error": result.error, "findings": []}
                
        except Exception as e:
            return {"success": False, "error": str(e), "findings": []}
    
    async def _execute_generic(self, scan_id: str, attack: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic attack"""
        return {"success": True, "findings": [], "raw_output": ""}
    
    async def _execute_security_headers(self, scan_id: str, attack: Dict[str, Any]) -> Dict[str, Any]:
        """Execute security headers analysis"""
        target_url = attack.get("target_url")
        
        try:
            result = await self.tool_sandbox.execute("security_headers", {
                "url": target_url,
            })
            
            if result.success:
                findings = self._parse_security_headers_output(result.output, target_url)
                
                for finding in findings:
                    await self._create_finding(scan_id, attack, finding)
                
                return {
                    "success": True,
                    "findings": findings,
                    "raw_output": result.output
                }
            else:
                return {"success": False, "error": result.error, "findings": []}
                
        except Exception as e:
            return {"success": False, "error": str(e), "findings": []}
    
    def _parse_sqlmap_output(self, output: str, url: str) -> List[Dict[str, Any]]:
        """Parse SQLMap output for findings"""
        findings = []
        
        # Simplified parsing - production would use proper SQLMap output parsing
        if "is vulnerable" in output.lower() or "injectable" in output.lower():
            findings.append({
                "type": "SQL_INJECTION",
                "severity": "HIGH",
                "url": url,
                "description": (
                    f"SQL Injection vulnerability detected at {url}.\n\n"
                    "The application fails to properly sanitize user input before incorporating it "
                    "into SQL queries. An attacker can inject malicious SQL statements to read, "
                    "modify, or delete database contents.\n\n"
                    "**Impact:** An attacker can extract sensitive data (usernames, passwords, "
                    "credit card numbers), modify or delete records, and in some cases execute "
                    "operating system commands on the database server."
                ),
                "evidence": output[:500],
                "remediation": (
                    "1. **Immediate:** Use parameterized queries (prepared statements) for all "
                    "database interactions.\n"
                    "2. **Input Validation:** Validate and sanitize all user inputs on the server side.\n"
                    "3. **ORM Usage:** Use an ORM framework that handles query parameterization automatically.\n"
                    "4. **Least Privilege:** Ensure the database user has minimal required permissions.\n"
                    "5. **WAF:** Deploy a Web Application Firewall to detect and block SQL injection attempts."
                ),
            })
        
        return findings
    
    def _parse_dalfox_output(self, output: str, url: str) -> List[Dict[str, Any]]:
        """Parse Dalfox/XSS simulator output for findings"""
        findings = []
        
        try:
            # Dalfox outputs JSON
            data = json.loads(output) if output else []
            for item in data:
                param = item.get("param", "unknown")
                payload = item.get("payload", "")

                # Distinguish between actual reflected XSS and missing-header findings
                if param == "headers":
                    # Missing security header — already covered by SECURITY_HEADERS attack
                    # Skip to avoid duplicates (security headers are handled separately)
                    continue

                findings.append({
                    "type": "XSS",
                    "severity": "MEDIUM",
                    "url": item.get("url", url),
                    "parameter": param,
                    "payload": payload,
                    "description": (
                        f"Cross-Site Scripting (XSS) vulnerability detected at {item.get('url', url)} "
                        f"in the '{param}' parameter.\n\n"
                        f"The injected payload `{payload[:80]}` was reflected in the response "
                        "without proper encoding or sanitization. An attacker can inject "
                        "arbitrary JavaScript code that executes in the context of other users' "
                        "browser sessions.\n\n"
                        "**Impact:** Session hijacking, credential theft, defacement, "
                        "phishing attacks, and malware distribution to legitimate users."
                    ),
                    "evidence": item.get("evidence", ""),
                    "remediation": (
                        "1. **Output Encoding:** HTML-encode all user-supplied data before rendering.\n"
                        "2. **Content Security Policy:** Implement a strict CSP header to prevent inline script execution.\n"
                        "3. **Input Validation:** Reject or strip HTML/JavaScript from user inputs.\n"
                        "4. **HTTPOnly Cookies:** Set the HttpOnly flag on session cookies to prevent JS access.\n"
                        "5. **Framework Protection:** Use a templating engine with auto-escaping enabled."
                    ),
                })
        except:
            pass
        
        return findings
    
    def _parse_idor_output(self, output: str, url: str) -> List[Dict[str, Any]]:
        """Parse IDOR tester output"""
        findings = []
        
        if "IDOR_DETECTED" in output:
            findings.append({
                "type": "IDOR",
                "severity": "HIGH",
                "url": url,
                "description": (
                    f"Insecure Direct Object Reference (IDOR) vulnerability detected at {url}.\n\n"
                    "The application exposes internal object references (e.g., numeric IDs) in URLs "
                    "and does not verify that the authenticated user is authorized to access the "
                    "requested resource. By changing the ID parameter, an attacker can access "
                    "other users' data.\n\n"
                    "**Impact:** Unauthorized access to sensitive user data, account takeover, "
                    "data exfiltration, and potential regulatory compliance violations (GDPR, HIPAA)."
                ),
                "evidence": output[:500],
                "remediation": (
                    "1. **Authorization Checks:** Verify that the authenticated user owns the requested resource on every API call.\n"
                    "2. **Indirect References:** Use indirect reference maps (UUIDs or tokens) instead of sequential IDs.\n"
                    "3. **Access Control Layer:** Implement a centralized authorization middleware.\n"
                    "4. **Rate Limiting:** Rate-limit enumeration attempts on resource endpoints.\n"
                    "5. **Audit Logging:** Log all access to sensitive resources for anomaly detection."
                ),
            })
        
        return findings
    
    def _parse_auth_bypass_output(self, output: str, url: str) -> List[Dict[str, Any]]:
        """Parse auth bypass tester output"""
        findings = []
        
        if "BYPASS_SUCCESSFUL" in output:
            # Try to extract methods from the JSON output
            bypass_methods = []
            try:
                json_start = output.index("[")
                json_end = output.rindex("]") + 1
                details = json.loads(output[json_start:json_end])
                bypass_methods = [d.get("method", "unknown") for d in details if isinstance(d, dict)]
            except Exception:
                pass

            methods_text = ", ".join(bypass_methods) if bypass_methods else "path traversal / verb tampering / header injection"

            findings.append({
                "type": "AUTH_BYPASS",
                "severity": "CRITICAL",
                "url": url,
                "description": (
                    f"Authentication bypass vulnerability detected on {url}.\n\n"
                    f"The following bypass techniques were successful: {methods_text}.\n\n"
                    "An attacker can access protected resources without valid credentials by manipulating "
                    "the request path, HTTP method, or headers. This allows unauthorized access to "
                    "administrative panels, user data, and sensitive application functionality.\n\n"
                    "**Impact:** Complete authentication bypass leading to unauthorized access. "
                    "An attacker can view, modify, or delete data belonging to other users, "
                    "escalate privileges, and compromise the entire application."
                ),
                "evidence": output[:500],
                "remediation": (
                    "1. **Immediate:** Implement server-side authentication checks on every protected route. "
                    "Do not rely on client-side or path-based access controls.\n"
                    "2. **Path Normalization:** Normalize all URL paths before evaluating access rules "
                    "(remove /./, /../, URL-encoded variants).\n"
                    "3. **Method Enforcement:** Restrict allowed HTTP methods per endpoint; reject OPTIONS/TRACE "
                    "on sensitive routes.\n"
                    "4. **Header Validation:** Do not trust X-Forwarded-For, X-Original-URL, or X-Rewrite-URL "
                    "headers for access control decisions.\n"
                    "5. **Testing:** Add integration tests that verify 401/403 responses for all protected "
                    "endpoints when accessed without valid credentials."
                ),
            })
        
        return findings
    
    def _parse_security_headers_output(self, output: str, url: str) -> List[Dict[str, Any]]:
        """Parse security headers analysis output"""
        findings = []

        if "SECURITY_HEADERS_ISSUES" not in output:
            return findings

        try:
            # Extract JSON array from the output
            json_start = output.index("[")
            json_end = output.rindex("]") + 1
            issues = json.loads(output[json_start:json_end])
        except Exception:
            return findings

        for issue in issues:
            if not isinstance(issue, dict):
                continue

            severity = (issue.get("severity", "LOW")).upper()
            title = issue.get("title", "Security Header Missing")
            description = issue.get("description", "")
            issue_type = issue.get("type", "SECURITY_HEADER_MISSING")

            findings.append({
                "type": issue_type,
                "severity": severity,
                "url": url,
                "description": (
                    f"{title}\n\n"
                    f"{description}\n\n"
                    "**OWASP Category:** A05:2021 - Security Misconfiguration\n\n"
                    "**Impact:** Missing security headers weaken the application's defense-in-depth "
                    "posture. While each missing header individually may be low-to-medium risk, "
                    "the cumulative effect significantly increases the attack surface."
                ),
                "evidence": f"Header '{issue.get('header', '')}' not found in HTTP response",
                "remediation": (
                    f"Add the missing header to your server configuration:\n\n"
                    f"**Header:** {issue.get('header', '')}\n\n"
                    "Configure this in your web server (Nginx, Apache) or application middleware.\n"
                    "For Nginx: add_header {header} \"value\" always;\n"
                    "For Apache: Header always set {header} \"value\"\n"
                    "For Express.js: Use the 'helmet' middleware package."
                ).format(header=issue.get("header", "")),
                "owasp_category": "A05",
            })

        return findings
    
    async def _create_finding(self, scan_id: str, attack: Dict[str, Any], finding: Dict[str, Any]) -> None:
        """Create finding node in PostgreSQL AND persist to PostgreSQL Vulnerability table."""
        finding_id = f"{scan_id}_finding_{len(self.findings)}"

        # ── 1. Try PostgreSQL (optional — graph enrichment) ──
        try:
            if self.graph_db and self.graph_db.is_connected:
                query = """
                MATCH (a:AttackNode {attack_id: $attack_id})
                CREATE (f:Finding {
                    finding_id: $finding_id,
                    type: $type,
                    severity: $severity,
                    url: $url,
                    description: $description,
                    created_at: datetime()
                })
                CREATE (a)-[:PRODUCED]->(f)
                RETURN f
                """
                async with self.graph_db.driver.session() as session:
                    await session.run(query,
                        attack_id=attack.get("attack_id"),
                        finding_id=finding_id,
                        type=finding.get("type"),
                        severity=finding.get("severity"),
                        url=finding.get("url"),
                        description=finding.get("description")
                    )
        except Exception as e:
            await self.log_action(scan_id, "postgresql_finding_error", {"error": str(e)})

        # ── 2. Persist to PostgreSQL (required — UI reads from here) ──
        try:
            from app.models.models import Scan, Endpoint, Vulnerability, VulnerabilitySeverity
            from app.core.database import SessionLocal

            db = SessionLocal()
            try:
                # Resolve scan PK
                scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
                if not scan:
                    return

                # Map severity string to enum
                severity_str = (finding.get("severity") or "medium").lower()
                severity_map = {
                    "critical": VulnerabilitySeverity.CRITICAL,
                    "high": VulnerabilitySeverity.HIGH,
                    "medium": VulnerabilitySeverity.MEDIUM,
                    "low": VulnerabilitySeverity.LOW,
                    "info": VulnerabilitySeverity.INFO,
                }
                severity_enum = severity_map.get(severity_str, VulnerabilitySeverity.MEDIUM)

                # Try to find a matching endpoint by URL
                endpoint_id = None
                finding_url = finding.get("url", "")
                if finding_url:
                    ep = db.query(Endpoint).filter(
                        Endpoint.scan_id == scan.id,
                        Endpoint.url == finding_url,
                    ).first()
                    if ep:
                        endpoint_id = ep.id

                # Map finding type to OWASP category
                vuln_type = finding.get("type", "UNKNOWN")
                owasp_map = {
                    "SQL_INJECTION": "A03",
                    "XSS": "A03",
                    "IDOR": "A01",
                    "AUTH_BYPASS": "A07",
                    "SSRF": "A10",
                    "PATH_TRAVERSAL": "A01",
                    "SECURITY_HEADER_MISSING": "A05",
                    "SERVER_INFO_LEAK": "A05",
                    "INSECURE_COOKIE": "A05",
                }
                # Prefer finding-level owasp_category if set
                owasp_category = finding.get("owasp_category") or owasp_map.get(vuln_type, "A05")

                cwe_map = {
                    "SQL_INJECTION": "CWE-89",
                    "XSS": "CWE-79",
                    "IDOR": "CWE-639",
                    "AUTH_BYPASS": "CWE-287",
                    "SSRF": "CWE-918",
                    "PATH_TRAVERSAL": "CWE-22",
                    "SECURITY_HEADER_MISSING": "CWE-693",
                    "SERVER_INFO_LEAK": "CWE-200",
                    "INSECURE_COOKIE": "CWE-614",
                }

                # Use the finding's title if available, otherwise generate from type
                title_map = {
                    "SQL_INJECTION": "SQL Injection Vulnerability",
                    "XSS": "Cross-Site Scripting (XSS)",
                    "IDOR": "Insecure Direct Object Reference (IDOR)",
                    "AUTH_BYPASS": "Authentication Bypass",
                    "SECURITY_HEADER_MISSING": finding.get("description", "").split("\n")[0] if finding.get("description") else "Missing Security Header",
                    "SERVER_INFO_LEAK": finding.get("description", "").split("\n")[0] if finding.get("description") else "Server Information Disclosure",
                    "INSECURE_COOKIE": "Insecure Cookie Configuration",
                }
                title = title_map.get(vuln_type, f"{vuln_type} vulnerability detected")

                vuln = Vulnerability(
                    scan_id=scan.id,
                    endpoint_id=endpoint_id,
                    title=title,
                    description=finding.get("description", f"{vuln_type} vulnerability found at {finding_url}"),
                    severity=severity_enum,
                    confidence=0.75,
                    owasp_category=owasp_category,
                    vulnerability_type=vuln_type,
                    request_payload=finding.get("payload", ""),
                    response_evidence=finding.get("evidence", ""),
                    affected_parameter=finding.get("parameter", ""),
                    attack_vector=attack.get("type", ""),
                    remediation=finding.get("remediation", ""),
                    cwe_id=cwe_map.get(vuln_type, ""),
                    status="UNVALIDATED",
                )
                db.add(vuln)
                db.commit()

                import logging
                logging.getLogger(__name__).info(
                    f"[executor] Persisted finding {finding_id} to PostgreSQL "
                    f"(scan={scan.id}, type={vuln_type}, severity={severity_str})"
                )
            finally:
                db.close()

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[executor] Failed to persist finding to DB: {e}")
    
    async def _upload_results(self, scan_id: str) -> None:
        """Upload raw results to MinIO"""
        try:
            results_data = json.dumps({
                "findings": self.findings,
                "session_data": self.session_data,
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2).encode()
            
            if self.storage_service:
                await self.storage_service.upload_to_bucket(
                    "rakshaidb-raw",
                    f"{scan_id}/executor/results.json",
                    results_data,
                    "application/json"
                )
        except Exception as e:
            await self.log_action(scan_id, "results_upload_error", {"error": str(e)})
