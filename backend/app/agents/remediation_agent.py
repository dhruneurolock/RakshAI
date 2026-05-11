"""
Remediation Agent
Generates instant LLM-based remediation solutions for vulnerabilities
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.models.models import Vulnerability
from app.core.database import get_db, SessionLocal

logger = logging.getLogger(__name__)


class RemediationAgent(BaseAgent):
    """
    LLM-powered remediation solution generator
    
    Responsibilities:
    - Analyze vulnerability details
    - Generate comprehensive remediation guidance
    - Provide code examples for immediate patching
    - Calculate remediation timeline and effort
    - Store remediation solutions in database
    """
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.db = None
    
    async def initialize(self):
        """Initialize remediation agent"""
        await super().initialize()
        logger.info(f"RemediationAgent initialized: {self.agent_id}")
    
    async def run(
        self,
        scan_id: str,
        vulnerability_id: Optional[int] = None,
        vulnerability_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate remediation solution for a vulnerability
        
        Args:
            scan_id: Scan identifier
            vulnerability_id: Database vulnerability ID (if from DB)
            vulnerability_data: Vulnerability details (dict)
            
        Returns:
            Remediation solution with code examples
        """
        try:
            logger.info(f"Generating remediation for vulnerability {vulnerability_id or 'provided'}")
            
            # Get vulnerability data if ID provided
            if vulnerability_id and not vulnerability_data:
                db = SessionLocal()
                try:
                    vuln = db.query(Vulnerability).filter(
                        Vulnerability.id == vulnerability_id
                    ).first()
                    
                    if not vuln:
                        logger.error(f"Vulnerability {vulnerability_id} not found")
                        return {
                            "status": "error",
                            "message": "Vulnerability not found"
                        }
                    
                    vulnerability_data = self._serialize_vulnerability(vuln)
                finally:
                    db.close()
                

            
            if not vulnerability_data:
                return {
                    "status": "error",
                    "message": "No vulnerability data provided"
                }
            
            # Detect target technology
            target_tech = self._detect_technology(vulnerability_data)
            logger.info(f"Detected technology: {target_tech}")
            
            # Generate LLM-based remediation
            if not self.llm_service:
                return {
                    "status": "error",
                    "message": "LLM service not initialized"
                }
            
            remediation = await self.llm_service.generate_remediation(
                vulnerability=vulnerability_data,
                target_technology=target_tech
            )
            
            # Enhance remediation with additional context
            remediation = self._enhance_remediation(remediation, vulnerability_data)
            
            # Log event
            await self.emit_progress(scan_id, {
                "type": "remediation_generated",
                "vuln_id": vulnerability_id,
                "vulnerability_type": vulnerability_data.get('type'),
                "severity": vulnerability_data.get('severity'),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Remediation generated successfully for {vulnerability_data.get('type')}")
            
            return {
                "status": "success",
                "vulnerability_id": vulnerability_id,
                "vulnerability_type": vulnerability_data.get('type'),
                "severity": vulnerability_data.get('severity'),
                "technology": target_tech,
                "remediation": remediation,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Remediation generation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _serialize_vulnerability(self, vuln: Vulnerability) -> Dict[str, Any]:
        """Convert database vulnerability to dict"""
        return {
            'id': vuln.id,
            'type': vuln.vulnerability_type,
            'title': vuln.title,
            'description': vuln.description,
            'severity': vuln.severity.value if hasattr(vuln.severity, 'value') else str(vuln.severity),
            'owasp_category': vuln.owasp_category,
            'cwe_id': vuln.cwe_id,
            'endpoint': vuln.endpoint.url if vuln.endpoint else '',
            'method': vuln.endpoint.method if vuln.endpoint else '',
            'evidence': vuln.response_evidence or '',
            'affected_parameter': vuln.affected_parameter or '',
        }
    
    def _detect_technology(self, vulnerability_data: Dict[str, Any]) -> str:
        """
        Detect target technology from vulnerability evidence
        
        Args:
            vulnerability_data: Vulnerability details
            
        Returns:
            Technology name (PHP, Python, Node.js, etc.)
        """
        endpoint = vulnerability_data.get('endpoint', '').lower()
        evidence = vulnerability_data.get('evidence', '').lower()
        
        # Check for technology indicators in endpoint/evidence
        if any(ext in endpoint for ext in ['.php', '.jsp', '.asp', '.aspx']):
            if '.php' in endpoint:
                return 'PHP'
            elif '.jsp' in endpoint:
                return 'Java'
            elif '.asp' in endpoint or '.aspx' in endpoint:
                return 'ASP.NET'
        
        if any(tech in evidence for tech in ['laravel', 'symfony', 'cake php', 'yii']):
            return 'PHP Framework'
        elif any(tech in evidence for tech in ['django', 'flask', 'fastapi']):
            return 'Python'
        elif any(tech in evidence for tech in ['express', 'fastapi', 'nest.js']):
            return 'Node.js'
        elif any(tech in evidence for tech in ['spring', 'hibernate', 'maven']):
            return 'Java'
        elif any(tech in evidence for tech in ['.net', 'mvc', 'aspnet']):
            return 'ASP.NET'
        
        # Check common headers
        if 'server:' in evidence:
            if 'apache' in evidence:
                return 'PHP/Apache'
            elif 'nginx' in evidence:
                return 'Node.js/Nginx or PHP/Nginx'
            elif 'iis' in evidence:
                return 'ASP.NET/IIS'
        
        # Default based on OWASP category
        owasp = vulnerability_data.get('owasp_category', '').lower()
        if 'injection' in owasp:
            return 'General/SQL'
        
        return 'General'
    
    def _enhance_remediation(
        self,
        remediation: Dict[str, Any],
        vulnerability_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance remediation with additional resources and context
        
        Args:
            remediation: Generated remediation solution
            vulnerability_data: Vulnerability details
            
        Returns:
            Enhanced remediation
        """
        # Add references
        references = self._get_references(vulnerability_data)
        if references:
            remediation['references'] = references
        
        # Add severity-based urgency
        severity = vulnerability_data.get('severity', '').lower()
        if severity in ['critical']:
            remediation['urgency'] = 'IMMEDIATE - Apply within 24 hours'
        elif severity in ['high']:
            remediation['urgency'] = 'HIGH - Apply within 1 week'
        elif severity in ['medium']:
            remediation['urgency'] = 'MEDIUM - Apply within 2 weeks'
        else:
            remediation['urgency'] = 'LOW - Apply within 1 month'
        
        # Add compliance notes
        owasp = vulnerability_data.get('owasp_category', '')
        cwe = vulnerability_data.get('cwe_id')
        
        compliance = []
        if owasp:
            compliance.append(f"OWASP Top 10: {owasp}")
        if cwe:
            compliance.append(f"CWE-{cwe}")
        
        if compliance:
            remediation['compliance_impact'] = compliance
        
        return remediation
    
    def _get_references(self, vulnerability_data: Dict[str, Any]) -> list:
        """Get reference links for vulnerability remediation"""
        references = []
        
        vuln_type = vulnerability_data.get('type', '')
        owasp = vulnerability_data.get('owasp_category', '')
        cwe = vulnerability_data.get('cwe_id')
        
        # OWASP References
        if 'CSRF' in vuln_type.upper():
            references.extend([
                "https://owasp.org/www-community/attacks/csrf",
                "https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html",
                "https://cwe.mitre.org/data/definitions/352.html"
            ])
        elif 'SQL' in vuln_type.upper():
            references.extend([
                "https://owasp.org/www-community/attacks/SQL_Injection",
                "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
                "https://cwe.mitre.org/data/definitions/89.html"
            ])
        elif 'XSS' in vuln_type.upper():
            references.extend([
                "https://owasp.org/www-community/attacks/xss/",
                "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
                "https://cwe.mitre.org/data/definitions/79.html"
            ])
        elif 'IDOR' in vuln_type.upper() or 'ACCESS_CONTROL' in vuln_type.upper():
            references.extend([
                "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
                "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html",
                "https://cwe.mitre.org/data/definitions/639.html"
            ])
        
        # Add CWE reference if available
        if cwe:
            references.append(f"https://cwe.mitre.org/data/definitions/{cwe}.html")
        
        return list(set(references))  # Remove duplicates
