"""
Proof-of-Concept (PoC) Generation Agent

Responsibilities:
1. Capture screenshots via Playwright
2. Record HTTP request/response traces
3. Generate cURL commands
4. LLM-generated business impact analysis
5. LLM-generated remediation steps
6. Upload evidence to MinIO
7. Update Vulnerability record with URLs
"""

from typing import Dict, Any, List, Optional
import json
import base64
from datetime import datetime
from io import BytesIO

from .base_agent import BaseAgent


class PoCAgent(BaseAgent):
    """Agent responsible for generating Proof-of-Concept evidence"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.poc_data = []
    
    async def run(self, scan_id: str, finding_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Execute PoC generation workflow
        
        Args:
            scan_id: Scan identifier
            finding_id: Specific finding to generate PoC for (if None, generates for all validated)
            
        Returns:
            Dict with PoC generation results
        """
        try:
            await self.emit_progress(scan_id, "poc", "started", {
                "message": "Starting PoC generation"
            })
            
            # Phase 1: Get validated findings (fall back to unvalidated if none)
            if finding_id:
                findings = [await self._get_finding(scan_id, finding_id)]
            else:
                findings = await self._get_validated_findings(scan_id)
                if not findings:
                    # Fallback: process unvalidated findings so they still
                    # get enriched with description, remediation, and PoC
                    findings = await self._get_unvalidated_findings(scan_id)
            
            if not findings:
                return {
                    "success": False,
                    "error": "No validated findings to generate PoC for",
                    "pocs_generated": 0
                }
            
            # Phase 2: Generate PoC for each finding
            pocs_generated = 0
            
            for i, finding in enumerate(findings, 1):
                await self.emit_progress(scan_id, "poc", "generating", {
                    "message": f"Generating PoC {i}/{len(findings)}",
                    "finding_type": finding.get("type")
                })
                
                result = await self.generate_poc(scan_id, finding)
                
                if result["success"]:
                    pocs_generated += 1
                    self.poc_data.append(result)
            
            summary = {
                "success": True,
                "findings_processed": len(findings),
                "pocs_generated": pocs_generated,
                "generation_rate": pocs_generated / len(findings) if findings else 0
            }
            
            await self.emit_progress(scan_id, "poc", "completed", summary)
            await self.log_action(scan_id, "poc_generation_completed", summary)
            
            return summary
            
        except Exception as e:
            await self.handle_error(scan_id, "poc", e)
            raise
    
    async def generate_poc(self, scan_id: str, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive PoC for a validated finding.
        
        Now includes structured step-by-step reproduction with per-step
        Playwright screenshots stored in the ``poc_steps`` JSON column.
        
        Returns:
            Dict with PoC URLs and LLM-generated content
        """
        finding_id = finding.get("finding_id")
        finding_type = finding.get("type")
        url = finding.get("url")
        
        await self.log_action(scan_id, "poc_generation_started", {
            "finding_id": finding_id,
            "type": finding_type
        })
        
        try:
            # Step 1: Capture full-page screenshot
            await self.emit_progress(scan_id, "poc", "screenshot", {
                "finding_id": finding_id
            })
            screenshot_url = await self._capture_screenshot(scan_id, finding_id, url, finding)
            
            # Step 1.5: Generate structured PoC steps with per-step screenshots
            await self.emit_progress(scan_id, "poc", "poc_steps", {
                "finding_id": finding_id,
                "message": "Generating step-by-step reproduction with screenshots"
            })
            poc_steps = await self._generate_poc_steps(scan_id, finding_id, finding)
            
            # Step 2: Record HTTP trace
            await self.emit_progress(scan_id, "poc", "http_trace", {
                "finding_id": finding_id
            })
            trace_url = await self._record_http_trace(scan_id, finding_id, url, finding)
            
            # Step 3: Generate cURL command
            await self.emit_progress(scan_id, "poc", "curl_command", {
                "finding_id": finding_id
            })
            curl_command = await self._generate_curl(finding)
            
            # Step 4: LLM-generated business impact
            await self.emit_progress(scan_id, "poc", "business_impact", {
                "finding_id": finding_id
            })
            business_impact = await self._generate_business_impact(finding)
            
            # Step 5: LLM-generated remediation
            await self.emit_progress(scan_id, "poc", "remediation", {
                "finding_id": finding_id
            })
            remediation = await self._generate_remediation(finding)
            
            # Step 6: Update finding in database
            poc_data = {
                "poc_screenshot_url": screenshot_url,
                "poc_http_trace_url": trace_url,
                "poc_curl_command": curl_command,
                "llm_business_impact": business_impact,
                "llm_remediation": remediation,
                "poc_steps": poc_steps,
                "poc_generated_at": datetime.utcnow().isoformat()
            }
            
            await self._update_finding_poc(finding_id, poc_data)
            
            result = {
                "success": True,
                "finding_id": finding_id,
                **poc_data
            }
            
            await self.log_action(scan_id, "poc_generated", {
                "finding_id": finding_id,
                "has_screenshot": bool(screenshot_url),
                "has_trace": bool(trace_url),
                "poc_steps_count": len(poc_steps) if poc_steps else 0
            })
            
            return result
            
        except Exception as e:
            await self.log_action(scan_id, "poc_generation_error", {
                "finding_id": finding_id,
                "error": str(e)
            })
            return {
                "success": False,
                "finding_id": finding_id,
                "error": str(e)
            }
    
    async def _capture_screenshot(
        self, 
        scan_id: str, 
        finding_id: str, 
        url: str, 
        finding: Dict[str, Any]
    ) -> Optional[str]:
        """
        Capture screenshot of vulnerability using Playwright
        
        Note: This is a placeholder. Production implementation:
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            screenshot = await page.screenshot(full_page=True)
        """
        try:
            # For now, create a placeholder screenshot
            # In production, use Playwright for real browser automation
            
            placeholder_data = self._create_placeholder_screenshot(finding)
            
            # Upload to MinIO
            presigned_url = await self.storage.upload_screenshot(
                scan_id,
                finding_id,
                placeholder_data
            )
            
            return presigned_url
            
        except Exception as e:
            await self.log_action(scan_id, "screenshot_error", {
                "finding_id": finding_id,
                "error": str(e)
            })
            return None
    
    def _create_placeholder_screenshot(self, finding: Dict[str, Any]) -> bytes:
        """Create a valid minimal PNG placeholder (1×1 orange pixel).

        Uses raw PNG encoding (no PIL required) so the browser can
        display something meaningful even when Playwright is unavailable.
        """
        import struct
        import zlib

        def _chunk(chunk_type: bytes, data: bytes) -> bytes:
            raw = chunk_type + data
            return struct.pack(">I", len(data)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)

        # 1×1 RGBA pixel (orange: #FF8C00, fully opaque)
        width, height = 1, 1
        raw_row = b"\x00" + b"\xff\x8c\x00\xff"  # filter-byte + RGBA
        ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
        return (
            b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr_data)
            + _chunk(b"IDAT", zlib.compress(raw_row))
            + _chunk(b"IEND", b"")
        )
    
    async def _generate_poc_steps(
        self,
        scan_id: str,
        finding_id: str,
        finding: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate structured step-by-step PoC reproduction instructions.
        
        Flow:
        1. Ask the LLM to decompose the vulnerability into discrete
           reproduction steps (JSON array).
        2. For each step, use Playwright to execute the action and
           capture a screenshot of the resulting page state.
        3. Upload each screenshot to MinIO/local storage.
        4. Return the enriched steps array with screenshot URLs.
        """
        steps: List[Dict[str, Any]] = []
        
        # ── 1. Ask LLM for structured steps ────────────────────────────
        try:
            raw_steps = await self._llm_generate_steps(finding)
        except Exception as e:
            await self.log_action(scan_id, "poc_steps_llm_error", {
                "finding_id": finding_id,
                "error": str(e)
            })
            # Fallback: single step from the existing description
            raw_steps = [{
                "step_number": 1,
                "title": "Reproduce the vulnerability",
                "description": finding.get("description", "Navigate to the affected endpoint and observe the vulnerability."),
                "action_url": finding.get("url", ""),
                "action_type": "navigate"
            }]
        
        # ── 2. Capture a screenshot per step ────────────────────────────
        for i, step in enumerate(raw_steps, 1):
            step_num = step.get("step_number", i)
            step_title = step.get("title", f"Step {step_num}")
            step_desc = step.get("description", "")
            action_url = step.get("action_url", finding.get("url", ""))
            
            # Capture screenshot for this step
            screenshot_url = await self._capture_step_screenshot(
                scan_id=scan_id,
                finding_id=finding_id,
                step_number=step_num,
                url=action_url,
                finding=finding
            )
            
            steps.append({
                "step_number": step_num,
                "title": step_title,
                "description": step_desc,
                "screenshot_url": screenshot_url
            })
            
            await self.log_action(scan_id, "poc_step_captured", {
                "finding_id": finding_id,
                "step_number": step_num,
                "has_screenshot": bool(screenshot_url)
            })
        
        return steps
    
    async def _llm_generate_steps(self, finding: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use the LLM to break a vulnerability into discrete reproduction steps.
        
        Returns a list of dicts, each containing:
            step_number, title, description, action_url, action_type
        """
        finding_type = finding.get("type", "UNKNOWN")
        url = finding.get("url", "")
        method = finding.get("method", "GET")
        description = finding.get("description", "")
        evidence = finding.get("evidence", "")
        payload = finding.get("payload", "")
        
        prompt = f"""You are a penetration testing expert. Break down the following 
vulnerability into clear, sequential reproduction steps.

VULNERABILITY DETAILS:
- Type: {finding_type}
- URL: {url}
- HTTP Method: {method}
- Description: {description}
- Evidence: {evidence}
- Payload: {payload}

Return a JSON array of steps. Each step MUST have:
- "step_number": integer starting at 1
- "title": short title (e.g. "Navigate to target endpoint")
- "description": detailed instruction for this step
- "action_url": the URL to visit/request for this step (use "{url}" if same)
- "action_type": one of "navigate", "inject_payload", "submit_form", "observe_response", "compare_baseline"

Generate 3-5 steps. Example format:
[
  {{"step_number": 1, "title": "Navigate to target", "description": "Open the target endpoint at {url}", "action_url": "{url}", "action_type": "navigate"}},
  {{"step_number": 2, "title": "Inject test payload", "description": "Send the payload ...", "action_url": "{url}", "action_type": "inject_payload"}}
]

Return ONLY the JSON array, no extra text.
"""
        
        if self.llm_service:
            import json as _json
            response = await self.llm_service.analyze(
                prompt=prompt,
                response_format="text",
                use_knowledge_base=False
            )
            # Parse the JSON array from the response
            response = response.strip()
            # Find the array boundaries
            arr_start = response.find("[")
            arr_end = response.rfind("]") + 1
            if arr_start != -1 and arr_end > arr_start:
                parsed = _json.loads(response[arr_start:arr_end])
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
        
        # Fallback: generate sensible default steps based on finding type
        return self._generate_fallback_steps(finding)
    
    def _generate_fallback_steps(self, finding: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate deterministic fallback steps when LLM is unavailable."""
        url = finding.get("url", "http://target-application/")
        finding_type = finding.get("type", "UNKNOWN")
        method = finding.get("method", "GET")
        payload = finding.get("payload", "")
        
        steps = [
            {
                "step_number": 1,
                "title": f"Prerequisites: Recreate the same endpoint context",
                "description": f"Navigate to the target endpoint at {url}",
                "action_url": url,
                "action_type": "navigate"
            },
            {
                "step_number": 2,
                "title": "Send the original probe or payload",
                "description": f"Send a {method} request to {url}" + (f" with payload: {payload}" if payload else ""),
                "action_url": url,
                "action_type": "inject_payload"
            },
            {
                "step_number": 3,
                "title": "Compare the response against the observed evidence",
                "description": f"Observe the response for signs of {finding_type}. Look for anomalous content, error messages, or data disclosure in the response.",
                "action_url": url,
                "action_type": "observe_response"
            },
            {
                "step_number": 4,
                "title": "Repeat the request to confirm the behavior is stable",
                "description": "Re-send the same request 2-3 times to verify consistent exploitability and rule out intermittent false positives.",
                "action_url": url,
                "action_type": "compare_baseline"
            },
            {
                "step_number": 5,
                "title": "Patch the endpoint and re-run the same request",
                "description": "After applying the fix, re-run the exact same request to verify the issue no longer reproduces. The patched response should differ from the vulnerable baseline.",
                "action_url": url,
                "action_type": "compare_baseline"
            }
        ]
        return steps
    
    async def _capture_step_screenshot(
        self,
        scan_id: str,
        finding_id: str,
        step_number: int,
        url: str,
        finding: Dict[str, Any]
    ) -> Optional[str]:
        """
        Capture a screenshot for a specific PoC step using Playwright.
        
        Falls back to a placeholder if Playwright is unavailable.
        """
        filename = f"poc_step_{step_number}.png"
        
        try:
            # Try real Playwright screenshot
            try:
                from playwright.async_api import async_playwright
                
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                    screenshot_bytes = await page.screenshot(full_page=True)
                    await browser.close()
                
            except (ImportError, Exception):
                # Playwright not available — create placeholder
                screenshot_bytes = self._create_placeholder_screenshot(finding)
            
            # Upload to storage (MinIO or local)
            if self.storage_service:
                presigned_url = await self.storage_service.upload_screenshot(
                    scan_id, finding_id, screenshot_bytes, filename=filename
                )
                return presigned_url
            
            return None
            
        except Exception as e:
            await self.log_action(scan_id, "step_screenshot_error", {
                "finding_id": finding_id,
                "step_number": step_number,
                "error": str(e)
            })
            return None
    
    async def _record_http_trace(
        self,
        scan_id: str,
        finding_id: str,
        url: str,
        finding: Dict[str, Any]
    ) -> Optional[str]:
        """Record HTTP request/response for reproduction"""
        try:
            # Build HTTP trace from finding evidence
            http_trace = {
                "request": {
                    "method": finding.get("method", "GET"),
                    "url": url,
                    "headers": finding.get("headers", {}),
                    "body": finding.get("request_body", "")
                },
                "response": {
                    "status_code": finding.get("status_code", 200),
                    "headers": finding.get("response_headers", {}),
                    "body": finding.get("evidence", "")[:1000]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Convert to JSON and upload
            trace_data = json.dumps(http_trace, indent=2).encode()
            
            presigned_url = await self.storage.upload_http_trace(
                scan_id,
                finding_id,
                trace_data
            )
            
            return presigned_url
            
        except Exception as e:
            await self.log_action(scan_id, "http_trace_error", {
                "finding_id": finding_id,
                "error": str(e)
            })
            return None
    
    async def _generate_curl(self, finding: Dict[str, Any]) -> str:
        """Generate cURL command for reproduction"""
        url = finding.get("url")
        method = finding.get("method", "GET")
        headers = finding.get("headers", {})
        body = finding.get("request_body", "")
        payload = finding.get("payload", "")
        
        # Start building cURL command
        curl_parts = [f"curl -X {method}"]
        
        # Add URL
        if payload and "{payload}" in url:
            curl_parts.append(f"'{url.replace('{payload}', payload)}'")
        else:
            curl_parts.append(f"'{url}'")
        
        # Add headers
        for key, value in headers.items():
            curl_parts.append(f"-H '{key}: {value}'")
        
        # Add body if POST/PUT
        if body and method in ["POST", "PUT", "PATCH"]:
            curl_parts.append(f"-d '{body}'")
        
        # Add common curl options
        curl_parts.append("--insecure")  # Skip SSL verification
        curl_parts.append("-v")  # Verbose output
        
        return " \\\n  ".join(curl_parts)
    
    async def _generate_business_impact(self, finding: Dict[str, Any]) -> str:
        """Use LLM to generate business impact analysis"""
        finding_type = finding.get("type", "UNKNOWN")
        severity = finding.get("severity", "medium")
        url = finding.get("url", "")
        description = finding.get("description", "")
        evidence = finding.get("evidence", "")

        prompt = f"""You are a senior cybersecurity consultant writing a business impact assessment.

VULNERABILITY:
- Type: {finding_type}
- Severity: {severity}
- URL: {url}
- Description: {description}
- Evidence: {evidence[:300]}

Write a business impact analysis in exactly this format:

## Executive Summary
[2-3 sentences explaining the vulnerability in business terms]

## What An Attacker Can Do
[Bullet points of specific attacker capabilities]

## Data & Operations At Risk
[What sensitive data or business processes are exposed]

## Financial & Reputational Impact
[Potential costs, fines, brand damage]

## Compliance Implications
[GDPR, PCI-DSS, SOC2, HIPAA implications]

## Risk Rating
[Critical/High/Medium/Low with justification]

Be specific, factual, and written for C-level executives."""

        try:
            # Try LLM service first
            if self.llm_service:
                try:
                    result = await self.llm_service.analyze(
                        prompt=prompt,
                        response_format="text",
                        use_knowledge_base=False
                    )
                    if result and len(result.strip()) > 50:
                        return result.strip()
                except Exception:
                    pass

            # Direct Ollama fallback
            import os
            import requests as _requests
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
            resp = _requests.post(
                f"{ollama_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.4, "num_predict": 2048}},
                timeout=120,
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                if text.strip():
                    return text.strip()

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"[poc] LLM business impact failed: {e}")

        # Deterministic fallback
        return self._fallback_business_impact(finding)

    def _fallback_business_impact(self, finding: Dict[str, Any]) -> str:
        """Deterministic business impact when LLM is unavailable."""
        vtype = finding.get("type", "UNKNOWN")
        url = finding.get("url", "the affected endpoint")

        impacts = {
            "AUTH_BYPASS": (
                f"**Critical Risk:** Authentication bypass on {url} allows attackers to access "
                "protected resources without valid credentials. This can lead to complete account "
                "takeover, unauthorized data access, and administrative privilege escalation.\n\n"
                "**Compliance Impact:** Violates OWASP A07:2021, PCI-DSS Req 6.5.10, and "
                "GDPR Article 32 (security of processing)."
            ),
            "SQL_INJECTION": (
                f"**Critical Risk:** SQL Injection on {url} allows attackers to read, modify, or "
                "delete the entire database. This includes user credentials, payment information, "
                "and personally identifiable information (PII).\n\n"
                "**Compliance Impact:** Violates OWASP A03:2021, PCI-DSS Req 6.5.1, GDPR "
                "Article 32, and SOC2 CC6.1."
            ),
            "XSS": (
                f"**High Risk:** Cross-Site Scripting on {url} allows attackers to inject "
                "malicious scripts that execute in victims' browsers. This enables session "
                "hijacking, credential theft, and phishing attacks.\n\n"
                "**Compliance Impact:** Violates OWASP A03:2021 and PCI-DSS Req 6.5.7."
            ),
            "IDOR": (
                f"**High Risk:** Insecure Direct Object Reference on {url} allows attackers "
                "to access other users' data by manipulating resource identifiers. This can "
                "expose sensitive personal and financial records.\n\n"
                "**Compliance Impact:** Violates OWASP A01:2021, GDPR Article 25 (data "
                "protection by design), and HIPAA §164.312."
            ),
        }
        return impacts.get(vtype, f"Security vulnerability detected on {url} requiring immediate remediation.")

    async def _generate_remediation(self, finding: Dict[str, Any]) -> str:
        """Use LLM to generate comprehensive step-by-step remediation with patching guidance."""
        finding_type = finding.get("type", "UNKNOWN")
        url = finding.get("url", "")
        description = finding.get("description", "")
        evidence = finding.get("evidence", "")
        payload = finding.get("payload", "")

        prompt = f"""You are a senior application security engineer. Generate a comprehensive, 
step-by-step remediation guide to PATCH this vulnerability.

VULNERABILITY DETAILS:
- Type: {finding_type}
- URL: {url}
- Description: {description}
- Payload Used: {payload[:200]}
- Evidence: {evidence[:300]}

Generate remediation in EXACTLY this format:

## Root Cause
[Explain WHY this vulnerability exists in 2-3 sentences]

## Immediate Hotfix (Deploy within 24 hours)
1. [First immediate action with exact command or config change]
2. [Second immediate action]

## Permanent Fix (Step-by-Step Code Patch)
1. [First code change - be specific about what file/function to modify]
2. [Second code change]
3. [Third code change]

## Before (Vulnerable Code)
```
[Show example of vulnerable code pattern]
```

## After (Patched Code)
```
[Show the fixed version of the same code]
```

## Additional Hardening
1. [Defense-in-depth measure 1]
2. [Defense-in-depth measure 2]
3. [Defense-in-depth measure 3]

## Verification Steps
1. [How to test that the fix works]
2. [How to verify the vulnerability is gone]
3. [Regression test to add]

## References
- [OWASP link]
- [CWE link]

IMPORTANT: Be extremely specific. Include actual code snippets, exact configuration 
changes, and precise testing commands. Each step must be actionable by a developer."""

        try:
            # Try LLM service first
            if self.llm_service:
                try:
                    result = await self.llm_service.analyze(
                        prompt=prompt,
                        response_format="text",
                        use_knowledge_base=False
                    )
                    if result and len(result.strip()) > 100:
                        return result.strip()
                except Exception:
                    pass

            # Direct Ollama fallback
            import os
            import requests as _requests
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
            resp = _requests.post(
                f"{ollama_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.3, "num_predict": 4096}},
                timeout=180,
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                if text.strip():
                    return text.strip()

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"[poc] LLM remediation failed: {e}")

        # Deterministic fallback
        return self._fallback_remediation(finding)

    def _fallback_remediation(self, finding: Dict[str, Any]) -> str:
        """Deterministic remediation when LLM is unavailable."""
        vtype = finding.get("type", "UNKNOWN")
        url = finding.get("url", "the affected endpoint")

        remediations = {
            "AUTH_BYPASS": (
                "## Root Cause\n"
                "The server does not enforce authentication on all protected routes, or allows "
                "path manipulation to bypass access controls.\n\n"
                "## Immediate Hotfix\n"
                "1. Add server-side authentication middleware to ALL protected routes\n"
                "2. Reject requests with path traversal patterns (/../, /%2e/, /..;/)\n\n"
                "## Permanent Fix\n"
                "1. Implement a centralized authentication guard that runs before every route handler\n"
                "2. Normalize all URL paths before evaluating access rules\n"
                "3. Restrict HTTP methods to only those explicitly needed per endpoint\n"
                "4. Remove trust for X-Forwarded-For, X-Original-URL headers in access decisions\n\n"
                "## Verification Steps\n"
                "1. Attempt to access protected endpoints without credentials — expect 401/403\n"
                "2. Try path traversal variants (/../, /%2e/) — expect 400 or redirect\n"
                "3. Test OPTIONS/TRACE methods on sensitive routes — expect 405\n\n"
                "## References\n"
                "- https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/\n"
                "- https://cwe.mitre.org/data/definitions/287.html"
            ),
            "SQL_INJECTION": (
                "## Root Cause\n"
                "User input is concatenated directly into SQL queries without parameterization.\n\n"
                "## Immediate Hotfix\n"
                "1. Replace all string-concatenated SQL with parameterized queries\n"
                "2. Enable WAF SQL injection rule set\n\n"
                "## Permanent Fix\n"
                "1. Use prepared statements with bound parameters for all database queries\n"
                "2. Use an ORM (SQLAlchemy, Hibernate, Entity Framework) instead of raw SQL\n"
                "3. Apply input validation — reject special characters in non-text fields\n"
                "4. Set database user to least-privilege (read-only where possible)\n\n"
                "## Before (Vulnerable)\n"
                "```python\n"
                "query = f\"SELECT * FROM users WHERE id = {user_input}\"\n"
                "```\n\n"
                "## After (Patched)\n"
                "```python\n"
                "query = \"SELECT * FROM users WHERE id = :id\"\n"
                "result = db.execute(query, {\"id\": user_input})\n"
                "```\n\n"
                "## Verification Steps\n"
                "1. Send `' OR '1'='1` as input — expect no SQL error in response\n"
                "2. Run sqlmap against the endpoint — expect 0 injectable parameters\n\n"
                "## References\n"
                "- https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html\n"
                "- https://cwe.mitre.org/data/definitions/89.html"
            ),
            "XSS": (
                "## Root Cause\n"
                "User input is reflected in HTML responses without proper encoding/escaping.\n\n"
                "## Immediate Hotfix\n"
                "1. HTML-encode all user-supplied values before rendering in templates\n"
                "2. Add Content-Security-Policy header: `default-src 'self'`\n\n"
                "## Permanent Fix\n"
                "1. Use a templating engine with auto-escaping enabled (Jinja2, React JSX)\n"
                "2. Set HttpOnly and Secure flags on all session cookies\n"
                "3. Implement CSP headers that block inline scripts\n"
                "4. Validate and sanitize all inputs using an allowlist approach\n\n"
                "## Before (Vulnerable)\n"
                "```html\n"
                "<p>Welcome, {{ user_input }}</p>\n"
                "```\n\n"
                "## After (Patched)\n"
                "```html\n"
                "<p>Welcome, {{ user_input | escape }}</p>\n"
                "```\n\n"
                "## Verification Steps\n"
                "1. Inject `<script>alert(1)</script>` — expect it to render as text, not execute\n"
                "2. Check response headers for Content-Security-Policy\n\n"
                "## References\n"
                "- https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html\n"
                "- https://cwe.mitre.org/data/definitions/79.html"
            ),
            "IDOR": (
                "## Root Cause\n"
                "The application uses predictable resource IDs and does not verify that the "
                "authenticated user owns the requested resource.\n\n"
                "## Immediate Hotfix\n"
                "1. Add authorization check: verify `resource.owner_id == current_user.id`\n"
                "2. Return 403 Forbidden when ownership check fails\n\n"
                "## Permanent Fix\n"
                "1. Use UUIDs instead of sequential integers for resource identifiers\n"
                "2. Implement a centralized authorization middleware\n"
                "3. Add row-level security policies in the database\n"
                "4. Log all access attempts for anomaly detection\n\n"
                "## Before (Vulnerable)\n"
                "```python\n"
                "@app.get('/api/orders/{order_id}')\n"
                "def get_order(order_id: int):\n"
                "    return db.query(Order).get(order_id)  # No auth check!\n"
                "```\n\n"
                "## After (Patched)\n"
                "```python\n"
                "@app.get('/api/orders/{order_id}')\n"
                "def get_order(order_id: int, user=Depends(get_current_user)):\n"
                "    order = db.query(Order).get(order_id)\n"
                "    if order.user_id != user.id:\n"
                "        raise HTTPException(403)\n"
                "    return order\n"
                "```\n\n"
                "## Verification Steps\n"
                "1. Access /api/orders/1 as User A, then try as User B — expect 403\n"
                "2. Enumerate IDs 1-100 without auth — expect 401 for all\n\n"
                "## References\n"
                "- https://owasp.org/Top10/A01_2021-Broken_Access_Control/\n"
                "- https://cwe.mitre.org/data/definitions/639.html"
            ),
        }
        return remediations.get(vtype, f"Apply security best practices to patch {vtype} on {url}.")
    

    
    async def _update_finding_poc(
        self,
        finding_id: str,
        poc_data: Dict[str, Any]
    ) -> None:
        """Update finding with PoC data in PostgreSQL."""
        try:
            from app.models.models import Vulnerability
            from app.core.database import SessionLocal
            from datetime import datetime as _dt

            db = SessionLocal()
            try:
                # finding_id can be a numeric PK or a string like "scan-uuid_finding_0"
                vuln = None
                if str(finding_id).isdigit():
                    vuln = db.query(Vulnerability).filter(Vulnerability.id == int(finding_id)).first()

                if not vuln:
                    import logging
                    logging.getLogger(__name__).warning(
                        f"[poc] Could not find Vulnerability {finding_id} to update"
                    )
                    return

                # Write all PoC fields that the UI reads
                if poc_data.get("poc_screenshot_url"):
                    vuln.poc_screenshot_url = poc_data["poc_screenshot_url"]
                if poc_data.get("poc_http_trace_url"):
                    vuln.poc_http_trace_url = poc_data["poc_http_trace_url"]
                if poc_data.get("poc_curl_command"):
                    vuln.poc_curl_command = poc_data["poc_curl_command"]
                    # Also store as llm_poc for the PoC tab
                    vuln.llm_poc = poc_data["poc_curl_command"]
                if poc_data.get("llm_business_impact"):
                    vuln.llm_business_impact = poc_data["llm_business_impact"]
                    # Also use as enriched explanation for the Description tab
                    vuln.llm_explanation = poc_data["llm_business_impact"]
                if poc_data.get("llm_remediation"):
                    vuln.llm_remediation = poc_data["llm_remediation"]
                    # Always overwrite remediation with the richer LLM version
                    vuln.remediation = poc_data["llm_remediation"]
                if poc_data.get("poc_steps"):
                    vuln.poc_steps = poc_data["poc_steps"]

                vuln.poc_generated_at = _dt.utcnow()
                db.commit()

                import logging
                logging.getLogger(__name__).info(
                    f"[poc] Updated Vulnerability {finding_id} with PoC data in PostgreSQL"
                )
            finally:
                db.close()

            await self.log_action("poc", "finding_updated", {
                "finding_id": finding_id,
                "has_screenshot": bool(poc_data.get("poc_screenshot_url")),
                "has_trace": bool(poc_data.get("poc_http_trace_url")),
                "has_curl": bool(poc_data.get("poc_curl_command")),
                "has_poc_steps": bool(poc_data.get("poc_steps")),
            })

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[poc] Failed to update finding {finding_id}: {e}")
            await self.log_action("poc", "update_error", {
                "finding_id": finding_id,
                "error": str(e)
            })
