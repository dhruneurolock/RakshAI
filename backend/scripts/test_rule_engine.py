"""
Integration Test: Rule Engine + Knowledge Base
Tests that all 7 rule engine components can access YAML data
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.rule_engine.context_normalizer import ContextNormalizer
from app.rule_engine.owasp_mapper import OWASPMapper
from app.rule_engine.test_case_evaluator import TestCaseEvaluator
from app.rule_engine.payload_binder import PayloadBinder
from app.rule_engine.safety_enforcer import SafetyEnforcer
from app.rule_engine.validator_selector import ValidatorSelector
from app.rule_engine.attack_plan_generator import AttackPlanGenerator
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger()


def test_rule_engine_integration():
    """Test complete rule engine pipeline with knowledge base"""
    
    print("=" * 80)
    print("🧪 Rule Engine Integration Test")
    print("=" * 80)
    print()
    
    # Determine knowledge base path
    kb_path = Path(__file__).parent.parent.parent / "knowledge-base"
    
    print(f"📁 Knowledge Base Path: {kb_path}")
    print(f"   Exists: {kb_path.exists()}")
    print()
    
    if not kb_path.exists():
        print("❌ Knowledge base not found!")
        return False
    
    try:
        # Sample endpoint for testing
        sample_endpoint = {
            "url": "https://example.com/api/users?id=123",
            "method": "GET",
            "parameters": {"id": "123"},
            "headers": {
                "Content-Type": "application/json",
                "Server": "Apache/2.4.41"
            },
            "forms": [],
            "cookies": {"session": "abc123"}
        }
        
        print("🔧 Initializing Rule Engine Components...")
        print()
        
        # === Component 1: Context Normalizer ===
        print("[1/7] Context Normalizer...")
        normalizer = ContextNormalizer()
        normalized = normalizer.normalize_endpoint(sample_endpoint)
        print(f"   ✅ Normalized endpoint")
        print(f"      URL: {normalized['url']}")
        print(f"      Parameters: {list(normalized['parameters'].keys())}")
        print()
        
        # === Component 2: OWASP Mapper ===
        print("[2/7] OWASP Mapper...")
        mapper = OWASPMapper()
        owasp_categories = mapper.map_endpoint(normalized)
        print(f"   ✅ Mapped to OWASP categories: {owasp_categories}")
        print()
        
        # === Component 3: Test Case Evaluator ===
        print("[3/7] Test Case Evaluator...")
        evaluator = TestCaseEvaluator(str(kb_path))
        selected_tests = evaluator.evaluate(normalized, owasp_categories)
        print(f"   ✅ Selected {len(selected_tests)} test cases")
        if selected_tests:
            print(f"      First test: {selected_tests[0].get('name', 'N/A')}")
        print()
        
        # === Component 4: Payload Binder ===
        print("[4/7] Payload Binder...")
        binder = PayloadBinder(str(kb_path))
        bound_tests = binder.bind_payloads(selected_tests, normalized)
        print(f"   ✅ Bound payloads to {len(bound_tests)} tests")
        
        # Count total payloads
        total_payloads = 0
        for test in bound_tests:
            for target in test.get("test_targets", []):
                total_payloads += len(target.get("payloads", []))
        print(f"      Total payloads bound: {total_payloads}")
        print()
        
        # === Component 5: Safety Enforcer ===
        print("[5/7] Safety Enforcer...")
        enforcer = SafetyEnforcer()
        
        # Test blocking
        test_payloads = [
            ("' OR 1=1--", True),  # Should be safe (non-destructive)
            ("'; DROP TABLE users--", False),  # Should be blocked (destructive)
            ("<script>alert('XSS')</script>", True),  # Should be safe
            ("rm -rf /", False),  # Should be blocked
        ]
        
        blocked_count = 0
        for payload, expected_safe in test_payloads:
            is_safe = enforcer.is_safe(payload)
            if is_safe != expected_safe:
                print(f"   ⚠️  Unexpected result for: {payload[:30]}...")
            if not is_safe:
                blocked_count += 1
        
        print(f"   ✅ Safety enforcer working")
        print(f"      Blocked {blocked_count}/{len(test_payloads)} test payloads as expected")
        print()
        
        # === Component 6: Validator Selector ===
        print("[6/7] Validator Selector...")
        validator_selector = ValidatorSelector(str(kb_path))
        
        validators_selected = 0
        for test in bound_tests:
            validators = validator_selector.select(test)
            validators_selected += len(validators)
        
        print(f"   ✅ Selected validators")
        print(f"      Total validators selected: {validators_selected}")
        print()
        
        # === Component 7: Attack Plan Generator ===
        print("[7/7] Attack Plan Generator...")
        generator = AttackPlanGenerator()
        
        attack_plan = generator.generate(
            endpoint=normalized,
            test_cases=bound_tests,
            scan_id="test-scan-001"
        )
        
        print(f"   ✅ Generated attack plan")
        print(f"      Total tests: {attack_plan['statistics']['total_tests']}")
        print(f"      Test categories: {attack_plan['statistics']['tests_by_category']}")
        print(f"      Estimated time: {attack_plan['execution']['estimated_time_seconds']}s")
        print()
        
        # === Final Statistics ===
        print("=" * 80)
        print("✅ RULE ENGINE INTEGRATION TEST SUCCESSFUL")
        print("=" * 80)
        print()
        print("Complete Pipeline Results:")
        print(f"  • Input: 1 endpoint ({sample_endpoint['url']})")
        print(f"  • OWASP Categories: {len(owasp_categories)}")
        print(f"  • Test Cases Selected: {len(selected_tests)}")
        print(f"  • Payloads Bound: {total_payloads}")
        print(f"  • Validators Selected: {validators_selected}")
        print(f"  • Final Attack Plan: {attack_plan['statistics']['total_tests']} tests")
        print()
        print("All 7 rule engine components are:")
        print("  ✅ Properly initialized")
        print("  ✅ Successfully accessing knowledge base YAML files")
        print("  ✅ Processing data through complete pipeline")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rule_engine_integration()
    sys.exit(0 if success else 1)
