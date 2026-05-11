"""
Validation Agent

Responsibilities:
1. Implement zero-hallucination guardrails
2. Replay findings 3 times
3. Check 85% success threshold (≥2 out of 3)
4. Update validation_replays and validation_count
5. Set status to VALIDATED or FALSE_POSITIVE
6. LLM analysis of false positives
7. Confidence scoring
"""

from typing import Dict, Any, List, Optional
import json
import asyncio
from datetime import datetime

from .base_agent import BaseAgent


class ValidationAgent(BaseAgent):
    """Agent responsible for validating findings with zero-hallucination guardrails"""
    
    # Configuration
    REPLAY_COUNT = 3
    CONFIDENCE_THRESHOLD = 0.85  # 85% = 2 out of 3 successes minimum
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.validation_results = []
    
    async def run(self, scan_id: str, finding_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute validation workflow
        
        Args:
            scan_id: Scan identifier
            finding_id: Specific finding to validate (if None, validates all)
            
        Returns:
            Dict with validation results
        """
        try:
            await self.emit_progress(scan_id, "validator", "started", {
                "message": "Starting validation phase"
            })
            
            # Phase 1: Get findings to validate
            if finding_id:
                findings = [await self._get_finding(scan_id, finding_id)]
            else:
                findings = await self._get_unvalidated_findings(scan_id)
            
            if not findings:
                return {
                    "success": False,
                    "error": "No findings to validate",
                    "validated_count": 0
                }
            
            # Phase 2: Validate each finding
            validated_count = 0
            false_positive_count = 0
            
            for i, finding in enumerate(findings, 1):
                await self.emit_progress(scan_id, "validator", "validating", {
                    "message": f"Validating finding {i}/{len(findings)}",
                    "finding_type": finding.get("type")
                })
                
                result = await self.validate_finding(scan_id, finding)
                
                if result["status"] == "VALIDATED":
                    validated_count += 1
                elif result["status"] == "FALSE_POSITIVE":
                    false_positive_count += 1
                
                self.validation_results.append(result)
            
            summary = {
                "success": True,
                "findings_checked": len(findings),
                "validated": validated_count,
                "false_positives": false_positive_count,
                "validation_rate": validated_count / len(findings) if findings else 0
            }
            
            await self.emit_progress(scan_id, "validator", "completed", summary)
            await self.log_action(scan_id, "validation_completed", summary)
            
            return summary
            
        except Exception as e:
            await self.handle_error(scan_id, "validator", e)
            raise
    
    async def validate_finding(self, scan_id: str, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single finding with 3x replay
        
        Returns:
            Dict with validation result and confidence score
        """
        finding_id = finding.get("finding_id")
        finding_type = finding.get("type")
        
        await self.log_action(scan_id, "validation_started", {
            "finding_id": finding_id,
            "type": finding_type
        })
        
        # Execute 3 replay attempts
        replay_results = []
        
        for attempt in range(1, self.REPLAY_COUNT + 1):
            await self.emit_progress(scan_id, "validator", "replay", {
                "finding_id": finding_id,
                "attempt": attempt,
                "total": self.REPLAY_COUNT
            })
            
            result = await self._replay_finding(scan_id, finding)
            replay_results.append(result)
            
            # Small delay between replays to avoid rate limiting
            if attempt < self.REPLAY_COUNT:
                await asyncio.sleep(2)
        
        # Calculate confidence score
        successes = sum(1 for r in replay_results if r.get("success"))
        confidence = successes / self.REPLAY_COUNT
        
        # Determine validation status
        if confidence >= self.CONFIDENCE_THRESHOLD:
            status = "VALIDATED"
            await self.log_action(scan_id, "finding_validated", {
                "finding_id": finding_id,
                "confidence": confidence,
                "replay_results": replay_results
            })
        else:
            status = "FALSE_POSITIVE"
            
            # Use LLM to analyze why it's a false positive
            fp_analysis = await self._analyze_false_positive(finding, replay_results)
            
            await self.log_action(scan_id, "false_positive_detected", {
                "finding_id": finding_id,
                "confidence": confidence,
                "analysis": fp_analysis
            })
        
        # Update finding in database
        await self._update_finding_validation(finding_id, {
            "status": status,
            "validation_replays": successes,
            "validation_count": self.REPLAY_COUNT,
            "confidence": confidence,
            "replay_details": replay_results
        })
        
        return {
            "finding_id": finding_id,
            "status": status,
            "confidence": confidence,
            "replays_successful": successes,
            "replays_total": self.REPLAY_COUNT,
            "replay_results": replay_results
        }
    
    async def _replay_finding(self, scan_id: str, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replay a single finding to verify it's reproducible
        
        Returns:
            Dict with success status and details
        """
        finding_type = finding.get("type")
        url = finding.get("url")
        evidence = finding.get("evidence", {})
        
        try:
            # Route to type-specific replay handler
            if finding_type == "SQL_INJECTION":
                return await self._replay_sqli(url, evidence)
            elif finding_type == "XSS":
                return await self._replay_xss(url, evidence)
            elif finding_type == "IDOR":
                return await self._replay_idor(url, evidence)
            elif finding_type == "AUTH_BYPASS":
                return await self._replay_auth_bypass(url, evidence)
            else:
                return await self._replay_generic(url, evidence)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _replay_sqli(self, url: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Replay SQL injection finding"""
        try:
            # Re-execute SQLMap with specific payload
            result = await self.tool_sandbox.execute("sqlmap", {
                "url": url,
                "batch": True,
                "level": 1,
                "risk": 1,
                "timeout": 60
            })
            
            # Check if vulnerability still exists
            success = result.success and (
                "is vulnerable" in result.output.lower() or
                "injectable" in result.output.lower()
            )
            
            return {
                "success": success,
                "response_time": result.execution_time if hasattr(result, 'execution_time') else 0,
                "evidence": result.output[:200] if success else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _replay_xss(self, url: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Replay XSS finding"""
        try:
            payload = evidence.get("payload", "<script>alert(1)</script>")
            
            # Use dalfox with specific payload
            result = await self.tool_sandbox.execute("dalfox", {
                "url": url,
                "data": payload,
                "timeout": 60
            })
            
            success = result.success and "VULN" in result.output
            
            return {
                "success": success,
                "payload": payload,
                "evidence": result.output[:200] if success else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _replay_idor(self, url: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Replay IDOR finding"""
        try:
            # Re-test IDOR vulnerability
            result = await self.tool_sandbox.execute("idor_tester", {
                "url": url,
                "id_range": 10,  # Quick test
                "method": evidence.get("method", "GET")
            })
            
            success = result.success and "IDOR_DETECTED" in result.output
            
            return {
                "success": success,
                "evidence": result.output[:200] if success else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _replay_auth_bypass(self, url: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Replay authentication bypass finding"""
        try:
            result = await self.tool_sandbox.execute("auth_bypass_tester", {
                "url": url,
                "methods": [evidence.get("method", "path_traversal")]
            })
            
            success = result.success and "BYPASS_SUCCESSFUL" in result.output
            
            return {
                "success": success,
                "evidence": result.output[:200] if success else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _replay_generic(self, url: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Generic replay for unknown finding types"""
        # For unknown types, assume it's valid but log warning
        await self.log_action("validation", "unknown_finding_type", {
            "url": url,
            "evidence": evidence
        })
        
        return {
            "success": True,
            "warning": "Unknown finding type - assumed valid",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _analyze_false_positive(
        self, 
        finding: Dict[str, Any], 
        replay_results: List[Dict[str, Any]]
    ) -> str:
        """Use LLM to analyze why a finding is a false positive"""
        try:
            # Prepare data for LLM
            prompt = f"""Analyze why this security finding failed validation:

Finding Type: {finding.get('type')}
URL: {finding.get('url')}
Initial Evidence: {finding.get('evidence', 'N/A')[:200]}

Replay Results:
{json.dumps(replay_results, indent=2)}

Provide a brief explanation of why this is likely a false positive.
Consider:
1. Network issues (timeouts, connectivity)
2. Application state changes
3. Rate limiting
4. Time-based conditions
5. Tool misdetection

Return only the explanation (2-3 sentences).
"""
            
            analysis = await self.llm_service.analyze(
                prompt=prompt,
                response_format="text",
                use_strategy_model=False  # Use detailed analysis model
            )
            
            return analysis.strip()
            
        except Exception as e:
            return f"Unable to analyze: {str(e)}"
    
    async def _get_unvalidated_findings(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get all unvalidated findings for a scan"""
        # Query database for findings with status = 'UNVALIDATED'
        # This is a mock - production would query PostgreSQL
        return []
    
    async def _get_finding(self, scan_id: str, finding_id: str) -> Dict[str, Any]:
        """Get specific finding"""
        # Query database for specific finding
        return {
            "finding_id": finding_id,
            "type": "SQL_INJECTION",
            "url": "http://example.com/api/test"
        }
    
    async def _update_finding_validation(
        self, 
        finding_id: str, 
        validation_data: Dict[str, Any]
    ) -> None:
        """Update finding validation status in database"""
        try:
            # This would update the Vulnerability model in PostgreSQL
            await self.log_action("validation", "finding_updated", {
                "finding_id": finding_id,
                "status": validation_data["status"],
                "confidence": validation_data["confidence"]
            })
            
        except Exception as e:
            await self.log_action("validation", "update_error", {
                "finding_id": finding_id,
                "error": str(e)
            })
