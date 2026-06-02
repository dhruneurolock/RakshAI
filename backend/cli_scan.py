import asyncio
import uuid
import json
import os
import sys

# Ensure the app module is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.orchestrator import OrchestratorService
from app.core.database import SessionLocal
from app.models.models import Scan, ScanStatus
from app.core.redis_client import get_redis

async def monitor_progress(scan_id: str):
    redis = await get_redis()
    pubsub = redis.pubsub()
    channel = f"scan:{scan_id}:progress"
    await pubsub.subscribe(channel)
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    agent = data.get("agent", "SYSTEM")
                    phase = data.get("phase", "info")
                    
                    # Handle different payload structures
                    if "details" in data and isinstance(data["details"], dict):
                        msg = data["details"].get("message", str(data["details"]))
                    elif "message" in data:
                        msg = data["message"]
                    else:
                        msg = str(data)
                        
                    print(f"🚀 [Agent: {agent.upper():<12}] [{phase.upper():<10}] ➔ {msg}")
                except Exception as e:
                    print(f"Raw Message: {message['data']}")
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(channel)

async def main():
    target = "https://juice-shop.herokuapp.com/"
    scan_id = f"cli-scan-{uuid.uuid4().hex[:8]}"
    print("="*70)
    print(f"🛡️  RAKSHAI CLI - LIVE AGENTIC SCAN")
    print(f"🎯 Target:   {target}")
    print(f"🆔 Scan ID:  {scan_id}")
    print("="*70)
    
    db = SessionLocal()
    new_scan = Scan(
        scan_id=scan_id,
        target_url=target,
        scan_type="full",
        status=ScanStatus.PENDING
    )
    db.add(new_scan)
    db.commit()
    db.close()
    
    # Start Redis monitor in the background
    monitor_task = asyncio.create_task(monitor_progress(scan_id))
    
    # Allow a moment for the subscriber to connect
    await asyncio.sleep(1)
    
    print("\n⏳ Launching Orchestrator and Agents...\n" + "-"*70)
    orchestrator = OrchestratorService()
    
    # Run pipeline in a separate thread so asyncio loop can process Redis messages
    await asyncio.to_thread(orchestrator._run_phase_pipeline_sync, scan_id)
    
    # Give a tiny delay for final messages to arrive
    await asyncio.sleep(2)
    monitor_task.cancel()
    
    print("-"*70)
    print("✅ Pipeline execution finished.")
    
    # Fetch results
    db = SessionLocal()
    scan = db.query(Scan).filter(Scan.scan_id == scan_id).first()
    vulns = scan.vulnerabilities if scan else []
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Status: {scan.status if scan else 'UNKNOWN'}")
    print(f"   Total Vulnerabilities Found: {len(vulns)}")
    
    if vulns:
        print("\n🔍 TOP FINDINGS:")
        for v in vulns[:5]:
            severity = getattr(v.severity, "name", str(v.severity))
            print(f"   - [{severity}] {v.title}")
    
    db.close()
    print("="*70)

if __name__ == "__main__":
    # Ensure Windows works with ProactorEventLoop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
