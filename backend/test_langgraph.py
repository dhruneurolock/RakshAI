"""
Test LangGraph Integration — CoordinatorAgent
Runs the LangGraph-powered pentest pipeline against OWASP Juice Shop.
"""
import asyncio
import sys
import os
import uuid
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models import Scan, ScanStatus
from app.agents.coordinator import CoordinatorAgent, PentestState, _LANGGRAPH_AVAILABLE


async def main():
    target_url = "https://juice-shop.herokuapp.com/#/login"
    scan_uuid = f"test-lg-{uuid.uuid4().hex[:8]}"

    print("=" * 70)
    print("  RAKSHAI — LangGraph Integration Test")
    print("=" * 70)
    print(f"  Target    : {target_url}")
    print(f"  Scan ID   : {scan_uuid}")
    print(f"  LangGraph : {'✅ Available' if _LANGGRAPH_AVAILABLE else '❌ Not installed'}")
    print("=" * 70)

    if not _LANGGRAPH_AVAILABLE:
        print("\n❌ FAIL: langgraph is not installed. Cannot test the graph pipeline.")
        return

    # ── 1. Verify graph compiles ──────────────────────────────────────────
    print("\n[1/4] Compiling LangGraph StateGraph...")
    coordinator = CoordinatorAgent(agent_id=f"coordinator-{scan_uuid[:8]}")
    graph = coordinator._build_graph()
    nodes = list(graph.get_graph().nodes.keys())
    print(f"  ✅ Graph compiled. Nodes: {nodes}")

    # ── 2. Verify PentestState schema ─────────────────────────────────────
    print("\n[2/4] Verifying PentestState schema...")
    state_keys = list(PentestState.__annotations__.keys())
    print(f"  ✅ State keys: {state_keys}")

    expected_keys = {"scan_id", "scan_db_id", "target_url", "policy", "strategy",
                     "recon", "strategy_plan", "execution", "validation", "poc",
                     "new_paths_found", "validation_failed"}
    missing = expected_keys - set(state_keys)
    if missing:
        print(f"  ❌ Missing keys: {missing}")
    else:
        print(f"  ✅ All expected keys present")

    # ── 3. Create scan record in DB ───────────────────────────────────────
    print("\n[3/4] Creating scan record in database...")
    db = SessionLocal()
    try:
        new_scan = Scan(
            scan_id=scan_uuid,
            target_url=target_url,
            scan_type="full",
            status=ScanStatus.PENDING,
        )
        db.add(new_scan)
        db.commit()
        scan_db_id = str(new_scan.id)
        print(f"  ✅ Scan record created (DB PK: {scan_db_id}, UUID: {scan_uuid})")
    finally:
        db.close()

    # ── 4. Run the LangGraph pipeline ─────────────────────────────────────
    print("\n[4/4] Running LangGraph coordinator pipeline...")
    print("-" * 70)

    start = time.time()
    try:
        await coordinator.initialize()
        result = await coordinator.run(scan_db_id)
        elapsed = time.time() - start

        print("-" * 70)
        print(f"\n✅ Pipeline completed in {elapsed:.1f}s")
        print(f"  Status       : {result.get('status')}")
        print(f"  Scan ID      : {result.get('scan_id')}")
        print(f"  Strategy     : {type(result.get('strategy')).__name__} "
              f"({len(str(result.get('strategy', '')))} chars)")
        print(f"  Recon        : endpoints_discovered = "
              f"{result.get('recon', {}).get('endpoints_discovered', 'N/A')}")
        print(f"  Strategy Plan: attacks_planned = "
              f"{result.get('strategy_plan', {}).get('attacks_planned', 'N/A')}")
        print(f"  Execution    : findings_discovered = "
              f"{result.get('execution', {}).get('findings_discovered', 'N/A')}")
        print(f"  Validation   : validated = "
              f"{result.get('validation', {}).get('validated', 'N/A')}")
        print(f"  PoC          : pocs_generated = "
              f"{result.get('poc', {}).get('pocs_generated', 'N/A')}")

    except Exception as e:
        elapsed = time.time() - start
        print(f"\n⚠️ Pipeline raised an exception after {elapsed:.1f}s:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await coordinator.cleanup()
        except Exception:
            pass

    # ── 5. Show final DB state ────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  Post-Scan Database State")
    print("=" * 70)
    db = SessionLocal()
    try:
        scan = db.query(Scan).filter(Scan.scan_id == scan_uuid).first()
        if scan:
            print(f"  Status        : {scan.status}")
            print(f"  Current Phase : {scan.current_phase}")
            print(f"  Strategy      : {'Yes' if scan.strategy else 'No'}")
            vulns = scan.vulnerabilities if scan.vulnerabilities else []
            print(f"  Vulnerabilities: {len(vulns)}")
            for v in vulns[:5]:
                sev = getattr(v.severity, "name", str(v.severity))
                print(f"    [{sev}] {v.title}")
    finally:
        db.close()

    print("=" * 70)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
