"""
Knowledge Base Validation and Testing Script
Run this to verify all YAML files are correctly loaded
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.knowledge_base import KnowledgeBaseLoader
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


def validate_knowledge_base():
    """Validate knowledge base structure and content"""
    
    print("=" * 80)
    print("🔍 RakshAI Knowledge Base Validation")
    print("=" * 80)
    print()
    
    # Determine knowledge base path
    kb_path = Path(__file__).parent.parent.parent.parent / "knowledge-base"
    
    print(f"📁 Knowledge Base Path: {kb_path}")
    print(f"   Exists: {kb_path.exists()}")
    print()
    
    if not kb_path.exists():
        print("❌ Knowledge base directory not found!")
        print(f"   Expected location: {kb_path}")
        return False
    
    try:
        # Load knowledge base
        print("📥 Loading knowledge base...")
        kb = KnowledgeBaseLoader(str(kb_path))
        print("✅ Knowledge base loaded successfully!")
        print()
        
        # Validate data
        print("🔍 Validating loaded data...")
        validation = kb.validate_loaded_data()
        
        print("   Validation Results:")
        for check, result in validation.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}: {result}")
        print()
        
        # Display statistics
        print("📊 Knowledge Base Statistics:")
        print(f"   Test Case Categories: {len(kb.test_cases)}")
        for category, cases in kb.test_cases.items():
            print(f"      - {category}: {len(cases)} test files")
        print()
        
        total_payloads = sum(len(p) if isinstance(p, list) else 1 for p in kb.payloads.values())
        print(f"   Payload Types: {len(kb.payloads)}")
        print(f"   Total Payloads: {total_payloads}")
        for payload_key in sorted(kb.payloads.keys())[:5]:  # Show first 5
            count = len(kb.payloads[payload_key]) if isinstance(kb.payloads[payload_key], list) else 1
            print(f"      - {payload_key}: {count} payloads")
        if len(kb.payloads) > 5:
            print(f"      ... and {len(kb.payloads) - 5} more")
        print()
        
        print(f"   Validators: {len(kb.validators)}")
        for validator_name in sorted(kb.validators.keys()):
            print(f"      - {validator_name}")
        print()
        
        print(f"   Metadata Files: {len(kb.metadata)}")
        for metadata_name in sorted(kb.metadata.keys()):
            print(f"      - {metadata_name}")
        print()
        
        # Test specific queries
        print("🧪 Testing Knowledge Base Queries:")
        
        # Test 1: Get SQL injection payloads
        sql_payloads = kb.search_payloads(vulnerability_type="sql")
        print(f"   ✅ SQL Injection payloads found: {len(sql_payloads)}")
        
        # Test 2: Get XSS payloads
        xss_payloads = kb.search_payloads(vulnerability_type="xss")
        print(f"   ✅ XSS payloads found: {len(xss_payloads)}")
        
        # Test 3: Get OWASP mapping
        owasp = kb.get_owasp_mapping()
        print(f"   ✅ OWASP mappings loaded: {len(owasp.get('categories', {})) if isinstance(owasp, dict) else 'N/A'}")
        
        # Test 4: Get validators
        sql_validator = kb.get_validator("sql_errors")
        print(f"   ✅ SQL error validator loaded: {sql_validator is not None}")
        
        xss_validator = kb.get_validator("xss_reflections")
        print(f"   ✅ XSS reflection validator loaded: {xss_validator is not None}")
        
        print()
        
        # Final result
        if validation["all_valid"]:
            print("=" * 80)
            print("✅ KNOWLEDGE BASE VALIDATION SUCCESSFUL")
            print("=" * 80)
            print()
            print("All YAML files are loaded and accessible!")
            print("The rule engine can now use:")
            print(f"  • {sum(len(cases) for cases in kb.test_cases.values())} test cases across {len(kb.test_cases)} categories")
            print(f"  • {total_payloads} payloads across {len(kb.payloads)} types")
            print(f"  • {len(kb.validators)} validators")
            print(f"  • {len(kb.metadata)} metadata files")
            return True
        else:
            print("=" * 80)
            print("⚠️  VALIDATION COMPLETED WITH WARNINGS")
            print("=" * 80)
            print()
            print("Some expected data is missing. Review validation results above.")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = validate_knowledge_base()
    sys.exit(0 if success else 1)
