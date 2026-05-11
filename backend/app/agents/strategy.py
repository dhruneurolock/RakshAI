"""
Attack Strategy Agent

Responsibilities:
1. Analyze discovered endpoints with LLM
2. Prioritize attack vectors (IDOR, XSS, SQLi, etc.)
3. Create AttackNode relationships in Neo4j
4. Consider authentication requirements
5. Generate attack sequences based on OWASP Top 10
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from .base_agent import BaseAgent


class AttackStrategyAgent(BaseAgent):
    """Agent responsible for LLM-powered threat modeling and attack planning"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.attack_nodes = []
    
    async def run(self, scan_id: str) -> Dict[str, Any]:
        """
        Execute attack strategy planning
        
        Args:
            scan_id: Scan identifier
            
        Returns:
            Dict with planned attacks
        """
        try:
            await self.emit_progress(scan_id, "strategy", "started", {
                "message": "Starting attack strategy planning"
            })
            
            # Phase 1: Get discovered endpoints from graph
            await self.emit_progress(scan_id, "strategy", "loading_endpoints", {
                "message": "Loading discovered endpoints"
            })
            endpoints = await self._get_discovered_endpoints(scan_id)
            
            if not endpoints:
                return {
                    "success": False,
                    "error": "No endpoints discovered",
                    "attacks_planned": 0
                }
            
            # Phase 2: LLM analysis of endpoints
            await self.emit_progress(scan_id, "strategy", "llm_analysis", {
                "message": f"Analyzing {len(endpoints)} endpoints with LLM"
            })
            threat_model = await self._create_threat_model(endpoints)
            
            # Phase 3: Prioritize attack vectors
            await self.emit_progress(scan_id, "strategy", "prioritization", {
                "message": "Prioritizing attack vectors"
            })
            prioritized_attacks = await self._prioritize_attacks(threat_model)
            
            # Phase 4: Check authentication requirements
            await self.emit_progress(scan_id, "strategy", "auth_analysis", {
                "message": "Analyzing authentication requirements"
            })
            auth_strategy = await self._analyze_authentication(endpoints)
            
            # Phase 5: Create attack nodes in Neo4j
            await self.emit_progress(scan_id, "strategy", "graph_update", {
                "message": "Creating attack plan in graph database"
            })
            await self._create_attack_nodes(scan_id, prioritized_attacks)
            
            # Phase 6: Store strategy in database
            strategy_doc = {
                "threat_model": threat_model,
                "prioritized_attacks": prioritized_attacks,
                "auth_strategy": auth_strategy,
                "total_attacks": len(prioritized_attacks),
                "created_at": datetime.utcnow().isoformat()
            }
            await self._store_strategy(scan_id, strategy_doc)
            
            result = {
                "success": True,
                "endpoints_analyzed": len(endpoints),
                "attacks_planned": len(prioritized_attacks),
                "high_priority_attacks": len([a for a in prioritized_attacks if a.get("priority", 0) >= 80]),
                "auth_required": auth_strategy.get("required", False)
            }
            
            await self.emit_progress(scan_id, "strategy", "completed", result)
            await self.log_action(scan_id, "strategy_completed", result)
            
            return result
            
        except Exception as e:
            await self.handle_error(scan_id, "strategy", e)
            raise
    
    async def _get_discovered_endpoints(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get discovered endpoints from Neo4j"""
        try:
            # Query Neo4j for endpoints
            endpoints = await self.graph_db.get_scan_endpoints(scan_id)
            return endpoints
            
        except Exception as e:
            await self.log_action(scan_id, "endpoint_retrieval_error", {"error": str(e)})
            return []
    
    async def _create_threat_model(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to create threat model"""
        try:
            # Prepare endpoint summary for LLM
            endpoint_summary = self._summarize_endpoints(endpoints)
            
            prompt = f"""Analyze these web application endpoints and create a threat model:

Endpoints discovered:
{endpoint_summary}

Based on OWASP Top 10, identify:
1. Potential injection points (SQL, XSS, Command Injection)
2. Broken access control opportunities (IDOR, privilege escalation)
3. Authentication/authorization bypass possibilities
4. Sensitive data exposure risks
5. Security misconfiguration indicators

Return a JSON threat model with:
{{
    "owasp_categories": [list of applicable OWASP categories],
    "injection_points": [list of endpoints vulnerable to injection],
    "access_control_targets": [list of endpoints for IDOR/access control testing],
    "auth_bypass_candidates": [list of endpoints to test for auth bypass],
    "sensitive_endpoints": [list of endpoints handling sensitive data],
    "risk_score": 0-100
}}
"""
            
            result = await self.llm_service.analyze(
                prompt=prompt,
                response_format="json",
                use_knowledge_base=True
            )
            
            # Parse LLM response
            try:
                threat_model = json.loads(result)
            except:
                # Fallback to basic threat model
                threat_model = self._create_basic_threat_model(endpoints)
            
            return threat_model
            
        except Exception as e:
            await self.log_action("llm_analysis", "error", {"error": str(e)})
            return self._create_basic_threat_model(endpoints)
    
    def _summarize_endpoints(self, endpoints: List[Dict[str, Any]]) -> str:
        """Create text summary of endpoints for LLM"""
        summary_lines = []
        
        for i, endpoint in enumerate(endpoints[:50], 1):  # Limit to 50 for token budget
            url = endpoint.get("url", "")
            method = endpoint.get("method", "GET")
            params = endpoint.get("params", {})
            
            line = f"{i}. {method} {url}"
            if params:
                line += f" (params: {', '.join(params.keys())})"
            
            summary_lines.append(line)
        
        if len(endpoints) > 50:
            summary_lines.append(f"... and {len(endpoints) - 50} more endpoints")
        
        return "\n".join(summary_lines)
    
    def _create_basic_threat_model(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback threat model without LLM"""
        injection_points = []
        access_control_targets = []
        auth_bypass_candidates = []
        sensitive_endpoints = []
        
        for endpoint in endpoints:
            url = endpoint.get("url", "").lower()
            params = endpoint.get("params", {})
            
            # Detect injection points
            if params or "search" in url or "query" in url:
                injection_points.append(endpoint)
            
            # Detect IDOR candidates (endpoints with IDs)
            if any(x in url for x in ["/id/", "/user/", "/order/", "/account/"]):
                access_control_targets.append(endpoint)
            
            # Detect auth bypass candidates
            if any(x in url for x in ["/login", "/auth", "/admin", "/api/"]):
                auth_bypass_candidates.append(endpoint)
            
            # Detect sensitive endpoints
            if any(x in url for x in ["/password", "/credit", "/payment", "/ssn"]):
                sensitive_endpoints.append(endpoint)
        
        return {
            "owasp_categories": ["A01-Broken-Access-Control", "A03-Injection"],
            "injection_points": injection_points[:10],
            "access_control_targets": access_control_targets[:10],
            "auth_bypass_candidates": auth_bypass_candidates[:10],
            "sensitive_endpoints": sensitive_endpoints[:10],
            "risk_score": 70
        }
    
    async def _prioritize_attacks(self, threat_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize and sequence attacks"""
        attacks = []
        
        # Priority 1: Authentication bypass (must test first)
        for endpoint in threat_model.get("auth_bypass_candidates", []):
            attacks.append({
                "type": "AUTH_BYPASS",
                "target": endpoint,
                "priority": 95,
                "tools": ["auth_bypass_tester", "jwt_tool"],
                "sequence": 1
            })
        
        # Priority 2: Broken access control (IDOR)
        for endpoint in threat_model.get("access_control_targets", []):
            attacks.append({
                "type": "IDOR",
                "target": endpoint,
                "priority": 85,
                "tools": ["idor_tester"],
                "sequence": 2
            })
        
        # Priority 3: SQL Injection
        for endpoint in threat_model.get("injection_points", []):
            attacks.append({
                "type": "SQLI",
                "target": endpoint,
                "priority": 80,
                "tools": ["sqlmap"],
                "sequence": 3
            })
        
        # Priority 4: XSS
        for endpoint in threat_model.get("injection_points", []):
            attacks.append({
                "type": "XSS",
                "target": endpoint,
                "priority": 70,
                "tools": ["dalfox", "xsstrike"],
                "sequence": 4
            })
        
        # Sort by priority
        attacks.sort(key=lambda x: x["priority"], reverse=True)
        
        return attacks
    
    async def _analyze_authentication(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze authentication requirements"""
        auth_endpoints = [
            ep for ep in endpoints 
            if any(x in ep.get("url", "").lower() for x in ["/login", "/auth", "/signin"])
        ]
        
        return {
            "required": len(auth_endpoints) > 0,
            "login_endpoints": auth_endpoints,
            "strategy": "test_auth_bypass_first" if auth_endpoints else "direct_testing"
        }
    
    async def _create_attack_nodes(self, scan_id: str, attacks: List[Dict[str, Any]]) -> None:
        """Create attack nodes in Neo4j"""
        try:
            for i, attack in enumerate(attacks):
                attack_node = await self.graph_db.create_attack_node(
                    scan_id=scan_id,
                    attack_data={
                        "attack_id": f"{scan_id}_attack_{i}",
                        "type": attack["type"],
                        "priority": attack["priority"],
                        "tools": attack["tools"],
                        "sequence": attack["sequence"],
                        "status": "PLANNED",
                        "target_url": attack["target"].get("url")
                    }
                )
                self.attack_nodes.append(attack_node)
                
        except Exception as e:
            await self.log_action(scan_id, "attack_node_creation_error", {"error": str(e)})
    
    async def _store_strategy(self, scan_id: str, strategy_doc: Dict[str, Any]) -> None:
        """Store strategy in database"""
        # This would update the Scan model's strategy field
        # For now, just log it
        await self.log_action(scan_id, "strategy_created", {
            "total_attacks": strategy_doc["total_attacks"]
        })
