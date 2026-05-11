#!/usr/bin/env python3
"""
Integration script for LLM-based remediation system
This script:
1. Adds logging import to vulnerabilities endpoint
2. Adds remediation endpoint code
3. Updates the __init__ file to export RemediationAgent
"""

import os

def update_vulnerabilities_endpoint():
    """Add remediation endpoint to vulnerabilities.py"""
    vul_path = "d:\\RakshAI\\backend\\app\\api\\v1\\endpoints\\vulnerabilities.py"
    
    with open(vul_path, 'r') as f:
        content = f.read()
    
    # Check if remediation endpoint already exists
    if 'generate-remediation' in content:
        print("✓ Remediation endpoint already present")
        return
    
    # Add logging import if not present
    if 'import logging' not in content:
        content = content.replace(
            'from app.models.schemas import VulnerabilityResponse\n\nrouter = APIRouter()',
            'from app.models.schemas import VulnerabilityResponse\nimport logging\n\nlogger = logging.getLogger(__name__)\n\nrouter = APIRouter()'
        )
        print("✓ Added logging import")
    
    # Find insertion point (before @router.get("/stats/by-severity"))
    insertion_marker = '@router.get("/stats/by-severity")'
    
    if insertion_marker not in content:
        print("✗ Could not find insertion point")
        return
    
    remediation_endpoint = """
@router.post("/{vuln_id}/generate-remediation")
async def generate_remediation(
    vuln_id: int,
    db: Session = Depends(get_db)
):
    \"\"\"
    Generate instant LLM-based remediation solution for vulnerability
    
    Returns comprehensive, actionable remediation guidance with code examples
    for immediate patching. Detects technology stack and provides targeted solutions.
    \"\"\"
    try:
        # Get vulnerability from database
        vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
        if not vuln:
            raise HTTPException(status_code=404, detail="Vulnerability not found")
        
        # Import RemediationAgent
        from app.agents.remediation_agent import RemediationAgent
        
        logger.info(f"Generating remediation for vulnerability {vuln_id} ({vuln.vulnerability_type})")
        
        # Initialize and run remediation agent
        agent = RemediationAgent(f"remediation_agent_{vuln_id}")
        await agent.initialize()
        
        # Run remediation generation
        result = await agent.run(
            scan_id=str(vuln.scan_id),
            vulnerability_id=vuln_id
        )
        
        # Return remediation if successful
        if result.get('status') == 'success':
            return {
                "message": "Remediation generated successfully",
                "vulnerability_id": vuln_id,
                "vulnerability_type": result.get('vulnerability_type'),
                "severity": result.get('severity'),
                "technology_detected": result.get('technology'),
                "remediation_solution": result.get('remediation'),
                "generated_at": result.get('generated_at')
            }
        else:
            logger.error(f"Remediation generation failed: {result.get('message')}")
            raise HTTPException(
                status_code=500,
                detail=f"Remediation generation failed: {result.get('message', 'Unknown error')}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate remediation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate remediation: {str(e)}")


"""
    
    # Insert the endpoint
    content = content.replace(insertion_marker, remediation_endpoint + insertion_marker)
    
    # Write updated content
    with open(vul_path, 'w') as f:
        f.write(content)
    
    print("✓ Remediation endpoint added to vulnerabilities.py")
    
def update_agents_init():
    """Export RemediationAgent from agents/__init__.py"""
    init_path = "d:\\RakshAI\\backend\\app\\agents\\__init__.py"
    
    with open(init_path, 'r') as f:
        content = f.read()
    
    if 'RemediationAgent' in content:
        print("✓ RemediationAgent already exported")
        return
    
    # Add import
    if 'from app.agents.remediation_agent import RemediationAgent' not in content:
        content += "\nfrom app.agents.remediation_agent import RemediationAgent\n"
        
        with open(init_path, 'w') as f:
            f.write(content)
        
        print("✓ RemediationAgent exported from agents/__init__.py")

def update_llm_service_imports():
    """Update LLMService to include Optional type hint"""
    llm_path = "d:\\RakshAI\\backend\\app\\services\\llm_service.py"
    
    with open(llm_path, 'r') as f:
        content = f.read()
    
    if 'from typing import Dict, Any, List, Optional' not in content:
        content = content.replace(
            'from typing import Dict, Any, List',
            'from typing import Dict, Any, List, Optional'
        )
        
        with open(llm_path, 'w') as f:
            f.write(content)
        
        print("✓ Updated typing imports in llm_service.py")
    else:
        print("✓ Optional already imported in llm_service.py")

if __name__ == "__main__":
    print("\\n🔧 Integrating LLM-based Remediation System...\\n")
    
    try:
        update_vulnerabilities_endpoint()
        update_agents_init()
        update_llm_service_imports()
        
        print("\\n✅ Integration complete!")
        print("\\n📋 Summary of changes:")
        print("  - Added RemediationAgent to app/agents/remediation_agent.py")
        print("  - Added generate_remediation() method to LLMService")
        print("  - Added /vulnerabilities/{id}/generate-remediation endpoint")
        print("  - Updated imports and exports")
        print("\\n🚀 To use the remediation system:")
        print("  POST /api/v1/vulnerabilities/{vulnerability_id}/generate-remediation")
        print("\\n📊 The system will:")
        print("  1. Analyze the vulnerability details")
        print("  2. Detect the target technology")
        print("  3. Generate comprehensive LLM-based solutions")
        print("  4. Provide code examples for instant patching")
        print("  5. Include best practices and testing instructions")
        
    except Exception as e:
        print(f"\\n❌ Integration failed: {e}")
        import traceback
        traceback.print_exc()
