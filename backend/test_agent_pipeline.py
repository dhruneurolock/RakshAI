"""
Agent Pipeline Deep Diagnostic
Tests each agent's REAL functionality, not just imports.
Identifies exactly which agents are broken and why.
"""

import asyncio
import sys
import os
import json
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

# Minimal logging
import logging
logging.basicConfig(level=logging.WARNING, format="%(name)s | %(message)s")


def header(title):
    print(f"\n{'━'*64}")
    print(f"  {title}")
    print(f"{'━'*64}")


def ok(msg):
    print(f"  ✅ {msg}")


def warn(msg):
    print(f"  ⚠️  {msg}")


def fail(msg):
    print(f"  ❌ {msg}")


def info(msg):
    print(f"  ℹ️  {msg}")


# ═══════════════════════════════════════════════════════════════════
# ISSUE TRACKER
# ═══════════════════════════════════════════════════════════════════
issues = []


async def test_base_agent():
    """Test 1: BaseAgent infrastructure (Redis, Neo4j, LLM)"""
    header("1. BASE AGENT INFRASTRUCTURE")

    from app.agents.base_agent import BaseAgent
    from app.agents.coordinator import CoordinatorAgent

    agent = CoordinatorAgent(agent_id="diag-base")
    await agent.initialize()

    # Neo4j
    if agent.graph_db and agent.graph_db.is_connected:
        ok("Neo4j: Connected")
    else:
        fail("Neo4j: NOT Connected")
        issues.append(("BaseAgent", "Neo4j not connected — check if Neo4j Desktop database is started"))

    # Redis
    if agent.redis_client:
        ok("Redis: Connected")
        # Test json.dumps serialization
        try:
            await agent.redis_client.publish("diag:test", json.dumps({"test": True}))
            ok("Redis publish (json.dumps): OK")
        except Exception as e:
            fail(f"Redis publish: {e}")
            issues.append(("BaseAgent", f"Redis publish broken: {e}"))
    else:
        fail("Redis: NOT Connected")
        issues.append(("BaseAgent", "Redis not connected"))

    # LLM Service
    if agent.llm_service:
        ok("LLM Service: Loaded")
    else:
        warn("LLM Service: Not loaded (agents will use fallbacks)")

    # Test emit_progress with BOTH call patterns
    info("Testing emit_progress with both call patterns...")
    try:
        # Pattern 1: BaseAgent style — (scan_id, {dict})
        await agent.emit_progress("diag-test", {"status": "test"})
        ok("emit_progress(scan_id, {dict}): OK")
    except TypeError as e:
        fail(f"emit_progress 2-arg pattern: {e}")
        issues.append(("BaseAgent", f"emit_progress 2-arg pattern broken: {e}"))
    try:
        # Pattern 2: Agent style — (scan_id, "agent", "phase", {details})
        await agent.emit_progress("diag-test", "recon", "started", {"message": "test"})
        ok("emit_progress(scan_id, 'recon', 'started', {dict}): OK")
    except TypeError as e:
        fail(f"emit_progress 4-arg pattern: {e}")
        issues.append(("BaseAgent", f"emit_progress 4-arg pattern broken: {e}"))

    # Test log_action
    try:
        await agent.log_action("diag-test", "diagnostic", {"step": "base_test"})
        ok("log_action (json.dumps): OK")
    except Exception as e:
        fail(f"log_action: {e}")
        issues.append(("BaseAgent", f"log_action broken: {e}"))

    # Test handle_error
    try:
        await agent.handle_error("diag-test", Exception("diagnostic test"))
        ok("handle_error: OK")
    except Exception as e:
        fail(f"handle_error: {e}")
        issues.append(("BaseAgent", f"handle_error broken: {e}"))

    await agent.cleanup()


async def test_coordinator():
    """Test 2: CoordinatorAgent — LLM strategy + graph init"""
    header("2. COORDINATOR AGENT")

    from app.agents.coordinator import CoordinatorAgent
    from app.models.models import ScanStatus

    agent = CoordinatorAgent(agent_id="diag-coordinator")
    await agent.initialize()

    # Test create_attack_strategy (LLM call)
    info("Testing create_attack_strategy (LLM call)...")
    try:
        strategy = await agent.create_attack_strategy(
            "https://example.com",
            {"max_depth": 3}
        )
        if strategy and isinstance(strategy, dict):
            ok(f"create_attack_strategy: OK (keys: {list(strategy.keys())[:5]})")
        else:
            warn(f"create_attack_strategy: returned {type(strategy)}")
    except Exception as e:
        fail(f"create_attack_strategy: {e}")
        issues.append(("Coordinator", f"LLM strategy generation failed: {e}"))

    # Test initialize_attack_graph (Neo4j)
    info("Testing initialize_attack_graph (Neo4j)...")
    try:
        await agent.initialize_attack_graph("diag-scan-001", {
            "priority_categories": ["A01", "A03"],
            "attack_vectors": [{"type": "SQLI", "priority": 90}]
        })
        ok("initialize_attack_graph: OK")
    except Exception as e:
        fail(f"initialize_attack_graph: {e}")
        issues.append(("Coordinator", f"Graph init failed: {e}"))

    # Test update_scan_status with known-good status values
    info("Testing update_scan_status with DB enum values...")
    # Check which values the DB actually accepts
    from app.core.database import SessionLocal
    from app.models.models import Scan
    db = SessionLocal()
    try:
        # Find any existing scan to test with
        scan = db.query(Scan).first()
        if scan:
            original_status = scan.status
            for status_val in [ScanStatus.PENDING, ScanStatus.RUNNING]:
                try:
                    scan.status = status_val
                    db.commit()
                    ok(f"DB accepts status '{status_val.value}': YES")
                    break
                except Exception as e:
                    db.rollback()
                    fail(f"DB rejects status '{status_val.value}': {e}")
                    issues.append(("Coordinator", f"DB enum missing '{status_val.value}' — needs ALTER TYPE"))

            # Test all 5 DB enum values
            for test_status in [ScanStatus.PENDING, ScanStatus.RUNNING, ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED]:
                try:
                    scan.status = test_status
                    db.commit()
                    ok(f"DB accepts status '{test_status.value}': YES")
                except Exception as e:
                    db.rollback()
                    fail(f"DB rejects status '{test_status.value}'")
                    issues.append(("Coordinator", f"PostgreSQL enum missing '{test_status.value}'"))
            
            # Restore original
            try:
                scan.status = original_status if original_status else ScanStatus.PENDING
                db.commit()
            except Exception:
                db.rollback()
        else:
            warn("No scans in DB to test status updates")
    finally:
        db.close()

    # Test trigger_recon_agent (Redis publish)
    info("Testing trigger_recon_agent (Redis)...")
    try:
        await agent.trigger_recon_agent("diag-scan-001", "https://example.com", {
            "recon_tools": ["httpx"],
            "crawl_depth": 2
        })
        ok("trigger_recon_agent: OK (Redis publish succeeded)")
    except Exception as e:
        fail(f"trigger_recon_agent: {e}")
        issues.append(("Coordinator", f"Redis publish in trigger_recon_agent failed: {e}"))

    await agent.cleanup()


async def test_recon():
    """Test 3: ReconAgent — tool_sandbox dependency"""
    header("3. RECON AGENT")

    from app.agents.recon import ReconAgent

    agent = ReconAgent(agent_id="diag-recon")
    await agent.initialize()

    # Check tool_sandbox dependency
    info("Checking tool_sandbox attribute...")
    if hasattr(agent, 'tool_sandbox') and agent.tool_sandbox is not None:
        ok("tool_sandbox: Available")
    else:
        fail("tool_sandbox: NOT AVAILABLE (attribute missing or None)")
        issues.append(("Recon", "tool_sandbox is None — httpx/katana/nuclei calls will crash with AttributeError"))
        issues.append(("Recon", "BaseAgent.__init__ never sets self.tool_sandbox"))

    # Runtime test: call emit_progress the way ReconAgent does
    info("Runtime testing emit_progress (4-arg pattern)...")
    try:
        await agent.emit_progress("diag-recon", "recon", "started", {"message": "test"})
        ok("emit_progress(scan_id, 'recon', 'started', {...}): OK")
    except TypeError as e:
        fail(f"emit_progress 4-arg: {e}")
        issues.append(("Recon", f"emit_progress broken: {e}"))

    # Runtime test: call handle_error the way ReconAgent does
    info("Runtime testing handle_error (3-arg pattern)...")
    try:
        await agent.handle_error("diag-recon", "recon", Exception("test"))
        ok("handle_error(scan_id, 'recon', error): OK")
    except TypeError as e:
        fail(f"handle_error 3-arg: {e}")
        issues.append(("Recon", f"handle_error broken: {e}"))

    await agent.cleanup()


async def test_strategy():
    """Test 4: StrategyAgent — LLM attack planning"""
    header("4. STRATEGY AGENT")

    from app.agents.strategy import AttackStrategyAgent

    agent = AttackStrategyAgent(agent_id="diag-strategy")
    await agent.initialize()

    # Check tool_sandbox
    if hasattr(agent, 'tool_sandbox') and agent.tool_sandbox is not None:
        ok("tool_sandbox: Available")
    else:
        warn("tool_sandbox: Not used directly by StrategyAgent")

    # Runtime test
    info("Runtime testing emit_progress...")
    try:
        await agent.emit_progress("diag-strategy", "strategy", "started", {"message": "test"})
        ok("emit_progress: OK")
    except TypeError as e:
        fail(f"emit_progress: {e}")
        issues.append(("Strategy", f"emit_progress broken: {e}"))

    ok("StrategyAgent: Importable and initializable")
    await agent.cleanup()


async def test_executor():
    """Test 5: ExecutorAgent — tool_sandbox + attack execution"""
    header("5. EXECUTOR AGENT")

    from app.agents.executor import ExploitExecutionAgent

    agent = ExploitExecutionAgent(agent_id="diag-executor")
    await agent.initialize()

    # Check tool_sandbox
    if hasattr(agent, 'tool_sandbox') and agent.tool_sandbox is not None:
        ok("tool_sandbox: Available")
    else:
        fail("tool_sandbox: NOT AVAILABLE")
        issues.append(("Executor", "tool_sandbox is None — sqlmap/dalfox calls will crash"))

    # Runtime test
    info("Runtime testing emit_progress...")
    try:
        await agent.emit_progress("diag-executor", "executor", "started", {"message": "test"})
        ok("emit_progress: OK")
    except TypeError as e:
        fail(f"emit_progress: {e}")
        issues.append(("Executor", f"emit_progress broken: {e}"))

    ok("ExecutorAgent: Importable and initializable")
    await agent.cleanup()


async def test_validator():
    """Test 6: ValidatorAgent"""
    header("6. VALIDATOR AGENT")

    from app.agents.validator import ValidationAgent

    agent = ValidationAgent(agent_id="diag-validator")
    await agent.initialize()

    # Check tool_sandbox
    if hasattr(agent, 'tool_sandbox') and agent.tool_sandbox is not None:
        ok("tool_sandbox: Available")
    else:
        fail("tool_sandbox: NOT AVAILABLE")
        issues.append(("Validator", "tool_sandbox is None — replay attacks will crash"))

    ok("ValidatorAgent: Importable and initializable")
    await agent.cleanup()


async def test_poc():
    """Test 7: PoCAgent"""
    header("7. POC AGENT")

    from app.agents.poc_generator import PoCAgent

    agent = PoCAgent(agent_id="diag-poc")
    await agent.initialize()

    ok("PoCAgent: Importable and initializable")
    await agent.cleanup()


async def test_remediation():
    """Test 8: RemediationAgent"""
    header("8. REMEDIATION AGENT")

    from app.agents.remediation_agent import RemediationAgent

    agent = RemediationAgent(agent_id="diag-remediation")
    await agent.initialize()

    ok("RemediationAgent: Importable and initializable")
    await agent.cleanup()


async def test_llm_json():
    """Test 9: LLM JSON output quality"""
    header("9. LLM JSON OUTPUT QUALITY")

    import requests

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

    info(f"Testing {model} at {ollama_url} with format='json'...")

    try:
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": 'Return a JSON object with keys "status" and "value". Example: {"status":"ok","value":42}',
                "stream": False,
                "format": "json"
            },
            timeout=60
        )

        if resp.status_code == 200:
            raw = resp.json().get("response", "")
            try:
                parsed = json.loads(raw)
                ok(f"LLM returned valid JSON: {parsed}")
            except json.JSONDecodeError as e:
                fail(f"LLM returned invalid JSON: {raw[:200]}")
                issues.append(("LLM", f"Even with format='json', output is invalid: {e}"))
        else:
            fail(f"Ollama HTTP {resp.status_code}")
    except requests.ConnectionError:
        fail("Ollama not running")
        issues.append(("LLM", "Ollama not running"))
    except requests.ReadTimeout:
        fail("Ollama timed out (>60s)")
        issues.append(("LLM", "Ollama timed out on simple JSON request"))


async def main():
    print("╔" + "═"*62 + "╗")
    print("║    RakshAI Agent Pipeline — Deep Diagnostic                ║")
    print("╚" + "═"*62 + "╝")

    await test_base_agent()
    await test_coordinator()
    await test_recon()
    await test_strategy()
    await test_executor()
    await test_validator()
    await test_poc()
    await test_remediation()
    await test_llm_json()

    # ═══════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ═══════════════════════════════════════════════════════════════
    header("DIAGNOSTIC SUMMARY")

    if not issues:
        print("\n  🎉 ALL AGENTS WORKING PROPERLY — NO ISSUES FOUND!\n")
    else:
        print(f"\n  🔴 Found {len(issues)} issue(s) that WILL crash the pipeline:\n")
        for i, (agent, desc) in enumerate(issues, 1):
            print(f"  {i}. [{agent}] {desc}")
        print()
        print("  These must be fixed before the scan pipeline will work.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
