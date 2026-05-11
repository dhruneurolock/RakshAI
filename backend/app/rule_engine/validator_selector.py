"""
Rule Engine - Component 6: Validator Selector
Selects appropriate validators from 6 YAML validator files
"""
import yaml
import structlog
from typing import Dict, List, Any, Optional
from pathlib import Path
from app.core.knowledge_base import get_knowledge_base_loader
from app.core.config import settings

logger = structlog.get_logger()


class ValidatorSelector:
    """
    Selects appropriate validators for detecting vulnerabilities
    based on attack type and expected response patterns.
    
    Input: Test cases + payloads
    Output: Selected validators for each test
    """
    
    def __init__(self, knowledge_base_path: str = "./knowledge-base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.logger = logger.bind(component="ValidatorSelector")
        
        # Use centralized knowledge base loader
        self.kb_loader = get_knowledge_base_loader(str(knowledge_base_path))
        self.validators_cache = self.kb_loader.get_all_validators()
        
        self.logger.info(
            "Validator selector initialized",
            total_validators=len(self.validators_cache)
        )
    
    def _load_validators(self):
        """DEPRECATED: Now using centralized KnowledgeBaseLoader"""
        # This method is no longer needed but kept for compatibility
        pass
    
    def select(self, test_case: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Select validators for a test case
        
        Args:
            test_case: Test case requiring validators
            
        Returns:
            List of selected validators with configuration
        """
        validators = []
        
        # Get validation config from test case
        validation_config = test_case.get("validation", {})
        validator_types = validation_config.get("validators", [])
        
        if not validator_types:
            # Auto-select based on test category
            validator_types = self._auto_select_validators(test_case)
        
        for validator_type in validator_types:
            validator_data = self._get_validator(validator_type)
            if validator_data:
                validators.append({
                    "type": validator_type,
                    "config": validator_data,
                    "priority": self._get_validator_priority(validator_type, test_case)
                })
        
        # Sort by priority
        validators.sort(key=lambda x: x["priority"], reverse=True)
        
        self.logger.info(
            "Validators selected",
            test_case=test_case.get("_source_file"),
            validators=[v["type"] for v in validators]
        )
        
        return validators
    
    def _get_validator(self, validator_type: str) -> Optional[Dict[str, Any]]:
        """Get validator configuration by type"""
        # Map validator types to cache keys
        type_mapping = {
            "sql_error": "sql_errors",
            "xss_reflection": "xss_reflections",
            "error_pattern": "error-patterns",
            "status_code": "status-codes",
            "auth_indicator": "auth_indicators",
            "auth_bypass": "auth_indicators",  # Use same YAML file
            "data_leak": "data-leak",
            "reflection": "reflection"
        }
        
        cache_key = type_mapping.get(validator_type, validator_type)
        return self.validators_cache.get(cache_key)
    
    def _auto_select_validators(self, test_case: Dict[str, Any]) -> List[str]:
        """Auto-select validators based on test case type"""
        validators = []
        
        # Get test metadata
        test_category = test_case.get("category", "")
        test_type = test_case.get("type", "")
        
        # Always check status codes
        validators.append("status_code")
        
        # SQL Injection tests
        if "sql" in test_type.lower() or "injection" in test_category.lower():
            # SQL injection often bypasses authentication
            validators.extend(["sql_error", "error_pattern", "data_leak", "auth_bypass"])
        
        # XSS tests
        if "xss" in test_type.lower():
            validators.extend(["xss_reflection", "reflection"])
        
        # Authentication tests
        if "auth" in test_type.lower() or "authentication" in test_category.lower():
            validators.extend(["auth_indicator", "auth_bypass", "status_code"])
        
        # SSRF tests
        if "ssrf" in test_type.lower():
            validators.extend(["status_code", "reflection"])
        
        # Generic injection tests
        if "injection" in test_type.lower():
            validators.extend(["error_pattern", "reflection"])
        
        # Error-based detection
        validators.append("error_pattern")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_validators = []
        for v in validators:
            if v not in seen:
                seen.add(v)
                unique_validators.append(v)
        
        return unique_validators
    
    def _get_validator_priority(self, validator_type: str, test_case: Dict[str, Any]) -> int:
        """Calculate validator priority"""
        # Base priorities
        priorities = {
            "sql_error": 90,        # High confidence SQL errors
            "xss_reflection": 85,   # High confidence XSS
            "auth_bypass": 88,      # High confidence auth bypass (URL + content)
            "auth_indicator": 80,   # Auth bypass indicators
            "error_pattern": 70,    # Generic errors
            "status_code": 60,      # HTTP status
            "reflection": 50,       # Payload reflection
            "data_leak": 75         # Data exposure
        }
        
        base_priority = priorities.get(validator_type, 50)
        
        # Adjust based on test case severity
        severity = test_case.get("severity", "medium").lower()
        severity_boost = {
            "critical": 20,
            "high": 15,
            "medium": 10,
            "low": 5,
            "info": 0
        }
        
        return base_priority + severity_boost.get(severity, 10)


# Singleton instance
validator_selector = ValidatorSelector(knowledge_base_path=settings.KNOWLEDGE_BASE_PATH)
