"""
Rule Engine - Component 7: Attack Plan Generator
Assembles the final attack execution plan
"""
import structlog
from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime

logger = structlog.get_logger()


class AttackPlanGenerator:
    """
    Generates the final attack execution plan by combining:
    - Normalized endpoint context
    - OWASP categories
    - Applicable test cases
    - Bound payloads
    - Selected validators
    
    This is the culmination of the rule engine pipeline.
    
    Input: All rule engine outputs
    Output: Complete, executable attack plan
    """
    
    def __init__(self):
        self.logger = logger.bind(component="AttackPlanGenerator")
    
    def generate(
        self,
        normalized_endpoint: Dict[str, Any],
        owasp_categories: List[str],
        applicable_tests: List[Dict[str, Any]],
        scan_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete attack plan for an endpoint
        
        Args:
            normalized_endpoint: Normalized endpoint from ContextNormalizer
            owasp_categories: OWASP categories from OWASPMapper
            applicable_tests: Test cases from TestCaseEvaluator (with bound payloads)
            scan_config: Optional scan configuration
            
        Returns:
            Complete attack plan ready for execution
        """
        plan_id = str(uuid.uuid4())
        
        attack_plan = {
            "plan_id": plan_id,
            "generated_at": datetime.utcnow().isoformat(),
            "target": {
                "url": normalized_endpoint.get("url"),
                "method": normalized_endpoint.get("method"),
                "endpoint_type": normalized_endpoint.get("metadata", {}).get("endpoint_type")
            },
            "scope": {
                "owasp_categories": owasp_categories,
                "total_tests": len(applicable_tests)
            },
            "tests": self._organize_tests(applicable_tests),
            "execution_config": self._generate_execution_config(scan_config),
            "metadata": {
                "has_auth": normalized_endpoint.get("metadata", {}).get("has_auth", False),
                "technology": normalized_endpoint.get("metadata", {}).get("technology"),
                "injectable_params": self._get_injectable_params(normalized_endpoint)
            }
        }
        
        # Add statistics
        attack_plan["statistics"] = self._calculate_statistics(attack_plan)
        
        self.logger.info(
            "Attack plan generated",
            plan_id=plan_id,
            url=normalized_endpoint.get("url"),
            total_tests=len(applicable_tests),
            owasp_categories=owasp_categories
        )
        
        return attack_plan
    
    def _organize_tests(self, applicable_tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Organize tests into execution-ready format"""
        organized_tests = []
        
        for test_item in applicable_tests:
            test_case = test_item.get("test_case", {})
            category = test_item.get("category")
            priority = test_item.get("priority", 0)
            
            organized_test = {
                "test_id": str(uuid.uuid4()),
                "category": category,
                "priority": priority,
                "name": test_case.get("name", "Unknown Test"),
                "description": test_case.get("description", ""),
                "severity": test_case.get("severity", "medium"),
                "cwe": test_case.get("cwe"),
                "owasp": test_case.get("owasp"),
                
                # Execution details
                "method": test_case.get("method", "GET"),
                "payloads": test_case.get("bound_payloads", []),
                "validators": test_case.get("validators", []),
                
                # Configuration
                "timeout": test_case.get("timeout", 30),
                "retry_count": test_case.get("retry_count", 0),
                "rate_limit": test_case.get("rate_limit", 10),
                
                # Expected behavior
                "expected_indicators": test_case.get("expected_indicators", []),
                "false_positive_filters": test_case.get("false_positive_filters", [])
            }
            
            organized_tests.append(organized_test)
        
        return organized_tests
    
    def _generate_execution_config(
        self,
        scan_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate execution configuration"""
        default_config = {
            "max_concurrent_tests": 5,
            "request_timeout": 30,
            "max_redirects": 3,
            "retry_on_failure": True,
            "max_retries": 2,
            "delay_between_tests": 0.5,  # seconds
            "rate_limit_per_second": 10,
            "follow_redirects": True,
            
            # Safety settings
            "enable_safety_enforcer": True,
            "max_payload_size": 10000,  # bytes
            "stop_on_critical_finding": False,
            
            # Logging
            "log_all_requests": True,
            "log_responses": True,
            "verbose": False
        }
        
        if scan_config:
            # Merge with scan-specific config
            default_config.update(scan_config)
        
        return default_config
    
    def _get_injectable_params(self, endpoint: Dict[str, Any]) -> List[str]:
        """Extract list of injectable parameter names"""
        parameters = endpoint.get("parameters", {})
        return [
            name for name, param in parameters.items()
            if param.get("injectable", False)
        ]
    
    def _calculate_statistics(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate plan statistics"""
        tests = plan.get("tests", [])
        
        # Count payloads
        total_payloads = sum(len(test.get("payloads", [])) for test in tests)
        
        # Count by severity
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for test in tests:
            severity = test.get("severity", "medium").lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by category
        category_counts = {}
        for test in tests:
            category = test.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Estimate execution time
        estimated_time = self._estimate_execution_time(plan)
        
        return {
            "total_tests": len(tests),
            "total_payloads": total_payloads,
            "avg_payloads_per_test": total_payloads / len(tests) if tests else 0,
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "estimated_execution_time_seconds": estimated_time
        }
    
    def _estimate_execution_time(self, plan: Dict[str, Any]) -> float:
        """Estimate total execution time in seconds"""
        tests = plan.get("tests", [])
        config = plan.get("execution_config", {})
        
        total_time = 0.0
        
        for test in tests:
            payload_count = len(test.get("payloads", []))
            timeout = test.get("timeout", config.get("request_timeout", 30))
            delay = config.get("delay_between_tests", 0.5)
            
            # Time per test = (payloads * timeout) + delays
            test_time = (payload_count * timeout) + (payload_count * delay)
            total_time += test_time
        
        # Account for concurrency
        max_concurrent = config.get("max_concurrent_tests", 5)
        if max_concurrent > 1:
            total_time = total_time / max_concurrent
        
        return round(total_time, 2)


# Singleton instance
attack_plan_generator = AttackPlanGenerator()
