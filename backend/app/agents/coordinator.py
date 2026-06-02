"""
Coordinator Agent - Orchestrates the entire agent-driven pentesting pipeline
using LangGraph for stateful, graph-based execution.

Graph topology (linear with future conditional-edge support):

  [planning] → [recon] → [strategy] → [executor] → [validator] → [poc] → END

All inter-agent data flows through:
  - PentestState  : the LangGraph shared state (in-memory, per scan)
  - PostgreSQL    : persistent Scan.strategy JSON and Vulnerability tables
  - Redis Pub/Sub : real-time progress events pushed to the UI
"""

import logging
from typing import Dict, Any, List, TypedDict
import json
import asyncio

# ── LangGraph ───────────────────────────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END
    _LANGGRAPH_AVAILABLE = True
except ImportError:
    StateGraph, END = None, None
    _LANGGRAPH_AVAILABLE = False

from app.agents.base_agent import BaseAgent
from app.models.models import Scan, ScanStatus, Endpoint, Vulnerability
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# Shared State Schema
# Each node receives the full state and returns only the keys it updates.
# LangGraph merges the returned dict back into the global state.
# ────────────────────────────────────────────────────────────────────────────

class PentestState(TypedDict):
    """Typed state shared across all pipeline nodes."""
    # Core identifiers (set once in planning node, read-only afterwards)
    scan_id: str            # UUID used by all downstream agents
    scan_db_id: str         # Original DB PK passed in from Celery task
    target_url: str
    policy: Dict[str, Any]

    # Node outputs (each node populates its own key)
    strategy: Dict[str, Any]        # planning node
    recon: Dict[str, Any]           # recon node
    strategy_plan: Dict[str, Any]   # strategy node
    execution: Dict[str, Any]       # executor node
    validation: Dict[str, Any]      # validator node
    poc: Dict[str, Any]             # poc node

    # Control flags for future conditional edges
    new_paths_found: bool           # executor → recon loop trigger
    validation_failed: bool         # validator → strategy loop trigger


# ────────────────────────────────────────────────────────────────────────────
# Coordinator Agent
# ────────────────────────────────────────────────────────────────────────────

class CoordinatorAgent(BaseAgent):
    """
    LAYER 2: Orchestration & Control Plane (LangGraph-powered)

    Builds and compiles a LangGraph StateGraph at runtime and invokes it
    asynchronously. Each pipeline phase is an async node in the graph:

        planning → recon → strategy → executor → validator → poc → END

    If langgraph is not installed, falls back to the original sequential
    implementation so the service remains functional.
    """

    # ── Public entry point ──────────────────────────────────────────────────

    async def run(self, scan_id: str, **kwargs) -> Dict[str, Any]:
        """
        Run the complete agent pipeline end-to-end.

        Args:
            scan_id: The DB primary key (Scan.id) as a string, or UUID.
        """
        try:
            await self.log_action(scan_id, "initialize", {"status": "starting"})

            if _LANGGRAPH_AVAILABLE:
                return await self._run_with_langgraph(scan_id)
            else:
                logger.warning(
                    "langgraph not installed — falling back to sequential execution. "
                    "Install with: pip install langgraph"
                )
                return await self._run_sequential_fallback(scan_id)

        except Exception as e:
            await self.handle_error(scan_id, e)
            raise

    # ── LangGraph execution path ────────────────────────────────────────────

    async def _run_with_langgraph(self, scan_id: str) -> Dict[str, Any]:
        """Build and invoke the LangGraph state machine."""
        logger.info(f"[{scan_id}] Starting LangGraph pipeline")

        # ── 1. Build the graph ──────────────────────────────────────────────
        graph = self._build_graph()

        # ── 2. Seed the initial state ───────────────────────────────────────
        initial_state: PentestState = {
            "scan_db_id": scan_id,
            "scan_id": scan_id,        # will be replaced by UUID in planning
            "target_url": "",
            "policy": {},
            "strategy": {},
            "recon": {},
            "strategy_plan": {},
            "execution": {},
            "validation": {},
            "poc": {},
            "new_paths_found": False,
            "validation_failed": False,
        }

        # ── 3. Invoke the graph (async) ─────────────────────────────────────
        final_state: PentestState = await graph.ainvoke(initial_state)

        logger.info(f"[{final_state['scan_id']}] LangGraph pipeline completed")

        return {
            "status": "success",
            "scan_id": final_state["scan_id"],
            "strategy": final_state["strategy"],
            "recon": final_state["recon"],
            "strategy_plan": final_state["strategy_plan"],
            "execution": final_state["execution"],
            "validation": final_state["validation"],
            "poc": final_state["poc"],
        }

    def _build_graph(self) -> Any:
        """
        Construct and compile the LangGraph StateGraph.

        Current topology:
            planning → recon → strategy → executor → validator → poc → END

        Future conditional edges can be added here:
            - executor  → recon     (if new_paths_found)
            - validator → strategy  (if validation_failed)
        """
        workflow = StateGraph(PentestState)

        # ── Register nodes ──────────────────────────────────────────────────
        workflow.add_node("planning",  self._node_planning)
        workflow.add_node("recon",     self._node_recon)
        workflow.add_node("strategy",  self._node_strategy)
        workflow.add_node("executor",  self._node_executor)
        workflow.add_node("validator", self._node_validator)
        workflow.add_node("poc",       self._node_poc)

        # ── Set entry point ─────────────────────────────────────────────────
        workflow.set_entry_point("planning")

        # ── Linear edges (Phase 1 — feature parity with old coordinator) ────
        workflow.add_edge("planning",  "recon")
        workflow.add_edge("recon",     "strategy")
        workflow.add_edge("strategy",  "executor")
        workflow.add_edge("executor",  "validator")
        workflow.add_edge("validator", "poc")
        workflow.add_edge("poc",       END)

        # ── Future: Conditional edges (Phase 2 — uncomment to enable) ───────
        # workflow.add_conditional_edges(
        #     "executor",
        #     self._route_after_executor,
        #     {"recon": "recon", "validator": "validator"},
        # )
        # workflow.add_conditional_edges(
        #     "validator",
        #     self._route_after_validator,
        #     {"strategy": "strategy", "poc": "poc"},
        # )

        return workflow.compile()

    # ── Graph Node Implementations ──────────────────────────────────────────

    async def _node_planning(self, state: PentestState) -> Dict[str, Any]:
        """
        Node 1 — Planning
        Loads scan from DB, resolves the UUID, initialises the Attack graph
        node, and runs LLM-based strategic analysis.
        """
        scan_db_id = state["scan_db_id"]
        logger.info(f"[planning] Loading scan {scan_db_id} from DB")

        db = SessionLocal()
        try:
            if str(scan_db_id).isdigit():
                scan = db.query(Scan).filter(Scan.id == int(scan_db_id)).first()
            else:
                scan = db.query(Scan).filter(Scan.scan_id == scan_db_id).first()

            if not scan:
                raise ValueError(f"Scan {scan_db_id} not found in database")

            target_url = scan.target_url
            scan_uuid  = scan.scan_id
            policy     = scan.policy or {}
        finally:
            db.close()

        # Status → RUNNING / planning
        await self.update_scan_status(scan_uuid, ScanStatus.RUNNING)
        await self.update_scan_phase(scan_uuid, "planning")

        # Initialise Attack graph node for this scan
        if self.graph_db:
            try:
                await self.graph_db.create_scan_node(scan_uuid, {
                    "target_url": target_url,
                    "status": "RUNNING",
                    "policy": policy,
                })
            except Exception as g_err:
                logger.warning(f"[planning] Attack graph node creation failed: {g_err}")

        # LLM-based strategic analysis
        strategy = await self.create_attack_strategy(target_url, policy)

        # Persist strategy to Scan record
        db = SessionLocal()
        try:
            scan = db.query(Scan).filter(Scan.scan_id == scan_uuid).first()
            if scan:
                scan.strategy = {"agent_strategy": strategy}
                db.commit()
        finally:
            db.close()

        logger.info(f"[planning] Strategy generated for {target_url}: "
                    f"priority_categories={strategy.get('priority_categories')}")

        # Return only the keys this node owns
        return {
            "scan_id":    scan_uuid,
            "target_url": target_url,
            "policy":     policy,
            "strategy":   strategy,
        }

    async def _node_recon(self, state: PentestState) -> Dict[str, Any]:
        """
        Node 2 — Reconnaissance
        Crawls the target, discovers endpoints, and stores them in PostgreSQL.
        """
        scan_id    = state["scan_id"]
        target_url = state["target_url"]
        policy     = state["policy"]

        await self.update_scan_phase(scan_id, "discovering")
        logger.info(f"[recon] Launching ReconAgent for scan {scan_id}")

        from app.agents.recon import ReconAgent
        agent = ReconAgent(agent_id=f"recon-{scan_id[:8]}")
        await agent.initialize()
        result = await agent.run(scan_id, target_url=target_url, policy=policy)
        await agent.cleanup()

        logger.info(f"[recon] Completed: {result.get('endpoints_discovered', 0)} endpoints discovered")

        return {"recon": result}

    async def _node_strategy(self, state: PentestState) -> Dict[str, Any]:
        """
        Node 3 — Attack Strategy
        Builds an OWASP-mapped attack plan from discovered endpoints.
        """
        scan_id = state["scan_id"]

        await self.update_scan_phase(scan_id, "strategizing")
        logger.info(f"[strategy] Launching AttackStrategyAgent for scan {scan_id}")

        from app.agents.strategy import AttackStrategyAgent
        agent = AttackStrategyAgent(agent_id=f"strategy-{scan_id[:8]}")
        await agent.initialize()
        result = await agent.run(scan_id)
        await agent.cleanup()

        logger.info(f"[strategy] Completed: {result.get('attacks_planned', 0)} attacks planned")

        return {"strategy_plan": result}

    async def _node_executor(self, state: PentestState) -> Dict[str, Any]:
        """
        Node 4 — Exploit Execution
        Sends payloads to the target and collects raw findings.
        Sets `new_paths_found` flag to True if the executor discovers
        endpoints that were not in the original recon surface (future loop).
        """
        scan_id = state["scan_id"]

        await self.update_scan_phase(scan_id, "exploiting")
        logger.info(f"[executor] Launching ExploitExecutionAgent for scan {scan_id}")

        from app.agents.executor import ExploitExecutionAgent
        agent = ExploitExecutionAgent(agent_id=f"executor-{scan_id[:8]}")
        await agent.initialize()
        result = await agent.run(scan_id)
        await agent.cleanup()

        findings_count = result.get("findings_discovered", 0)
        logger.info(f"[executor] Completed: {findings_count} raw findings discovered")

        # Future hook: detect new paths and set flag to trigger recon loop
        new_paths_found = bool(result.get("new_paths", []))

        return {
            "execution":      result,
            "new_paths_found": new_paths_found,
        }

    async def _node_validator(self, state: PentestState) -> Dict[str, Any]:
        """
        Node 5 — Validation
        Re-executes each raw finding 3× and applies the 85 % confidence
        threshold to filter false positives.
        Sets `validation_failed` if confidence is globally low (future loop).
        """
        scan_id = state["scan_id"]

        await self.update_scan_phase(scan_id, "validating")
        logger.info(f"[validator] Launching ValidationAgent for scan {scan_id}")

        from app.agents.validator import ValidationAgent
        agent = ValidationAgent(agent_id=f"validator-{scan_id[:8]}")
        await agent.initialize()
        result = await agent.run(scan_id)
        await agent.cleanup()

        validated_count = result.get("validated", 0)
        logger.info(f"[validator] Completed: {validated_count} findings confirmed")

        # Future hook: if validation pass-rate is very low, flag for re-strategy
        validation_failed = validated_count == 0 and state["execution"].get("findings_discovered", 0) > 0

        return {
            "validation":       result,
            "validation_failed": validation_failed,
        }

    async def _node_poc(self, state: PentestState) -> Dict[str, Any]:
        """
        Node 6 — Proof-of-Concept Generation
        Generates reproducible PoCs and LLM-powered impact explanations
        for every validated finding.
        """
        scan_id = state["scan_id"]

        await self.update_scan_phase(scan_id, "generating_poc")
        logger.info(f"[poc] Launching PoCAgent for scan {scan_id}")

        from app.agents.poc_generator import PoCAgent
        agent = PoCAgent(agent_id=f"poc-{scan_id[:8]}")
        await agent.initialize()
        result = await agent.run(scan_id)
        await agent.cleanup()

        logger.info(f"[poc] Completed: {result.get('pocs_generated', 0)} PoCs generated")

        # Update scan summary counts from actual DB data before marking complete
        await self._update_scan_summary_counts(scan_id)

        await self.update_scan_phase(scan_id, "completed")
        from app.models.models import ScanStatus
        await self.update_scan_status(scan_id, ScanStatus.COMPLETED)

        return {"poc": result}

    # ── Future conditional routing functions ────────────────────────────────

    def _route_after_executor(self, state: PentestState) -> str:
        """
        Conditional edge: executor → recon (loop) or executor → validator.
        Currently unused — will be wired in Phase 2 conditional edges.
        """
        if state.get("new_paths_found"):
            logger.info("[router] New paths found after execution — looping back to recon")
            return "recon"
        return "validator"

    def _route_after_validator(self, state: PentestState) -> str:
        """
        Conditional edge: validator → strategy (loop) or validator → poc.
        Currently unused — will be wired in Phase 2 conditional edges.
        """
        if state.get("validation_failed"):
            logger.info("[router] Validation failed — looping back to strategy for re-prioritisation")
            return "strategy"
        return "poc"

    # ── Sequential fallback (used when langgraph is not installed) ──────────

    async def _run_sequential_fallback(self, scan_id: str) -> Dict[str, Any]:
        """
        Original sequential pipeline preserved as a fallback.
        Functionally identical to the pre-LangGraph coordinator.
        """
        db = SessionLocal()
        try:
            if str(scan_id).isdigit():
                scan = db.query(Scan).filter(Scan.id == int(scan_id)).first()
            else:
                scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()

            if not scan:
                raise ValueError(f"Scan {scan_id} not found")

            target_url = scan.target_url
            scan_uuid  = scan.scan_id
            policy     = scan.policy or {}
            scan_id    = scan_uuid
        finally:
            db.close()

        await self.update_scan_status(scan_id, ScanStatus.RUNNING)
        await self.update_scan_phase(scan_id, "planning")

        if self.graph_db:
            try:
                await self.graph_db.create_scan_node(scan_id, {
                    "target_url": target_url,
                    "status": "RUNNING",
                    "policy": policy,
                })
            except Exception as g_err:
                logger.warning(f"Attack graph node creation failed: {g_err}")

        strategy = await self.create_attack_strategy(target_url, policy)

        db = SessionLocal()
        try:
            scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
            if scan:
                scan.strategy = {"agent_strategy": strategy}
                db.commit()
        finally:
            db.close()

        # Recon
        await self.update_scan_phase(scan_id, "discovering")
        from app.agents.recon import ReconAgent
        recon_agent = ReconAgent(agent_id=f"recon-{scan_id[:8]}")
        await recon_agent.initialize()
        recon_result = await recon_agent.run(scan_id, target_url=target_url, policy=policy)
        await recon_agent.cleanup()

        # Strategy
        await self.update_scan_phase(scan_id, "strategizing")
        from app.agents.strategy import AttackStrategyAgent
        strategy_agent = AttackStrategyAgent(agent_id=f"strategy-{scan_id[:8]}")
        await strategy_agent.initialize()
        strategy_result = await strategy_agent.run(scan_id)
        await strategy_agent.cleanup()

        # Execution
        await self.update_scan_phase(scan_id, "exploiting")
        from app.agents.executor import ExploitExecutionAgent
        exec_agent = ExploitExecutionAgent(agent_id=f"executor-{scan_id[:8]}")
        await exec_agent.initialize()
        exec_result = await exec_agent.run(scan_id)
        await exec_agent.cleanup()

        # Validation
        await self.update_scan_phase(scan_id, "validating")
        from app.agents.validator import ValidationAgent
        val_agent = ValidationAgent(agent_id=f"validator-{scan_id[:8]}")
        await val_agent.initialize()
        val_result = await val_agent.run(scan_id)
        await val_agent.cleanup()

        # PoC
        await self.update_scan_phase(scan_id, "generating_poc")
        from app.agents.poc_generator import PoCAgent
        poc_agent = PoCAgent(agent_id=f"poc-{scan_id[:8]}")
        await poc_agent.initialize()
        poc_result = await poc_agent.run(scan_id)
        await poc_agent.cleanup()

        # Update scan summary counts from actual DB data
        await self._update_scan_summary_counts(scan_id)

        await self.update_scan_phase(scan_id, "completed")
        from app.models.models import ScanStatus
        await self.update_scan_status(scan_id, ScanStatus.COMPLETED)

        return {
            "status": "success",
            "strategy": strategy,
            "scan_id": scan_id,
            "recon": recon_result,
            "strategy_plan": strategy_result,
            "execution": exec_result,
            "validation": val_result,
            "poc": poc_result,
        }

    # ── LLM Strategy ────────────────────────────────────────────────────────

    async def create_attack_strategy(
        self,
        target_url: str,
        policy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use LLM to create an intelligent, OWASP-mapped attack strategy."""
        logger.info(f"Creating attack strategy for {target_url}")

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

        fallback_strategy = {
            "app_type": "web_application",
            "likely_auth": "unknown",
            "priority_categories": ["A01", "A03", "A05"],
            "recon_tools": ["httpx", "katana"],
            "estimated_endpoints": "unknown",
            "risk_level": "MEDIUM",
            "attack_vectors": [
                {"type": "access_control", "priority": 90, "rationale": "common high-impact class"},
                {"type": "injection",      "priority": 85, "rationale": "broad web exposure"},
            ],
        }

        if self.llm_service is None:
            return fallback_strategy

        try:
            strategy = await asyncio.wait_for(
                self.llm_service.analyze(prompt, response_format="json"),
                timeout=25,
            )
            if isinstance(strategy, str):
                strategy = json.loads(strategy)
        except Exception:
            strategy = fallback_strategy

        logger.info(f"Generated strategy: {strategy.get('priority_categories')}")
        return strategy

    # ── DB Helpers ──────────────────────────────────────────────────────────

    async def update_scan_status(self, scan_id: str, status: Any) -> None:
        """Update scan status in PostgreSQL."""
        db = SessionLocal()
        try:
            if str(scan_id).isdigit():
                scan = db.query(Scan).filter(Scan.id == int(scan_id)).first()
            else:
                scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()

            if scan:
                scan.status = status
                from app.models.models import ScanStatus
                if status == ScanStatus.COMPLETED or status == "COMPLETED":
                    from datetime import datetime
                    scan.completed_at = datetime.utcnow()
                    scan.progress_percentage = 100
                db.commit()
                status_str = status.value if hasattr(status, "value") else str(status)
                logger.info(f"Scan {scan_id} status → {status_str}")
                await self.emit_progress(scan_id, "coordinator", "status_update", {"status": status_str, "progress": 100 if status_str == "COMPLETED" else None})
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not update scan status: {e}")
        finally:
            db.close()

    async def update_scan_phase(self, scan_id: str, phase: str) -> None:
        """Update detailed scan phase in PostgreSQL."""
        db = SessionLocal()
        try:
            if str(scan_id).isdigit():
                scan = db.query(Scan).filter(Scan.id == int(scan_id)).first()
            else:
                scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()

            if scan:
                scan.current_phase = phase
                db.commit()
                logger.info(f"Scan {scan_id} phase → {phase}")
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not update scan phase: {e}")
        finally:
            db.close()

    async def load_knowledge_base_context(self) -> str:
        """Load static OWASP context for LLM strategy prompt."""
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

    async def get_current_findings(self, scan_id: str) -> list:
        """Get validated findings from PostgreSQL (used by LLM re-prioritisation)."""
        db = SessionLocal()
        try:
            findings = db.query(Vulnerability).filter(
                Vulnerability.scan_id == scan_id,
                Vulnerability.status == "VALIDATED",
            ).all()
            return [
                {
                    "type":     f.vulnerability_type,
                    "severity": str(f.severity),
                    "endpoint": f.endpoint.url if f.endpoint else None,
                }
                for f in findings
            ]
        finally:
            db.close()

    async def _update_scan_summary_counts(self, scan_id: str) -> None:
        """
        Update Scan severity counts and summary stats from the
        actual Vulnerability records in PostgreSQL.
        This ensures the dashboard and scan detail page show correct numbers.
        """
        from app.models.models import VulnerabilitySeverity
        db = SessionLocal()
        try:
            scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
            if not scan:
                return

            vulns = db.query(Vulnerability).filter(
                Vulnerability.scan_id == scan.id
            ).all()

            scan.total_findings = len(vulns)
            scan.validated_findings = sum(
                1 for v in vulns if v.status == "VALIDATED"
            )
            scan.false_positives = sum(
                1 for v in vulns if v.is_false_positive
            )

            scan.critical_count = sum(
                1 for v in vulns
                if v.severity == VulnerabilitySeverity.CRITICAL and not v.is_false_positive
            )
            scan.high_count = sum(
                1 for v in vulns
                if v.severity == VulnerabilitySeverity.HIGH and not v.is_false_positive
            )
            scan.medium_count = sum(
                1 for v in vulns
                if v.severity == VulnerabilitySeverity.MEDIUM and not v.is_false_positive
            )
            scan.low_count = sum(
                1 for v in vulns
                if v.severity == VulnerabilitySeverity.LOW and not v.is_false_positive
            )
            scan.info_count = sum(
                1 for v in vulns
                if v.severity == VulnerabilitySeverity.INFO and not v.is_false_positive
            )

            # Also update endpoint/attack counters if not already set
            if scan.endpoints_discovered == 0:
                from app.models.models import Endpoint as EndpointModel
                scan.endpoints_discovered = db.query(EndpointModel).filter(
                    EndpointModel.scan_id == scan.id
                ).count()

            db.commit()
            logger.info(
                f"[coordinator] Updated scan {scan_id} summary: "
                f"{scan.total_findings} findings "
                f"(C:{scan.critical_count} H:{scan.high_count} "
                f"M:{scan.medium_count} L:{scan.low_count} I:{scan.info_count})"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"[coordinator] Failed to update scan summary: {e}")
        finally:
            db.close()
