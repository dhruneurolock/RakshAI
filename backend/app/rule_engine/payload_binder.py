"""
Rule Engine - Component 4: Payload Binder
Binds safe payloads from ~1000 YAML entries to test cases
"""
import yaml
import structlog
from typing import Dict, List, Any, Optional
from pathlib import Path
import random
from app.core.knowledge_base import get_knowledge_base_loader
from app.core.config import settings

logger = structlog.get_logger()


class PayloadBinder:
    """
    Binds payloads from the knowledge base to test cases.
    Selects appropriate payloads based on vulnerability type and context.
    
    Input: Test cases + endpoint context
    Output: Test cases with bound payloads
    """
    
    def __init__(self, knowledge_base_path: str = "./knowledge-base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.logger = logger.bind(component="PayloadBinder")
        
        # Use centralized knowledge base loader
        self.kb_loader = get_knowledge_base_loader(str(knowledge_base_path))
        self.payloads_cache = self.kb_loader.get_all_payloads()
        
        total_payloads = sum(len(p) if isinstance(p, list) else 1 for p in self.payloads_cache.values())
        self.logger.info(
            "Payload binder initialized",
            payload_types=len(self.payloads_cache),
            total_payloads=total_payloads
        )
    
    def _load_payloads(self):
        """DEPRECATED: Now using centralized KnowledgeBaseLoader"""
        # This method is no longer needed but kept for compatibility
        pass
        
        total_payloads = sum(len(payloads) for payloads in self.payloads_cache.values())
        self.logger.info("Payloads loaded", total_payloads=total_payloads)
    
    def bind_payloads(
        self,
        test_case: Dict[str, Any],
        endpoint: Dict[str, Any],
        max_payloads: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Bind payloads to a test case
        
        Args:
            test_case: Test case requiring payloads
            endpoint: Normalized endpoint context
            max_payloads: Maximum number of payloads to bind
            
        Returns:
            List of bound payloads with metadata
        """
        # Check for test_cases array (common structure in knowledge base)
        if "test_cases" in test_case and isinstance(test_case["test_cases"], list):
            # Extract all payloads from all test cases in the file
            all_inline_payloads = []
            for individual_test in test_case["test_cases"]:
                test_payloads = individual_test.get("payloads", [])
                all_inline_payloads.extend(test_payloads)
            
            if all_inline_payloads:
                # Convert inline payloads to standard format
                converted_payloads = []
                for payload_item in all_inline_payloads:
                    if isinstance(payload_item, str):
                        # Simple string payload
                        converted_payloads.append({
                            "payload": payload_item,
                            "technique": "inline",
                            "safety": "safe"
                        })
                    elif isinstance(payload_item, dict):
                        # Already formatted payload
                        converted_payloads.append(payload_item)
                
                # Bind inline payloads to parameters
                bound_payloads = self._bind_to_parameters(converted_payloads, endpoint, {})
                
                self.logger.info(
                    "Inline payloads bound from test_cases array",
                    test_case=test_case.get("_source_file"),
                    total_inline=len(all_inline_payloads),
                    total_bound=len(bound_payloads)
                )
                
                return bound_payloads[:max_payloads]
        
        # Check for direct inline payloads (less common)
        inline_payloads = test_case.get("payloads", [])
        
        if inline_payloads:
            # Convert inline payloads to standard format
            converted_payloads = []
            for payload_item in inline_payloads:
                if isinstance(payload_item, str):
                    # Simple string payload
                    converted_payloads.append({
                        "payload": payload_item,
                        "technique": "inline",
                        "safety": "safe"
                    })
                elif isinstance(payload_item, dict):
                    # Already formatted payload
                    converted_payloads.append(payload_item)
            
            # Bind inline payloads to parameters
            bound_payloads = self._bind_to_parameters(converted_payloads, endpoint, {})
            
            self.logger.info(
                "Inline payloads bound",
                test_case=test_case.get("_source_file"),
                total_inline=len(inline_payloads),
                total_bound=len(bound_payloads)
            )
            
            return bound_payloads[:max_payloads]
        
        # Fallback to external payload references (advanced cases)
        payload_config = test_case.get("payload_config", {})
        payload_type = payload_config.get("type")
        
        if not payload_type:
            self.logger.warning("No payload type specified", test_case=test_case.get("_source_file"))
            return []
        
        # Get payloads for this type
        payloads = self._get_payloads_by_type(payload_type)
        
        # Filter payloads based on context
        filtered_payloads = self._filter_payloads(payloads, endpoint, payload_config)
        
        # Limit number of payloads
        if len(filtered_payloads) > max_payloads:
            # Prioritize diverse payloads
            filtered_payloads = self._select_diverse_payloads(filtered_payloads, max_payloads)
        
        # Bind to injectable parameters
        bound_payloads = self._bind_to_parameters(filtered_payloads, endpoint, payload_config)
        
        self.logger.info(
            "Payloads bound",
            test_case=test_case.get("_source_file"),
            total_bound=len(bound_payloads)
        )
        
        return bound_payloads
    
    def _get_payloads_by_type(self, payload_type: str) -> List[Dict[str, Any]]:
        """Get payloads by type"""
        # Map payload types to cache keys
        type_mapping = {
            "sql_injection": "injection/sql-injection",
            "nosql_injection": "injection/nosql-injection",
            "xss": "injection/xss",
            "xxe": "injection/xxe",
            "ssrf": "ssrf/ssrf-payloads",
            "path_traversal": "file-inclusion/path-traversal",
            "auth_bypass": "auth/auth-bypass",
            "deserialization": "deserialization/insecure-deserialization",
            "cors": "misc/cors-csrf"
        }
        
        cache_key = type_mapping.get(payload_type, payload_type)
        
        # Try direct match first
        if cache_key in self.payloads_cache:
            return self.payloads_cache[cache_key]
        
        # Try partial match
        for key, payloads in self.payloads_cache.items():
            if payload_type in key:
                return payloads
        
        self.logger.warning("No payloads found for type", payload_type=payload_type)
        return []
    
    def _filter_payloads(
        self,
        payloads: List[Dict[str, Any]],
        endpoint: Dict[str, Any],
        payload_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter payloads based on context and safety"""
        filtered = []
        
        for payload in payloads:
            # Check safety level
            if not self._is_safe_payload(payload):
                continue
            
            # Check context requirements
            if payload_config.get("requires_specific_context"):
                if not self._matches_context(payload, endpoint):
                    continue
            
            filtered.append(payload)
        
        return filtered
    
    def _is_safe_payload(self, payload: Dict[str, Any]) -> bool:
        """Check if payload is safe for testing"""
        # Check destructive flag
        if payload.get("destructive", False):
            return False
        
        # Check safety metadata
        safety_level = payload.get("safety", "safe")
        return safety_level in ["safe", "medium"]
    
    def _matches_context(
        self,
        payload: Dict[str, Any],
        endpoint: Dict[str, Any]
    ) -> bool:
        """Check if payload matches endpoint context"""
        # Check technology match
        payload_tech = payload.get("technology")
        if payload_tech:
            endpoint_tech = endpoint.get("metadata", {}).get("technology")
            if endpoint_tech != "unknown" and endpoint_tech != payload_tech:
                return False
        
        return True
    
    def _select_diverse_payloads(
        self,
        payloads: List[Dict[str, Any]],
        max_count: int
    ) -> List[Dict[str, Any]]:
        """Select diverse payloads to maximize coverage"""
        # Group by technique/category
        grouped = {}
        for payload in payloads:
            technique = payload.get("technique", "default")
            if technique not in grouped:
                grouped[technique] = []
            grouped[technique].append(payload)
        
        # Select evenly from each group
        selected = []
        per_group = max(1, max_count // len(grouped))
        
        for group_payloads in grouped.values():
            selected.extend(group_payloads[:per_group])
        
        # Fill remaining slots with high-priority payloads
        if len(selected) < max_count:
            remaining = [p for p in payloads if p not in selected]
            # Prioritize by severity
            remaining.sort(key=lambda x: x.get("severity", "medium"), reverse=True)
            selected.extend(remaining[:max_count - len(selected)])
        
        return selected[:max_count]
    
    def _bind_to_parameters(
        self,
        payloads: List[Dict[str, Any]],
        endpoint: Dict[str, Any],
        payload_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Bind payloads to injectable parameters"""
        bound_payloads = []
        
        # Get injectable parameters
        parameters = endpoint.get("parameters", {})
        injectable_params = [
            name for name, param in parameters.items()
            if param.get("injectable", False)
        ]
        
        if not injectable_params:
            # If no injectable params, test will inject in body or headers
            for payload in payloads:
                bound_payloads.append({
                    "payload": payload.get("payload", ""),
                    "metadata": payload,
                    "injection_point": "body",
                    "parameter": None
                })
            return bound_payloads
        
        # Bind to each injectable parameter
        target_params = payload_config.get("target_parameters", injectable_params)
        
        for param_name in target_params:
            if param_name not in parameters:
                continue
            
            for payload in payloads:
                bound_payloads.append({
                    "payload": payload.get("payload", ""),
                    "metadata": payload,
                    "injection_point": "parameter",
                    "parameter": param_name,
                    "parameter_type": parameters[param_name].get("type"),
                    "original_value": parameters[param_name].get("value")
                })
        
        return bound_payloads


# Singleton instance
payload_binder = PayloadBinder(knowledge_base_path=settings.KNOWLEDGE_BASE_PATH)
