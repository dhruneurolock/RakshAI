"""
Reconnaissance Agent

Responsibilities:
1. Execute discovery tools (httpx, katana, nuclei, subfinder)
2. Browser automation with Playwright
3. Form discovery
4. Technology detection
5. Create Endpoint nodes in Neo4j
6. Upload raw outputs to MinIO
"""

from typing import Dict, Any, List, Optional
import asyncio
import json
from datetime import datetime

from .base_agent import BaseAgent


class ReconAgent(BaseAgent):
    """Agent responsible for reconnaissance and discovery phase"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.discovered_endpoints = []
        self.technologies = []
    
    async def run(self, scan_id: str) -> Dict[str, Any]:
        """
        Execute reconnaissance workflow
        
        Args:
            scan_id: Scan identifier
            
        Returns:
            Dict with discovered endpoints and technologies
        """
        try:
            await self.emit_progress(scan_id, "recon", "started", {
                "message": "Starting reconnaissance phase"
            })
            
            # Get scan details
            scan = await self._get_scan_details(scan_id)
            target_url = scan.get("target_url")
            
            # Phase 1: HTTP probing
            await self.emit_progress(scan_id, "recon", "http_probing", {
                "message": "Probing HTTP endpoints"
            })
            http_results = await self._http_probe(target_url)
            
            # Phase 2: Web crawling
            await self.emit_progress(scan_id, "recon", "crawling", {
                "message": "Crawling web application"
            })
            crawl_results = await self._web_crawl(target_url)
            
            # Phase 3: Technology detection
            await self.emit_progress(scan_id, "recon", "tech_detect", {
                "message": "Detecting technologies"
            })
            tech_results = await self._detect_technologies(target_url)
            
            # Phase 4: Vulnerability template scanning
            await self.emit_progress(scan_id, "recon", "template_scan", {
                "message": "Running Nuclei templates"
            })
            nuclei_results = await self._nuclei_scan(target_url)
            
            # Phase 5: Form discovery (browser automation)
            await self.emit_progress(scan_id, "recon", "form_discovery", {
                "message": "Discovering forms and inputs"
            })
            form_results = await self._discover_forms(target_url)
            
            # Phase 6: Store in Neo4j
            await self.emit_progress(scan_id, "recon", "graph_update", {
                "message": "Storing results in graph database"
            })
            await self._store_in_graph(scan_id, {
                "http": http_results,
                "crawl": crawl_results,
                "tech": tech_results,
                "nuclei": nuclei_results,
                "forms": form_results
            })
            
            # Phase 7: Upload raw outputs to MinIO
            await self._upload_raw_outputs(scan_id, {
                "http": http_results,
                "crawl": crawl_results,
                "tech": tech_results,
                "nuclei": nuclei_results,
                "forms": form_results
            })
            
            result = {
                "success": True,
                "endpoints_discovered": len(self.discovered_endpoints),
                "technologies": self.technologies,
                "forms_found": len(form_results.get("forms", [])),
                "nuclei_findings": len(nuclei_results.get("findings", []))
            }
            
            await self.emit_progress(scan_id, "recon", "completed", result)
            await self.log_action(scan_id, "recon_completed", result)
            
            return result
            
        except Exception as e:
            await self.handle_error(scan_id, "recon", e)
            raise
    
    async def _http_probe(self, target_url: str) -> Dict[str, Any]:
        """Execute httpx for HTTP probing"""
        try:
            result = await self.tool_sandbox.execute("httpx", {
                "target": target_url,
                "tech_detect": True,
                "status_code": True,
                "title": True,
                "web_server": True,
                "json": True,
                "timeout": 10
            })
            
            if result.success:
                # Parse httpx JSON output
                data = json.loads(result.output) if result.output else {}
                return {
                    "success": True,
                    "url": data.get("url", target_url),
                    "status_code": data.get("status_code"),
                    "title": data.get("title"),
                    "web_server": data.get("webserver"),
                    "tech": data.get("tech", [])
                }
            else:
                return {"success": False, "error": result.error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _web_crawl(self, target_url: str) -> Dict[str, Any]:
        """Execute katana for web crawling"""
        try:
            result = await self.tool_sandbox.execute("katana", {
                "url": target_url,
                "depth": 3,
                "js_crawl": True,
                "form_extraction": True,
                "json": True,
                "timeout": 300
            })
            
            if result.success:
                # Parse katana output
                endpoints = []
                for line in result.output.split("\n"):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            endpoints.append({
                                "url": data.get("url"),
                                "method": data.get("method", "GET"),
                                "source": data.get("source")
                            })
                        except:
                            endpoints.append({"url": line.strip(), "method": "GET"})
                
                self.discovered_endpoints.extend(endpoints)
                
                return {
                    "success": True,
                    "endpoints": endpoints,
                    "count": len(endpoints)
                }
            else:
                return {"success": False, "error": result.error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _detect_technologies(self, target_url: str) -> Dict[str, Any]:
        """Detect technologies using httpx and custom detection"""
        try:
            # Use httpx for tech detection
            result = await self.tool_sandbox.execute("httpx", {
                "target": target_url,
                "tech_detect": True,
                "json": True
            })
            
            if result.success:
                data = json.loads(result.output) if result.output else {}
                technologies = data.get("tech", [])
                self.technologies = technologies
                
                return {
                    "success": True,
                    "technologies": technologies,
                    "count": len(technologies)
                }
            else:
                return {"success": False, "error": result.error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _nuclei_scan(self, target_url: str) -> Dict[str, Any]:
        """Execute Nuclei vulnerability templates"""
        try:
            result = await self.tool_sandbox.execute("nuclei", {
                "target": target_url,
                "templates": ["exposures", "cves", "vulnerabilities"],
                "severity": ["critical", "high", "medium"],
                "json": True,
                "timeout": 300
            })
            
            if result.success:
                findings = []
                for line in result.output.split("\n"):
                    if line.strip():
                        try:
                            finding = json.loads(line)
                            findings.append({
                                "template_id": finding.get("templateID"),
                                "name": finding.get("info", {}).get("name"),
                                "severity": finding.get("info", {}).get("severity"),
                                "matched_at": finding.get("matched-at"),
                                "type": finding.get("type")
                            })
                        except:
                            pass
                
                return {
                    "success": True,
                    "findings": findings,
                    "count": len(findings)
                }
            else:
                return {"success": False, "error": result.error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _discover_forms(self, target_url: str) -> Dict[str, Any]:
        """
        Discover forms using browser automation
        
        Note: This is a placeholder. In production, use Playwright:
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(target_url)
            forms = await page.query_selector_all('form')
        """
        try:
            # For now, use katana's form extraction
            result = await self.tool_sandbox.execute("katana", {
                "url": target_url,
                "form_extraction": True,
                "json": True
            })
            
            if result.success:
                forms = []
                # Parse katana form extraction output
                # This is simplified - actual implementation would parse properly
                forms.append({
                    "url": target_url,
                    "method": "POST",
                    "inputs": []
                })
                
                return {
                    "success": True,
                    "forms": forms,
                    "count": len(forms)
                }
            else:
                return {"success": False, "error": result.error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _store_in_graph(self, scan_id: str, results: Dict[str, Any]) -> None:
        """Store discovered endpoints in Neo4j"""
        try:
            # Add all discovered endpoints to graph
            for endpoint in self.discovered_endpoints:
                await self.graph_db.add_endpoint(scan_id, endpoint)
            
            # Store technologies as graph properties
            # This would be done via a custom query
            
        except Exception as e:
            await self.log_action(scan_id, "graph_storage_error", {"error": str(e)})
    
    async def _upload_raw_outputs(self, scan_id: str, results: Dict[str, Any]) -> None:
        """Upload raw tool outputs to MinIO"""
        try:
            # Upload each result to MinIO
            for tool_name, tool_result in results.items():
                if tool_result.get("success"):
                    data = json.dumps(tool_result, indent=2).encode()
                    
                    await self.storage.upload_to_bucket(
                        "rakshaidb-raw",
                        f"{scan_id}/recon/{tool_name}.json",
                        data,
                        "application/json"
                    )
        except Exception as e:
            await self.log_action(scan_id, "storage_upload_error", {"error": str(e)})
    
    async def _get_scan_details(self, scan_id: str) -> Dict[str, Any]:
        """Get scan details from database"""
        # This would query the database
        # For now, return mock data
        return {
            "scan_id": scan_id,
            "target_url": "http://example.com",
            "scan_type": "full"
        }
