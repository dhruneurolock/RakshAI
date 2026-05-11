"""
Coordinator Agent - LLM-Driven Planning Engine
Orchestrates the entire penetration testing workflow
"""

import logging
from typing import Dict, Any, List
import json
import asyncio

from app.agents.base_agent import BaseAgent
from app.models.models import Scan, ScanStatus
from app.core.database import get_db, SessionLocal

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """
    LAYER 2: Orchestration & Control Plane
    
    Responsibilities:
    - Dynamic Task Decomposition
    - Attack Path Prioritization
    - Agent Scheduling
    - Risk-Based Planning
    - Guardrail Enforcement
    - Adaptive Testing Loop Control
    """
    
    async def run(self, scan_id: str, **kwargs) -> Dict[str, Any]:
        """
        Initialize and orchestrate the complete scan workflow
        
        Workflow:
        1. LLM Strategic Planning
        2. Initialize Attack Graph
        3. Trigger Recon Agent
        4. Monitor & Adapt
        """
        try:
            await self.log_action(scan_id, "initialize", {"status": "starting"})
            
            # Get scan details
            db = SessionLocal()
            try:
                scan = db.query(Scan).filter(Scan.id == scan_id).first()
                if not scan:
                    raise ValueError(f"Scan {scan_id} not found")
                target_url = scan.target_url
                policy = scan.policy or {}
            finally:
                db.close()
            
            # Update scan status
            await self.update_scan_status(scan_id, ScanStatus.PLANNING)
            
            # LLM-Driven Strategic Planning
            strategy = await self.create_attack_strategy(target_url, policy)
            
            # Initialize Attack Graph
            await self.initialize_attack_graph(scan_id, strategy)
            
            # Trigger Recon Agent
            await self.trigger_recon_agent(scan_id, target_url, strategy)
            
            # Start adaptive monitoring loop
            await self.start_adaptive_loop(scan_id)
            
            return {
                "status": "success",
                "strategy": strategy,
                "scan_id": scan_id
            }
            
        except Exception as e:
            await self.handle_error(scan_id, e)
            raise
    
    async def create_attack_strategy(
        self, 
        target_url: str, 
        policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to create intelligent attack strategy
        
        Args:
            target_url: Target URL to analyze
            policy: Security policy constraints
            
        Returns:
            Attack strategy dictionary
        """
        logger.info(f"Creating attack strategy for {target_url}")
        
        # Load knowledge base context
        kb_context = await self.load_knowledge_base_context()
        
        prompt = f"""
Analyze the target URL and create a penetration testing strategy.

Target: {target_url}
Policy Constraints: {json.dumps(policy, indent=2)}

Knowledge Base Context:
{kb_context}

Based on the URL pattern and common vulnerabilities:
1. What type of application is this likely to be?
2. What OWASP Top 10:2025 categories are most relevant?
3. What reconnaissance tools should run first?
4. What is the priority order for vulnerability testing?
5. What are likely authentication mechanisms?

Provide your analysis in JSON format:
{{
    "app_type": "type of application",
    "likely_auth": "authentication mechanism",
    "priority_categories": ["OWASP categories in order"],
    "recon_tools": ["tools to use"],
    "estimated_endpoints": "number estimate",
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "attack_vectors": [
        {{
            "type": "vulnerability type",
            "priority": 1-100,
            "rationale": "why this is priority"
        }}
    ]
}}
"""
        
        # Call LLM for strategic planning (bounded wait)
        if self.llm_service is None:
            return {
                "app_type": "web_application",
                "likely_auth": "unknown",
                "priority_categories": ["A01", "A03", "A05"],
                "recon_tools": ["httpx", "katana"],
                "estimated_endpoints": "unknown",
                "risk_level": "MEDIUM",
                "attack_vectors": [
                    {"type": "access_control", "priority": 90, "rationale": "common high-impact class"},
                    {"type": "injection", "priority": 85, "rationale": "broad web exposure"},
                ],
            }

        try:
            strategy = await asyncio.wait_for(
                self.llm_service.analyze(prompt, response_format="json"),
                timeout=25,
            )
        except Exception:
            strategy = {
                "app_type": "web_application",
                "likely_auth": "unknown",
                "priority_categories": ["A01", "A03", "A05"],
                "recon_tools": ["httpx", "katana"],
                "estimated_endpoints": "unknown",
                "risk_level": "MEDIUM",
                "attack_vectors": [
                    {"type": "access_control", "priority": 90, "rationale": "common high-impact class"},
                    {"type": "injection", "priority": 85, "rationale": "broad web exposure"},
                ],
            }
        
        logger.info(f"Generated strategy: {strategy.get('priority_categories')}")
        
        return strategy
    
    async def initialize_attack_graph(
        self, 
        scan_id: str, 
        strategy: Dict[str, Any]
    ) -> None:
        """
        Create empty attack graph in Neo4j
        
        Args:
            scan_id: Scan identifier
            strategy: Attack strategy from LLM
        """
        logger.info(f"Initializing attack graph for scan {scan_id}")
        
        # Create scan node in graph database
        await self.graph_db.execute(
            """
            CREATE (scan:Scan {
                id: $scan_id,
                created_at: datetime(),
                strategy: $strategy,
                status: 'INITIALIZING'
            })
            """,
            {"scan_id": scan_id, "strategy": json.dumps(strategy)}
        )
        
        await self.log_action(scan_id, "graph_initialized", {"nodes": 1})
    
    async def trigger_recon_agent(
        self,
        scan_id: str,
        target_url: str,
        strategy: Dict[str, Any]
    ) -> None:
        """
        Trigger Recon Agent via message bus
        
        Args:
            scan_id: Scan identifier
            target_url: Target URL
            strategy: Attack strategy
        """
        logger.info(f"Triggering recon agent for scan {scan_id}")
        
        await self.redis_client.publish(
            "agent:recon:start",
            {
                "scan_id": scan_id,
                "target_url": target_url,
                "tools": strategy.get("recon_tools", ["httpx", "katana"]),
                "depth": strategy.get("crawl_depth", 3)
            }
        )
        
        await self.update_scan_status(scan_id, ScanStatus.DISCOVERING)
    
    async def start_adaptive_loop(self, scan_id: str) -> None:
        """
        Start adaptive testing loop monitoring
        
        This runs continuously:
        - Monitor attack graph for unexplored paths
        - Re-prioritize based on findings
        - Trigger new attacks based on discoveries
        """
        logger.info(f"Starting adaptive loop for scan {scan_id}")
        
        # Schedule periodic check (every 30 seconds)
        await self.redis_client.publish(
            "scheduler:adaptive_check",
            {
                "scan_id": scan_id,
                "interval": 30
            }
        )
    
    async def adaptive_check(self, scan_id: str) -> None:
        """
        Check attack graph and adapt strategy
        
        While unexplored attack paths exist:
            Plan → Execute → Validate → Update Graph → Reprioritize
        """
        # Query graph for unexplored endpoints
        result = await self.graph_db.execute(
            """
            MATCH (scan:Scan {id: $scan_id})-[:DISCOVERED]->(e:Endpoint)
            WHERE NOT EXISTS((scan)-[:PLANNED_ATTACK]->(:AttackNode)-[:TARGETS]->(e))
            RETURN e
            LIMIT 10
            """,
            {"scan_id": scan_id}
        )
        
        unexplored = result.get("e", [])
        
        if unexplored:
            logger.info(f"Found {len(unexplored)} unexplored endpoints")
            
            # LLM re-prioritization based on current findings
            findings = await self.get_current_findings(scan_id)
            new_strategy = await self.llm_service.reprioritize(
                unexplored_endpoints=unexplored,
                current_findings=findings
            )
            
            # Trigger strategy agent for new targets
            await self.redis_client.publish(
                "agent:strategy:replan",
                {
                    "scan_id": scan_id,
                    "new_targets": unexplored,
                    "strategy": new_strategy
                }
            )
        else:
            # No more unexplored paths - finalize scan
            await self.finalize_scan(scan_id)
    
    async def finalize_scan(self, scan_id: str) -> None:
        """Finalize scan and trigger reporting"""
        logger.info(f"Finalizing scan {scan_id}")
        
        await self.update_scan_status(scan_id, ScanStatus.AGGREGATING)
        
        # Trigger report generation
        await self.redis_client.publish(
            "agent:report:generate",
            {"scan_id": scan_id}
        )
    
    async def update_scan_status(self, scan_id: str, status: ScanStatus) -> None:
        """Update scan status in database"""
        db = SessionLocal()
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = status
                db.commit()
        finally:
            db.close()
    
    async def load_knowledge_base_context(self) -> str:
        """Load relevant context from knowledge base"""
        # Load OWASP Top 10 summaries from YAML files
        # This will be enhanced with vector DB RAG later
        return """
        OWASP Top 10:2025:
        - A01: Broken Access Control (IDOR, privilege escalation)
        - A02: Cryptographic Failures (weak encryption, exposed secrets)
        - A03: Injection (SQLi, XSS, Command Injection)
        - A04: Insecure Design (logic flaws, business logic bypass)
        - A05: Security Misconfiguration (default configs, verbose errors)
        - A06: Vulnerable and Outdated Components
        - A07: Identification and Authentication Failures
        - A08: Software and Data Integrity Failures
        - A09: Security Logging and Monitoring Failures
        - A10: Server-Side Request Forgery (SSRF)
        """
    
    async def get_current_findings(self, scan_id: str) -> List[Dict]:
        """Get validated findings so far"""
        db = SessionLocal()
        try:
            from app.models.models import Vulnerability
            findings = db.query(Vulnerability).filter(
                Vulnerability.scan_id == scan_id,
                Vulnerability.status == "VALIDATED"
            ).all()
            
            return [
                {
                    "type": f.vulnerability_type,
                    "severity": f.severity,
                    "endpoint": f.endpoint
                }
                for f in findings
            ]
        finally:
            db.close()
