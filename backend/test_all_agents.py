"""
Comprehensive Agent Health Check
Tests all agents, Neo4j, LLM (Ollama), Redis, and database connections.
"""

import asyncio
import sys
import os

# Add the backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


async def test_neo4j():
    """Test Neo4j connection"""
    print("\n" + "="*60)
    print("1. NEO4J DATABASE")
    print("="*60)
    try:
        from app.core.graph_db import get_graph_db
        graph = await get_graph_db()
        if graph.is_connected:
            print("   ✅ Neo4j: CONNECTED")
            # Test a simple query
            result = await graph.execute("RETURN 1 AS test")
            print(f"   ✅ Neo4j query test: PASSED (result: {result})")
            # Don't close - keep singleton alive for Coordinator test
        else:
            print("   ❌ Neo4j: NOT CONNECTED")
            print("      -> Make sure Neo4j Desktop is running and the database is started")
    except Exception as e:
        print(f"   ❌ Neo4j: FAILED - {e}")


async def test_ollama():
    """Test Ollama LLM connection"""
    print("\n" + "="*60)
    print("2. OLLAMA LLM SERVICE")
    print("="*60)
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    print(f"   URL: {ollama_url}")
    print(f"   Model: {ollama_model}")
    
    try:
        import requests
        # Test if Ollama is running
        resp = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            print(f"   ✅ Ollama: RUNNING ({len(models)} models available)")
            print(f"      Models: {', '.join(model_names[:5])}")
            
            if any(ollama_model in name for name in model_names):
                print(f"   ✅ Model '{ollama_model}': AVAILABLE")
            else:
                print(f"   ⚠️  Model '{ollama_model}': NOT FOUND")
                print(f"      -> Run: ollama pull {ollama_model}")
        else:
            print(f"   ❌ Ollama: HTTP {resp.status_code}")
    except requests.ConnectionError:
        print("   ❌ Ollama: NOT RUNNING")
        print("      -> Start Ollama and run: ollama serve")
    except Exception as e:
        print(f"   ❌ Ollama: FAILED - {e}")


async def test_database():
    """Test PostgreSQL/SQLite database"""
    print("\n" + "="*60)
    print("3. SQL DATABASE (PostgreSQL/SQLite)")
    print("="*60)
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        print("   ✅ Database: CONNECTED")
        db.close()
    except Exception as e:
        print(f"   ❌ Database: FAILED - {e}")


async def test_redis():
    """Test Redis connection"""
    print("\n" + "="*60)
    print("4. REDIS")
    print("="*60)
    try:
        from app.core.redis_client import get_redis
        redis = await get_redis()
        if redis:
            print("   ✅ Redis: CONNECTED")
        else:
            print("   ⚠️  Redis: Not available (agents will work without it)")
    except Exception as e:
        print(f"   ⚠️  Redis: {e} (agents will work without it)")


async def test_agents():
    """Test all agents can be imported and initialized"""
    print("\n" + "="*60)
    print("5. AGENT IMPORTS")
    print("="*60)
    
    agents = [
        ("CoordinatorAgent", "app.agents.coordinator", "CoordinatorAgent"),
        ("ReconAgent", "app.agents.recon", "ReconAgent"),
        ("AttackStrategyAgent", "app.agents.strategy", "AttackStrategyAgent"),
        ("ExploitExecutionAgent", "app.agents.executor", "ExploitExecutionAgent"),
        ("ValidationAgent", "app.agents.validator", "ValidationAgent"),
        ("PoCAgent", "app.agents.poc_generator", "PoCAgent"),
        ("RemediationAgent", "app.agents.remediation_agent", "RemediationAgent"),
    ]
    
    for display_name, module_path, class_name in agents:
        try:
            mod = __import__(module_path, fromlist=[class_name])
            cls = getattr(mod, class_name)
            instance = cls(agent_id=f"test-{display_name.lower()}")
            print(f"   ✅ {display_name}: OK")
        except Exception as e:
            print(f"   ❌ {display_name}: FAILED - {e}")


async def test_coordinator_init():
    """Test that CoordinatorAgent can fully initialize (Neo4j + LLM)"""
    print("\n" + "="*60)
    print("6. COORDINATOR FULL INITIALIZATION")
    print("="*60)
    try:
        from app.agents.coordinator import CoordinatorAgent
        coordinator = CoordinatorAgent(agent_id="test-coordinator")
        await coordinator.initialize()
        
        # Check graph_db
        if coordinator.graph_db and coordinator.graph_db.is_connected:
            print("   ✅ Coordinator -> Neo4j: CONNECTED")
        else:
            print("   ⚠️  Coordinator -> Neo4j: Not connected (will use fallback)")
        
        # Check LLM
        if coordinator.llm_service:
            print("   ✅ Coordinator -> LLM Service: LOADED")
        else:
            print("   ⚠️  Coordinator -> LLM Service: Not loaded")
        
        # Check Redis
        if coordinator.redis_client:
            print("   ✅ Coordinator -> Redis: CONNECTED")
        else:
            print("   ⚠️  Coordinator -> Redis: Not connected (non-critical)")
        
        await coordinator.cleanup()
        print("   ✅ Coordinator cleanup: OK")
        
    except Exception as e:
        print(f"   ❌ Coordinator init: FAILED - {e}")


async def test_orchestrator_import():
    """Test the main orchestrator can import and use agents"""
    print("\n" + "="*60)
    print("7. ORCHESTRATOR (Main Scan Service)")
    print("="*60)
    try:
        from app.services.orchestrator import OrchestratorService
        print("   ✅ OrchestratorService: IMPORTED")
    except Exception as e:
        print(f"   ❌ ScanOrchestrator: FAILED - {e}")


async def main():
    print("╔" + "═"*58 + "╗")
    print("║       RakshAI / NeuroPentWeb Agent Health Check        ║")
    print("╚" + "═"*58 + "╝")
    
    await test_neo4j()
    await test_ollama()
    await test_database()
    await test_redis()
    await test_agents()
    await test_coordinator_init()
    await test_orchestrator_import()
    
    print("\n" + "="*60)
    print("HEALTH CHECK COMPLETE")
    print("="*60)
    print("\nLegend:")
    print("  ✅ = Working")
    print("  ⚠️  = Warning (non-critical)")
    print("  ❌ = Error (needs fixing)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
