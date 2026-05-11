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
    
    async def run(self, scan_id: str, finding_id: Optional[str] = None) -> Dict[str, Any]:
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
        Generate comprehensive PoC for a validated finding
        
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
            # Step 1: Capture screenshot
            await self.emit_progress(scan_id, "poc", "screenshot", {
                "finding_id": finding_id
            })
            screenshot_url = await self._capture_screenshot(scan_id, finding_id, url, finding)
            
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
                "has_trace": bool(trace_url)
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
        """Create a placeholder image (in production, use real screenshot)"""
        # This would be replaced with actual Playwright screenshot
        # For now, return empty bytes
        return b"PNG_SCREENSHOT_PLACEHOLDER"
    
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
    
    async def _get_validated_findings(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get all validated findings for a scan"""
        # Query database for findings with status = 'VALIDATED'
        # This is a mock - production would query PostgreSQL
        return []
    
    async def _get_finding(self, scan_id: str, finding_id: str) -> Dict[str, Any]:
        """Get specific finding"""
        return {
            "finding_id": finding_id,
            "type": "SQL_INJECTION",
            "severity": "HIGH",
            "url": "http://example.com/api/test",
            "method": "GET"
        }
    
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
