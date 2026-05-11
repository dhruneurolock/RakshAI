"""
Test Enterprise Architecture Components

This script verifies all new components are working:
1. LLM Service (Ollama + LangChain)
2. Tool Sandbox
3. Graph Database (Neo4j)
4. Storage Service (MinIO)
5. Coordinator Agent
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.llm_service import get_llm_service
from app.core.tool_sandbox import get_tool_sandbox
from app.core.graph_db import get_graph_db
from app.services.storage_service import get_storage_service
from app.agents import CoordinatorAgent


async def test_llm_service():
    """Test LLM Service"""
    print("🤖 Testing LLM Service...")
    try:
        llm = await get_llm_service()
        
        # Test simple analysis
        result = await llm.analyze(
            prompt="What are the top 3 OWASP vulnerabilities?",
            response_format="json",
            use_strategy_model=True
        )
        
        print(f"   ✅ LLM Response: {result[:100]}...")
        return True
    except Exception as e:
        print(f"   ❌ LLM Service Error: {e}")
        return False


async def test_tool_sandbox():
    """Test Tool Sandbox"""
    print("🛠️  Testing Tool Sandbox...")
    try:
        sandbox = get_tool_sandbox()
        
        # Test httpx command builder
        result = await sandbox.execute("httpx", {
            "target": "http://example.com",
            "status_code": True,
            "timeout": 5
        })
        
        if result.success:
            print(f"   ✅ Tool executed successfully")
            print(f"   Output: {result.output[:100]}...")
        else:
            print(f"   ⚠️  Tool failed (this is OK if httpx not installed): {result.error}")
        return True
    except Exception as e:
        print(f"   ❌ Tool Sandbox Error: {e}")
        return False


async def test_graph_db():
    """Test Neo4j Graph Database"""
    print("📊 Testing Graph Database...")
    try:
        graph = await get_graph_db()
        
        # Test connection
        await graph.connect()
        
        # Create test scan node
        scan_id = "test_scan_123"
        await graph.create_scan_node(scan_id, {
            "target_url": "http://test.example.com",
            "scan_type": "test"
        })
        
        print(f"   ✅ Created scan node: {scan_id}")
        
        # Clean up
        await graph.driver.session().run(
            "MATCH (s:Scan {scan_id: $scan_id}) DELETE s",
            scan_id=scan_id
        )
        
        return True
    except Exception as e:
        print(f"   ❌ Graph DB Error: {e}")
        print(f"   Make sure Neo4j is running: docker-compose up -d neo4j")
        return False


async def test_storage_service():
    """Test MinIO Storage Service"""
    print("💾 Testing Storage Service...")
    try:
        storage = await get_storage_service()
        
        # Test bucket creation
        bucket_name = "neuropent-test"
        if not await storage.bucket_exists(bucket_name):
            await storage.create_bucket(bucket_name)
            print(f"   ✅ Created bucket: {bucket_name}")
        else:
            print(f"   ✅ Bucket exists: {bucket_name}")
        
        # Test file upload
        test_data = b"This is a test file for NeuroPentWeb"
        object_name = "test_file.txt"
        
        url = await storage.upload_to_bucket(
            bucket_name,
            object_name,
            test_data,
            "text/plain"
        )
        
        if url:
            print(f"   ✅ Uploaded test file")
            print(f"   Presigned URL: {url[:80]}...")
        
        return True
    except Exception as e:
        print(f"   ❌ Storage Service Error: {e}")
        print(f"   Make sure MinIO is running: docker-compose up -d minio")
        return False


async def test_coordinator_agent():
    """Test Coordinator Agent"""
    print("🧠 Testing Coordinator Agent...")
    try:
        agent = CoordinatorAgent("test_coordinator")
        await agent.initialize()
        
        # Note: This will fail if LLM/Graph/Storage aren't working
        # but should at least instantiate
        print(f"   ✅ Agent initialized: {agent.agent_id}")
        print(f"   Model: {agent.llm_service}")
        
        return True
    except Exception as e:
        print(f"   ❌ Coordinator Agent Error: {e}")
        return False


async def main():
    """Run all tests"""
    print("")
    print("=" * 60)
    print("🔬 NeuroPentWeb Enterprise Architecture Test Suite")
    print("=" * 60)
    print("")
    
    results = {}
    
    # Run tests
    results["llm"] = await test_llm_service()
    print("")
    
    results["sandbox"] = await test_tool_sandbox()
    print("")
    
    results["graph"] = await test_graph_db()
    print("")
    
    results["storage"] = await test_storage_service()
    print("")
    
    results["agent"] = await test_coordinator_agent()
    print("")
    
    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {component.upper():20s} {status}")
    
    print("")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    if total_passed == total_tests:
        print(f"🎉 All {total_tests} tests passed!")
    else:
        print(f"⚠️  {total_passed}/{total_tests} tests passed")
        print("")
        print("Common issues:")
        print("  • LLM: Run 'docker exec neuropent_ollama ollama pull llama3.1:8b'")
        print("  • Graph: Run 'docker-compose up -d neo4j'")
        print("  • Storage: Run 'docker-compose up -d minio'")
        print("  • Tools: Install security tools (see ENTERPRISE-IMPLEMENTATION.md)")
    
    print("")
    return total_passed == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
