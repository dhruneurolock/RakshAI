"""
Rule Engine - Component 3: Test Case Evaluator
Selects applicable test cases from 96 YAML files based on context
"""
import yaml
import structlog
from typing import Dict, List, Any
from pathlib import Path
from app.core.knowledge_base import get_knowledge_base_loader
from app.core.config import settings

logger = structlog.get_logger()


class TestCaseEvaluator:
    """
    Evaluates which test cases from the knowledge base are applicable
    to a given endpoint based on OWASP categories and context.
    
    Input: Normalized endpoint + OWASP categories
    Output: List of applicable test cases
    """
    
    def __init__(self, knowledge_base_path: str = "./knowledge-base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.logger = logger.bind(component="TestCaseEvaluator")
        
        # Use centralized knowledge base loader
        self.kb_loader = get_knowledge_base_loader(str(knowledge_base_path))
        self.test_cases_cache = self.kb_loader.get_all_test_cases()
        
        self.logger.info(
            "Test case evaluator initialized",
            total_categories=len(self.test_cases_cache),
            total_tests=sum(len(cases) for cases in self.test_cases_cache.values())
        )
    
    def _load_test_cases(self):
        """DEPRECATED: Now using centralized KnowledgeBaseLoader"""
        # This method is no longer needed but kept for compatibility
        pass
    
    def evaluate(
        self, 
        normalized_endpoint: Dict[str, Any], 
        owasp_categories: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate which test cases are applicable to this endpoint
        
        Args:
            normalized_endpoint: Normalized endpoint context
            owasp_categories: List of applicable OWASP categories
            
        Returns:
            List of applicable test cases with metadata
        """
        applicable_tests = []
        
        for category in owasp_categories:
            # Get test cases for this category
            category_tests = self._get_category_tests(category)
            
            # Filter based on endpoint context
            for test_case in category_tests:
                if self._is_test_applicable(test_case, normalized_endpoint):
                    applicable_tests.append({
                        "category": category,
                        "test_case": test_case,
                        "priority": self._calculate_priority(test_case, normalized_endpoint)
                    })
        
        # Sort by priority (highest first)
        applicable_tests.sort(key=lambda x: x["priority"], reverse=True)
        
        self.logger.info(
            "Test cases evaluated",
            url=normalized_endpoint.get("url"),
            total_applicable=len(applicable_tests)
        )
        
        return applicable_tests
    
    def _get_category_tests(self, category: str) -> List[Dict[str, Any]]:
        """Get test cases for a specific OWASP category"""
        # Map OWASP codes to directory names
        category_map = {
            "A01": "A01-broken-access-control",
            "A02": "A02-security-misconfiguration",
            "A03": "A03-software-supply-chain",
            "A04": "A04-crypto-failures",
            "A05": "A05-injection",
            "A06": "A06-insecure-design",
            "A07": "A07-auth-failures",
            "A08": "A08-software-data-integrity",
            "A09": "A09-logging-alerting",
            "A10": "A10-ssrf"
        }
        
        category_dir = category_map.get(category, category)
        return self.test_cases_cache.get(category_dir, [])
    
    def _is_test_applicable(
        self, 
        test_case: Dict[str, Any], 
        endpoint: Dict[str, Any]
    ) -> bool:
        """
        Determine if a test case is applicable to an endpoint
        using deterministic rules
        """
        # Get test case requirements
        requirements = test_case.get("requirements", {})
        
        # Check HTTP method requirements
        required_methods = requirements.get("methods", [])
        if required_methods:
            endpoint_method = endpoint.get("method", "GET")
            if endpoint_method not in required_methods:
                return False
        
        # Check parameter requirements
        required_param_types = requirements.get("parameter_types", [])
        if required_param_types:
            endpoint_params = endpoint.get("parameters", {})
            endpoint_param_types = set(
                param.get("type") for param in endpoint_params.values()
            )
            
            # Test requires at least one matching parameter type
            if not any(ptype in endpoint_param_types for ptype in required_param_types):
                return False
        
        # Check endpoint type requirements
        required_endpoint_type = requirements.get("endpoint_type")
        if required_endpoint_type:
            actual_type = endpoint.get("metadata", {}).get("endpoint_type")
            if actual_type != required_endpoint_type:
                return False
        
        # Check authentication requirements
        requires_auth = requirements.get("requires_auth")
        if requires_auth is not None:
            has_auth = endpoint.get("metadata", {}).get("has_auth", False)
            if requires_auth and not has_auth:
                return False
        
        # Check injectable parameters requirement
        requires_injectable = requirements.get("requires_injectable_params", False)
        if requires_injectable:
            endpoint_params = endpoint.get("parameters", {})
            has_injectable = any(
                param.get("injectable", False) 
                for param in endpoint_params.values()
            )
            if not has_injectable:
                return False
        
        return True
    
    def _calculate_priority(
        self, 
        test_case: Dict[str, Any], 
        endpoint: Dict[str, Any]
    ) -> int:
        """
        Calculate test case priority based on severity and context match
        
        Priority scale: 0-100
        - Severity: 0-70 points
        - Context match: 0-30 points
        """
        priority = 0
        
        # Severity-based priority
        severity = test_case.get("severity", "medium").lower()
        severity_points = {
            "critical": 70,
            "high": 50,
            "medium": 30,
            "low": 15,
            "info": 5
        }
        priority += severity_points.get(severity, 30)
        
        # Context match bonus
        requirements = test_case.get("requirements", {})
        
        # Exact method match
        required_methods = requirements.get("methods", [])
        if required_methods and endpoint.get("method") in required_methods:
            priority += 10
        
        # Multiple injectable parameters
        endpoint_params = endpoint.get("parameters", {})
        injectable_count = sum(
            1 for param in endpoint_params.values() 
            if param.get("injectable", False)
        )
        priority += min(injectable_count * 5, 20)  # Max 20 bonus points
        
        return priority


# Singleton instance
test_case_evaluator = TestCaseEvaluator(knowledge_base_path=settings.KNOWLEDGE_BASE_PATH)
