"""
Exploit Execution Agent

Responsibilities:
1. Execute planned attacks via Tool Sandbox
2. Session management (cookies, tokens, headers)
3. Parameter fuzzing
4. Capture raw outputs
5. Upload results to MinIO
6. Create Finding nodes in Neo4j
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
    
    async def run(self, scan_id: str, attack_id: Optional[str] = None) -> Dict[str, Any]:
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
        """Get planned attacks from Neo4j"""
        try:
            # Query for all PLANNED attack nodes
            query = """
            MATCH (s:Scan {scan_id: $scan_id})-[:PLANNED_ATTACK]->(a:AttackNode)
            WHERE a.status = 'PLANNED'
            RETURN a
            ORDER BY a.sequence, a.priority DESC
            """
            
            async with self.graph_db.driver.session() as session:
                result = await session.run(query, scan_id=scan_id)
                attacks = [record["a"] async for record in result]
            
            return attacks
            
        except Exception as e:
            await self.log_action(scan_id, "attack_retrieval_error", {"error": str(e)})
            return []
    
    async def _get_attack_node(self, scan_id: str, attack_id: str) -> Dict[str, Any]:
        """Get specific attack node"""
        # Simplified - would query Neo4j for specific attack
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
                "timeout": 300
            })
            
            if result.success:
                # Parse SQLMap output for findings
                findings = self._parse_sqlmap_output(result.output, target_url)
                
                # Create finding nodes in Neo4j
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
                "timeout": 300
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
    
    def _parse_sqlmap_output(self, output: str, url: str) -> List[Dict[str, Any]]:
        """Parse SQLMap output for findings"""
        findings = []
        
        # Simplified parsing - production would use proper SQLMap output parsing
        if "is vulnerable" in output.lower() or "injectable" in output.lower():
            findings.append({
                "type": "SQL_INJECTION",
                "severity": "HIGH",
                "url": url,
                "description": "SQL injection vulnerability detected",
                "evidence": output[:500]
            })
        
        return findings
    
    def _parse_dalfox_output(self, output: str, url: str) -> List[Dict[str, Any]]:
        """Parse Dalfox output for XSS findings"""
        findings = []
        
        try:
            # Dalfox outputs JSON
            data = json.loads(output) if output else []
            for item in data:
                findings.append({
                    "type": "XSS",
                    "severity": "MEDIUM",
                    "url": url,
                    "parameter": item.get("param"),
                    "payload": item.get("payload"),
                    "description": "Cross-Site Scripting (XSS) vulnerability detected",
                    "evidence": item.get("evidence")
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
                "description": "Insecure Direct Object Reference (IDOR) vulnerability",
                "evidence": output[:500]
            })
        
        return findings
    
    def _parse_auth_bypass_output(self, output: str, url: str) -> List[Dict[str, Any]]:
        """Parse auth bypass tester output"""
        findings = []
        
        if "BYPASS_SUCCESSFUL" in output:
            findings.append({
                "type": "AUTH_BYPASS",
                "severity": "CRITICAL",
                "url": url,
                "description": "Authentication bypass vulnerability detected",
                "evidence": output[:500]
            })
        
        return findings
    
    async def _create_finding(self, scan_id: str, attack: Dict[str, Any], finding: Dict[str, Any]) -> None:
        """Create finding node in Neo4j and database"""
        try:
            # Create in Neo4j
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
            
            finding_id = f"{scan_id}_finding_{len(self.findings)}"
            
            async with self.graph_db.driver.session() as session:
                await session.run(query, 
                    attack_id=attack.get("attack_id"),
                    finding_id=finding_id,
                    type=finding.get("type"),
                    severity=finding.get("severity"),
                    url=finding.get("url"),
                    description=finding.get("description")
                )
            
            # Also create in PostgreSQL (Vulnerability model)
            # This would be done via database service
            
        except Exception as e:
            await self.log_action(scan_id, "finding_creation_error", {"error": str(e)})
    
    async def _upload_results(self, scan_id: str) -> None:
        """Upload raw results to MinIO"""
        try:
            results_data = json.dumps({
                "findings": self.findings,
                "session_data": self.session_data,
                "timestamp": datetime.utcnow().isoformat()
            }, indent=2).encode()
            
            await self.storage.upload_to_bucket(
                "rakshaidb-raw",
                f"{scan_id}/executor/results.json",
                results_data,
                "application/json"
            )
        except Exception as e:
            await self.log_action(scan_id, "results_upload_error", {"error": str(e)})
