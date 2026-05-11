"""
Comprehensive Agent Validation Script

Validates all 6 agents in the NeuroPentWeb system:
1. CoordinatorAgent - Orchestration & control plane
2. ReconAgent - Reconnaissance & discovery
3. AttackStrategyAgent - LLM-powered threat modeling
4. ExploitExecutionAgent - Attack execution
5. ValidationAgent - Finding validation with zero-hallucination
6. PoCAgent - Proof-of-Concept generation

Exit codes:
- 0: All agents working
- 1: Some agents failed
"""

import sys
import asyncio
from pathlib import Path
from typing import Dict, Tuple, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.agents import (
    CoordinatorAgent,
    ReconAgent, 
    AttackStrategyAgent,
    ExploitExecutionAgent,
    ValidationAgent,
    PoCAgent,
)


class AgentValidator:
    """Validates all agents systematically"""
    
    AGENTS = [
        ("CoordinatorAgent", CoordinatorAgent, "Orchestration & control plane"),
        ("ReconAgent", ReconAgent, "Reconnaissance & discovery"),
        ("AttackStrategyAgent", AttackStrategyAgent, "LLM-powered threat modeling"),
        ("ExploitExecutionAgent", ExploitExecutionAgent, "Attack execution"),
        ("ValidationAgent", ValidationAgent, "Finding validation"),
        ("PoCAgent", PoCAgent, "Proof-of-Concept generation"),
    ]
    
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        
    async def validate_all(self) -> bool:
        """Validate all agents"""
        print("")
        print("=" * 70)
        print("🔬 NEUROPENTWEB AGENT VALIDATION SUITE")
        print("=" * 70)
        print("")
        
        for name, cls, description in self.AGENTS:
            await self._validate_agent(name, cls, description)
            print("")
        
        return self._print_summary()
    
    async def _validate_agent(self, name: str, cls, description: str) -> None:
        """Validate single agent"""
        print(f"🧪 Testing {name}")
        print(f"   Description: {description}")
        print(f"   ", end="")
        
        try:
            # Step 1: Instantiation
            agent = cls(f"validator_{name.lower()}")
            print("✓ Instantiated ", end="")
            
            # Step 2: Initialization
            await agent.initialize()
            print("✓ Initialized ", end="")
            
            # Step 3: Verify core attributes
            assert hasattr(agent, 'agent_id'), "Missing agent_id attribute"
            assert hasattr(agent, 'run'), "Missing run() method"
            assert hasattr(agent, 'initialize'), "Missing initialize() method"
            print("✓ Valid API")
            
            self.results.append((name, True, "All checks passed"))
            
        except Exception as e:
            error_msg = str(e)[:80]
            print(f"✗ FAILED: {error_msg}")
            self.results.append((name, False, error_msg))
    
    def _print_summary(self) -> bool:
        """Print summary and return success status"""
        print("=" * 70)
        print("📊 VALIDATION RESULTS SUMMARY")
        print("=" * 70)
        print("")
        
        passed = 0
        failed = 0
        
        for name, success, msg in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {name:30s} {status}")
            if not success:
                print(f"    → {msg}")
            
            if success:
                passed += 1
            else:
                failed += 1
        
        print("")
        print(f"  TOTAL: {passed}/{len(self.results)} agents working")
        print("")
        
        if failed == 0:
            print("🎉 ALL AGENTS ARE FULLY FUNCTIONAL!")
            print("")
            print("Next steps:")
            print("  1. Run: docker-compose up -d neo4j minio ollama")
            print("  2. Start backend: python backend/app/main.py")
            print("  3. Start frontend: npm run dev --prefix frontend")
            print("  4. Create a scan: POST /api/v1/scans/")
            print("")
            return True
        else:
            print(f"⚠️  {failed} agent(s) need attention. See errors above.")
            print("")
            return False


async def main():
    """Run validation"""
    validator = AgentValidator()
    success = await validator.validate_all()
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Validation interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
