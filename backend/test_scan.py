"""
Agentic Pipeline Test Scan
Runs a full scan against Google Gruyere to verify the agentic pipeline works end-to-end.
"""

import asyncio
import sys
import os
import uuid
import logging
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Configure logging to see all agent activity
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-35s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S"
)
# Suppress noisy libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("postgresql").setLevel(logging.WARNING)

logger = logging.getLogger("SCAN_TEST")

TARGET_URL = "https://www.demoblaze.com/"


async def run_test_scan():
    """Run a full agentic pipeline scan"""
    
    scan_id = str(uuid.uuid4())
    
    print("+" + "-"*62 + "+")
    print("|     RakshAI Agentic Pipeline — Live Scan Test              |")
    print("+" + "-"*62 + "+")
    print(f"\n[Target] Target:  {TARGET_URL}")
    print(f"[Key] Scan ID: {scan_id}")
    print(f"{'-'*64}")
    
    # -- Step 1: Create scan record in database --
    print("\n[Step] STEP 1: Creating scan record in database...")
    try:
        from app.core.database import SessionLocal
        from app.models.models import Scan, ScanStatus
        
        db = SessionLocal()
        scan = Scan(
            scan_id=scan_id,
            target_url=TARGET_URL,
            scan_type="full",
            status=ScanStatus.PENDING,
        )
        db.add(scan)
        db.commit()
        db_scan_id = scan.id  # Get the auto-generated DB primary key
        db.close()
        print(f"   [OK] Scan record created (DB ID: {db_scan_id})")
    except Exception as e:
        print(f"   ❌ Failed to create scan: {e}")
        return
    
    # -- Step 2: Test PostgreSQL attack graph creation --
    print("\n[Graph]️  STEP 2: Creating attack graph in PostgreSQL...")
    try:
        from app.core.graph_db import get_graph_db
        graph = await get_graph_db()
        
        if graph.is_connected:
            await graph.create_scan_node(scan_id, {
                "target_url": TARGET_URL,
                "status": "INITIALIZING",
                "scan_type": "full"
            })
            print(f"   [OK] Scan node created in PostgreSQL")
            
            # Verify it was created
            stats = await graph.get_scan_statistics(scan_id)
            print(f"   [OK] Graph stats: {stats}")
        else:
            print(f"   ⚠️  PostgreSQL not connected, skipping graph")
    except Exception as e:
        print(f"   ❌ PostgreSQL error: {e}")
    
    # -- Step 3: Test LLM strategy generation --
    print("\n[LLM] STEP 3: Asking LLM to generate attack strategy...")
    try:
        import requests
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        
        prompt = f"""Create an initial web pentest strategy in JSON for target: {TARGET_URL}
Return JSON with:
{{
  "scope_validation": ["..."],
  "initial_vectors": ["SQLI", "XSS", "IDOR", "AUTH_BYPASS"],
  "priority": ["high-level ordered priorities"],
  "business_impact_hypothesis": "...",
  "recon_tools": ["httpx", "katana"],
  "exploit_tools": ["sqlmap", "dalfox", "custom-idor", "auth-bypass"]
}}"""
        
        start_time = time.time()
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": ollama_model, 
                "prompt": prompt, 
                "stream": False,
                "format": "json"
            },
            timeout=120
        )
        elapsed = time.time() - start_time
        
        if resp.status_code == 200:
            llm_response = resp.json().get("response", "")
            print(f"   [OK] LLM responded in {elapsed:.1f}s")
            print(f"   [Memo] Strategy preview: {llm_response[:200]}...")
        else:
            print(f"   ❌ LLM returned HTTP {resp.status_code}")
    except Exception as e:
        print(f"   ❌ LLM error: {e}")
    
    # -- Step 4: Test CoordinatorAgent initialization --
    print("\n[Agent] STEP 4: Initializing CoordinatorAgent...")
    try:
        from app.agents.coordinator import CoordinatorAgent
        
        coordinator = CoordinatorAgent(agent_id=f"coordinator-{scan_id[:8]}")
        await coordinator.initialize()
        
        postgresql_ok = coordinator.graph_db and coordinator.graph_db.is_connected
        llm_ok = coordinator.llm_service is not None
        redis_ok = coordinator.redis_client is not None
        
        print(f"   {'[OK]' if postgresql_ok else '❌'} PostgreSQL: {'Connected' if postgresql_ok else 'NOT Connected'}")
        print(f"   {'[OK]' if llm_ok else '❌'} LLM:   {'Loaded' if llm_ok else 'NOT Loaded'}")
        print(f"   {'[OK]' if redis_ok else '⚠️ '} Redis: {'Connected' if redis_ok else 'Not available'}")
        
        await coordinator.cleanup()
    except Exception as e:
        print(f"   ❌ Coordinator error: {e}")
    
    # -- Step 5: Run the Orchestrator pipeline --
    print("\n[Launch] STEP 5: Launching full OrchestratorService pipeline...")
    print(f"   (This will run the actual scan against {TARGET_URL})")
    print(f"   [Wait] Please wait — this may take 2-5 minutes...\n")
    
    try:
        from app.services.orchestrator import OrchestratorService
        
        orchestrator = OrchestratorService()
        result = await orchestrator.start_scan(
            scan_id=scan_id,
            target_url=TARGET_URL,
            scan_type="full",
            user_id="test-user",
            policy=None
        )
        
        print(f"\n   [Result] Orchestrator result: {result}")
        
        if result.get("success"):
            print(f"   [OK] Scan launched successfully!")
            print(f"   [Info]️  The scan is running in a background thread.")
            print(f"   [Wait] Waiting 60 seconds for initial results...\n")
            
            # Wait and check for results
            await asyncio.sleep(60)
            
            # Check database for findings
            db = SessionLocal()
            try:
                from app.models.models import Vulnerability
                scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
                if scan:
                    print(f"   [Step] Scan Status: {scan.status}")
                    vulns = db.query(Vulnerability).filter(Vulnerability.scan_id == scan.id).all()
                    print(f"   [Search] Vulnerabilities found: {len(vulns)}")
                    for v in vulns[:10]:
                        print(f"      • [{v.severity.value if hasattr(v.severity, 'value') else v.severity}] {v.title}")
            finally:
                db.close()
            
            # Check PostgreSQL for graph data
            graph = await get_graph_db()
            if graph.is_connected:
                stats = await graph.get_scan_statistics(scan_id)
                print(f"   [Graph]️  PostgreSQL Graph: {stats}")
        else:
            print(f"   ❌ Scan failed: {result.get('error')} - {result.get('message')}")
        
    except Exception as e:
        print(f"   ❌ Orchestrator error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'-'*64}")
    print("SCAN TEST COMPLETE")
    print(f"{'-'*64}\n")


if __name__ == "__main__":
    asyncio.run(run_test_scan())
