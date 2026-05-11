"""
System Diagnostics API
Checks all agents, LLM service, and infrastructure health.
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


def _check_tcp_port(host: str, port: int, timeout: float = 3.0) -> bool:
    """Check if a TCP port is reachable."""
    import socket
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False


def _check_ollama_service(base_url: str, configured_model: str = "") -> Dict[str, Any]:
    """Check Ollama service health and list available models."""
    result: Dict[str, Any] = {
        "status": "offline",
        "url": base_url,
        "models": [],
        "configured_model": configured_model,
        "model_available": False,
        "response_time_ms": None,
        "error": None,
    }

    try:
        start = time.time()
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        elapsed_ms = round((time.time() - start) * 1000)
        result["response_time_ms"] = elapsed_ms

        if resp.status_code == 200:
            result["status"] = "online"
            data = resp.json()
            models = data.get("models", [])
            result["models"] = [
                {
                    "name": m.get("name", ""),
                    "size_gb": round(m.get("size", 0) / 1e9, 2),
                    "modified_at": m.get("modified_at", ""),
                }
                for m in models
            ]
            model_names = [m.get("name", "") for m in models]
            result["model_available"] = any(
                configured_model in name for name in model_names
            ) if configured_model else False
        else:
            result["error"] = f"HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection refused — Ollama server is not running"
    except Exception as e:
        result["error"] = str(e)

    return result


def _check_llm_inference(base_url: str, model: str) -> Dict[str, Any]:
    """Send a simple test prompt to verify LLM inference is working."""
    result: Dict[str, Any] = {
        "status": "failed",
        "model": model,
        "prompt": "Respond with exactly: OK",
        "response": None,
        "response_time_ms": None,
        "error": None,
    }

    if not model:
        result["error"] = "No OLLAMA_MODEL configured"
        return result

    try:
        start = time.time()
        resp = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": "Respond with only the word OK",
                "stream": False,
                "options": {"num_predict": 10, "temperature": 0},
            },
            timeout=120,
        )
        elapsed_ms = round((time.time() - start) * 1000)
        result["response_time_ms"] = elapsed_ms

        if resp.status_code == 200:
            data = resp.json()
            response_text = data.get("response", "").strip()
            result["response"] = response_text[:200]
            result["status"] = "working" if response_text else "empty_response"
        else:
            result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection refused — Ollama not running"
    except requests.exceptions.Timeout:
        result["error"] = "Timeout — LLM took too long to respond (>120s). Model may be loading for the first time."
    except Exception as e:
        result["error"] = str(e)

    return result


def _check_neo4j() -> Dict[str, Any]:
    """Check Neo4j connectivity, trying multiple common passwords and auto-fix."""
    settings = get_settings()
    neo4j_uri = getattr(settings, "NEO4J_URI", "bolt://localhost:7687")
    result: Dict[str, Any] = {
        "status": "offline",
        "uri": neo4j_uri,
        "authenticated_with": None,
        "error": None,
    }

    if not _check_tcp_port("localhost", 7687, timeout=3):
        result["error"] = "Port 7687 not reachable — Start Neo4j from Neo4j Desktop"
        return result

    try:
        from neo4j import GraphDatabase
    except ImportError:
        result["error"] = "neo4j Python driver not installed (pip install neo4j)"
        return result

    neo4j_user = getattr(settings, "NEO4J_USER", "neo4j")
    configured_pass = getattr(settings, "NEO4J_PASSWORD", "")

    # Try passwords in priority order: configured → common defaults
    passwords_to_try = []
    if configured_pass:
        passwords_to_try.append(configured_pass)
    for default_pw in ["RakshAI123", "neo4j", "root", "password", "neuropent_graph_pass", "admin"]:
        if default_pw not in passwords_to_try:
            passwords_to_try.append(default_pw)

    last_error = None
    for pwd in passwords_to_try:
        try:
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, pwd))
            with driver.session() as session:
                record = session.run("RETURN 1 AS ok").single()
                if record and record["ok"] == 1:
                    result["status"] = "online"
                    result["authenticated_with"] = f"{neo4j_user}/{'*' * len(pwd)}"
                    if pwd != configured_pass:
                        result["password_hint"] = (
                            f"Connected with password '{pwd}' — update NEO4J_PASSWORD "
                            f"in .env to match"
                        )
            driver.close()
            if result["status"] == "online":
                return result
        except Exception as e:
            last_error = str(e)
            if "Unauthorized" in last_error or "authentication" in last_error.lower():
                continue
            else:
                result["error"] = last_error
                return result

    # Try without auth (if user disabled auth in neo4j.conf)
    try:
        driver = GraphDatabase.driver(neo4j_uri)
        with driver.session() as session:
            record = session.run("RETURN 1 AS ok").single()
            if record and record["ok"] == 1:
                result["status"] = "online"
                result["authenticated_with"] = "No Authentication (Disabled)"
                result["password_hint"] = "Connected without password (auth_enabled=false)"
        driver.close()
        if result["status"] == "online":
            return result
    except Exception as e:
        last_error = str(e)

    # All passwords failed — give clear fix instructions
    result["error"] = (
        f"Authentication failed for user '{neo4j_user}'. "
        f"Open Neo4j Browser at http://localhost:7474, login with your current password, "
        f"then run: ALTER CURRENT USER SET PASSWORD FROM 'your_current_pw' TO 'neuropent_graph_pass'"
    )
    return result


def _check_redis() -> Dict[str, Any]:
    """Check Redis connectivity."""
    settings = get_settings()
    redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    result: Dict[str, Any] = {
        "status": "offline",
        "url": redis_url,
        "error": None,
    }

    if not _check_tcp_port("localhost", 6379, timeout=3):
        result["error"] = "Port 6379 not reachable"
        return result

    try:
        import redis as redis_lib
        client = redis_lib.from_url(redis_url, socket_timeout=3)
        pong = client.ping()
        if pong:
            result["status"] = "online"
        client.close()
    except Exception as e:
        result["error"] = str(e)

    return result


def _check_database(db: Session) -> Dict[str, Any]:
    """Check database connectivity."""
    result: Dict[str, Any] = {
        "status": "offline",
        "error": None,
    }
    try:
        row = db.execute("SELECT 1").fetchone()
        if row:
            result["status"] = "online"
    except Exception:
        try:
            from sqlalchemy import text
            row = db.execute(text("SELECT 1")).fetchone()
            if row:
                result["status"] = "online"
        except Exception as e:
            result["error"] = str(e)
    return result


def _check_agents() -> List[Dict[str, Any]]:
    """Validate all agent classes can be imported and instantiated."""
    agent_definitions = [
        {
            "name": "CoordinatorAgent",
            "role": "LLM-Driven Planning Engine — Orchestrates the entire penetration testing workflow",
            "module": "app.agents.coordinator",
            "class_name": "CoordinatorAgent",
            "responsibilities": [
                "Dynamic Task Decomposition",
                "Attack Path Prioritization",
                "Agent Scheduling",
                "Risk-Based Planning",
                "Guardrail Enforcement",
                "Adaptive Testing Loop Control",
            ],
        },
        {
            "name": "ReconAgent",
            "role": "Reconnaissance & Discovery — Execute discovery tools, browser automation, technology detection",
            "module": "app.agents.recon",
            "class_name": "ReconAgent",
            "responsibilities": [
                "HTTP probing (httpx)",
                "Web crawling (katana)",
                "Technology detection",
                "Nuclei template scanning",
                "Form discovery (Playwright)",
                "Neo4j endpoint storage",
                "MinIO raw output upload",
            ],
        },
        {
            "name": "AttackStrategyAgent",
            "role": "LLM-Powered Threat Modeling — Analyze endpoints and prioritize attack vectors",
            "module": "app.agents.strategy",
            "class_name": "AttackStrategyAgent",
            "responsibilities": [
                "LLM threat model creation",
                "IDOR/XSS/SQLi/AuthBypass prioritization",
                "OWASP Top 10 attack sequencing",
                "Authentication analysis",
                "Neo4j AttackNode creation",
            ],
        },
        {
            "name": "ExploitExecutionAgent",
            "role": "Exploit Execution — Execute planned attacks via Tool Sandbox",
            "module": "app.agents.executor",
            "class_name": "ExploitExecutionAgent",
            "responsibilities": [
                "SQLi execution (SQLMap)",
                "XSS execution (Dalfox)",
                "IDOR testing (custom)",
                "Auth bypass testing",
                "Session management",
                "Parameter fuzzing",
                "Finding node creation in Neo4j",
            ],
        },
        {
            "name": "ValidationAgent",
            "role": "Zero-Hallucination Guardrails — Replay findings 3x with 85% success threshold",
            "module": "app.agents.validator",
            "class_name": "ValidationAgent",
            "responsibilities": [
                "3x replay validation",
                "85% confidence threshold enforcement",
                "LLM false-positive analysis",
                "Confidence scoring",
                "VALIDATED/FALSE_POSITIVE status assignment",
            ],
        },
        {
            "name": "PoCAgent",
            "role": "Proof-of-Concept Evidence Generation — Screenshots, HTTP traces, cURL commands",
            "module": "app.agents.poc_generator",
            "class_name": "PoCAgent",
            "responsibilities": [
                "Playwright screenshot capture",
                "HTTP request/response traces",
                "cURL command generation",
                "LLM business impact analysis",
                "LLM remediation generation",
                "MinIO evidence upload",
            ],
        },
        {
            "name": "RemediationAgent",
            "role": "LLM-Powered Remediation — Generate instant remediation solutions with code examples",
            "module": "app.agents.remediation_agent",
            "class_name": "RemediationAgent",
            "responsibilities": [
                "Technology detection from evidence",
                "LLM remediation generation",
                "Code example generation",
                "Timeline/effort estimation",
                "Compliance reference mapping (OWASP, CWE)",
            ],
        },
    ]

    results = []
    for agent_def in agent_definitions:
        check: Dict[str, Any] = {
            "name": agent_def["name"],
            "role": agent_def["role"],
            "responsibilities": agent_def["responsibilities"],
            "status": "failed",
            "importable": False,
            "instantiable": False,
            "has_run_method": False,
            "has_initialize_method": False,
            "error": None,
        }

        try:
            import importlib
            mod = importlib.import_module(agent_def["module"])
            cls = getattr(mod, agent_def["class_name"])
            check["importable"] = True

            # Try instantiation
            instance = cls(agent_id=f"diag-{agent_def['name'].lower()}")
            check["instantiable"] = True

            # Check key methods
            check["has_run_method"] = hasattr(instance, "run") and callable(getattr(instance, "run"))
            check["has_initialize_method"] = hasattr(instance, "initialize") and callable(getattr(instance, "initialize"))

            if check["importable"] and check["instantiable"] and check["has_run_method"]:
                check["status"] = "ready"
            else:
                check["status"] = "partial"

        except Exception as e:
            check["error"] = str(e)

        results.append(check)

    return results


def _check_orchestrator_pipeline() -> Dict[str, Any]:
    """Check that the orchestrator pipeline can be instantiated."""
    result: Dict[str, Any] = {
        "status": "failed",
        "importable": False,
        "instantiable": False,
        "has_start_scan": False,
        "pipeline_phases": [],
        "error": None,
    }

    try:
        from app.services.orchestrator import OrchestratorService
        result["importable"] = True

        orch = OrchestratorService()
        result["instantiable"] = True
        result["has_start_scan"] = hasattr(orch, "start_scan") and callable(getattr(orch, "start_scan"))

        result["pipeline_phases"] = [
            "Phase 1: Initialization — Scope/policy validation + LLM strategy",
            "Phase 2: Reconnaissance — HTTP probe, crawl, tech detection, attack graph",
            "Phase 3: Strategy Planning — Endpoint-aware execution plan + OWASP mapping",
            "Phase 4: Exploit Testing — SQLi/XSS/IDOR/AuthBypass execution + advanced checks",
            "Phase 5: Validation — 3x replay with 85% confidence threshold",
            "Phase 6: PoC Generation — Evidence capture (screenshots, HTTP traces, cURL)",
            "Phase 7: Reporting — PDF/Word/Excel/JSON report generation",
        ]

        if result["importable"] and result["instantiable"] and result["has_start_scan"]:
            result["status"] = "ready"

    except Exception as e:
        result["error"] = str(e)

    return result


@router.get("/system-check")
async def run_system_diagnostics(db: Session = Depends(get_db)):
    """
    Run comprehensive system diagnostics.
    
    Checks:
    - All 7 agents (import, instantiation, methods)
    - LLM service (Ollama connectivity + model availability + inference test)
    - Infrastructure (Neo4j, Redis, Database)
    - Orchestrator pipeline readiness
    """
    start_time = time.time()
    settings = get_settings()
    ollama_base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = getattr(settings, "OLLAMA_MODEL", "") or os.getenv("OLLAMA_MODEL", "")
    # Fallback: if settings returns empty, try common model name
    if not ollama_model:
        ollama_model = "qwen2.5:latest"

    # Run all checks
    agents_result = _check_agents()
    ollama_result = _check_ollama_service(ollama_base_url, ollama_model)
    llm_inference_result = _check_llm_inference(ollama_base_url, ollama_model)
    neo4j_result = _check_neo4j()
    redis_result = _check_redis()
    database_result = _check_database(db)
    orchestrator_result = _check_orchestrator_pipeline()

    # Compute overall agent health
    total_agents = len(agents_result)
    ready_agents = sum(1 for a in agents_result if a["status"] == "ready")

    # Overall health score
    checks = {
        "database": database_result["status"] == "online",
        "ollama_service": ollama_result["status"] == "online",
        "ollama_model": ollama_result.get("model_available", False),
        "llm_inference": llm_inference_result["status"] == "working",
        "neo4j": neo4j_result["status"] == "online",
        "redis": redis_result["status"] == "online",
        "agents": ready_agents == total_agents,
        "orchestrator": orchestrator_result["status"] == "ready",
    }
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    health_score = round((passed / total) * 100)

    if health_score >= 80:
        overall_status = "healthy"
    elif health_score >= 50:
        overall_status = "degraded"
    else:
        overall_status = "critical"

    elapsed_ms = round((time.time() - start_time) * 1000)

    return {
        "overall_status": overall_status,
        "health_score": health_score,
        "checks_passed": passed,
        "checks_total": total,
        "check_details": checks,
        "diagnostic_time_ms": elapsed_ms,
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {
            "total": total_agents,
            "ready": ready_agents,
            "details": agents_result,
        },
        "llm": {
            "ollama_service": ollama_result,
            "inference_test": llm_inference_result,
        },
        "infrastructure": {
            "database": database_result,
            "neo4j": neo4j_result,
            "redis": redis_result,
        },
        "orchestrator": orchestrator_result,
    }
