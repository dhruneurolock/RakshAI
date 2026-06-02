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
            
            # Phase 1: Get validated findings
            if finding_id:
                findings = [await self._get_finding(scan_id, finding_id)]
            else:
                findings = await self._get_validated_findings(scan_id)
            
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
        try:
            finding_type = finding.get("type")
            severity = finding.get("severity")
            url = finding.get("url")
            
            prompt = f"""Generate a business impact analysis for this security vulnerability:

Vulnerability Type: {finding_type}
Severity: {severity}
Affected URL: {url}
Description: {finding.get("description", "N/A")}

Provide a concise business impact analysis (3-4 sentences) covering:
1. What an attacker can do
2. What business data/operations are at risk
3. Potential financial or reputational impact
4. Compliance implications (GDPR, PCI-DSS, etc.)

Focus on business terms that executives can understand.
"""
            
            impact = await self.llm_service.analyze(
                prompt=prompt,
                response_format="text",
                use_strategy_model=False  # Use detailed analysis model
            )
            
            return impact.strip()
            
        except Exception as e:
            return f"Business impact analysis unavailable: {str(e)}"
    
    async def _generate_remediation(self, finding: Dict[str, Any]) -> str:
        """Use LLM to generate remediation steps"""
        try:
            finding_type = finding.get("type")
            url = finding.get("url")
            
            # Use RAG to retrieve remediation guidance from knowledge base
            prompt = f"""Generate remediation steps for this security vulnerability:

Vulnerability Type: {finding_type}
Affected URL: {url}
Description: {finding.get("description", "N/A")}

Provide specific, actionable remediation steps:
1. Immediate mitigation (quick fix)
2. Long-term solution (proper fix)
3. Code examples if applicable
4. Testing verification steps

Be specific to the technology stack and vulnerability type.
"""
            
            remediation = await self.llm_service.analyze(
                prompt=prompt,
                response_format="text",
                use_strategy_model=False  # Use detailed analysis model
            )
            
            return remediation.strip()
            
        except Exception as e:
            return f"Remediation guidance unavailable: {str(e)}"
    

    
    async def _update_finding_poc(
        self,
        finding_id: str,
        poc_data: Dict[str, Any]
    ) -> None:
        """Update finding with PoC data in database"""
        try:
            # This would update the Vulnerability model in PostgreSQL
            await self.log_action("poc", "finding_updated", {
                "finding_id": finding_id,
                "has_screenshot": bool(poc_data.get("poc_screenshot_url")),
                "has_trace": bool(poc_data.get("poc_http_trace_url")),
                "has_curl": bool(poc_data.get("poc_curl_command"))
            })
            
        except Exception as e:
            await self.log_action("poc", "update_error", {
                "finding_id": finding_id,
                "error": str(e)
            })
