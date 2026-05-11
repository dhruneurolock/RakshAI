"""
Rule Engine - Component 2: OWASP Mapper
Maps endpoints to applicable OWASP Top 10:2025 categories
"""
import yaml
import structlog
from typing import Dict, List, Any, Set
from pathlib import Path

logger = structlog.get_logger()


class OWASPMapper:
    """
    Maps normalized endpoints to applicable OWASP Top 10:2025 categories
    using deterministic rules (NO ML).
    
    Input: Normalized endpoint context
    Output: List of applicable OWASP categories (A01-A10)
    """
    
    OWASP_CATEGORIES = {
        "A01": "Broken Access Control",
        "A02": "Security Misconfiguration",
        "A03": "Software Supply Chain",
        "A04": "Cryptographic Failures",
        "A05": "Injection",
        "A06": "Insecure Design",
        "A07": "Authentication Failures",
        "A08": "Software & Data Integrity",
        "A09": "Security Logging & Alerting Failures",
        "A10": "Server-Side Request Forgery (SSRF)"
    }
    
    def __init__(self, knowledge_base_path: str = "./knowledge-base"):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.logger = logger.bind(component="OWASPMapper")
        self.mapping_rules = self._load_mapping_rules()
    
    def _load_mapping_rules(self) -> Dict[str, Any]:
        """Load OWASP mapping rules from YAML"""
        owasp_file = self.knowledge_base_path / "metadata" / "owasp_top10_2025.yaml"
        
        if owasp_file.exists():
            with open(owasp_file, 'r') as f:
                return yaml.safe_load(f) or {}
        
        # Fallback to default rules
        return self._get_default_mapping_rules()
    
    def map_endpoint(self, normalized_endpoint: Dict[str, Any]) -> List[str]:
        """
        Map a single endpoint to applicable OWASP categories
        
        Args:
            normalized_endpoint: Normalized endpoint from ContextNormalizer
            
        Returns:
            List of applicable OWASP categories (e.g., ["A01", "A05"])
        """
        categories: Set[str] = set()
        
        # Always test for injection vulnerabilities
        categories.add("A05")  # Injection
        
        # Check for access control issues
        if self._requires_access_control_testing(normalized_endpoint):
            categories.add("A01")  # Broken Access Control
        
        # Check for authentication issues
        if self._requires_auth_testing(normalized_endpoint):
            categories.add("A07")  # Authentication Failures
        
        # Check for SSRF potential
        if self._has_ssrf_potential(normalized_endpoint):
            categories.add("A10")  # SSRF
        
        # Check for crypto issues
        if self._requires_crypto_testing(normalized_endpoint):
            categories.add("A04")  # Cryptographic Failures
        
        # Always test for security misconfiguration
        categories.add("A02")  # Security Misconfiguration
        
        # Check for insecure design patterns
        if self._has_insecure_design_indicators(normalized_endpoint):
            categories.add("A06")  # Insecure Design
        
        # Check for integrity issues
        if self._requires_integrity_testing(normalized_endpoint):
            categories.add("A08")  # Software & Data Integrity
        
        # Check for logging failures
        if self._requires_logging_testing(normalized_endpoint):
            categories.add("A09")  # Logging & Alerting Failures
        
        # Supply chain testing (less endpoint-specific, more application-wide)
        if self._has_supply_chain_indicators(normalized_endpoint):
            categories.add("A03")  # Software Supply Chain
        
        sorted_categories = sorted(list(categories))
        self.logger.info(
            "Endpoint mapped to OWASP categories",
            url=normalized_endpoint.get("url"),
            categories=sorted_categories
        )
        
        return sorted_categories
    
    def _requires_access_control_testing(self, endpoint: Dict[str, Any]) -> bool:
        """Determine if endpoint requires access control testing"""
        url = endpoint.get("url", "").lower()
        parameters = endpoint.get("parameters", {})
        metadata = endpoint.get("metadata", {})
        
        # Check for ID parameters (IDOR potential)
        has_id_param = any(
            param.get("type") == "id" 
            for param in parameters.values()
        )
        
        # Check for admin/user paths
        admin_patterns = ["/admin", "/user", "/account", "/profile", "/dashboard"]
        has_admin_path = any(pattern in url for pattern in admin_patterns)
        
        # Check if requires authentication
        has_auth = metadata.get("has_auth", False)
        
        return has_id_param or has_admin_path or has_auth
    
    def _requires_auth_testing(self, endpoint: Dict[str, Any]) -> bool:
        """Determine if endpoint requires authentication testing"""
        url = endpoint.get("url", "").lower()
        metadata = endpoint.get("metadata", {})
        
        # Login/auth endpoints
        auth_patterns = ["/login", "/signin", "/auth", "/register", "/signup", "/logout"]
        is_auth_endpoint = any(pattern in url for pattern in auth_patterns)
        
        # Endpoints with authentication
        has_auth = metadata.get("has_auth", False)
        
        return is_auth_endpoint or has_auth
    
    def _has_ssrf_potential(self, endpoint: Dict[str, Any]) -> bool:
        """Check if endpoint has SSRF potential"""
        parameters = endpoint.get("parameters", {})
        url = endpoint.get("url", "").lower()
        
        # Check for URL parameters
        has_url_param = any(
            param.get("type") == "url"
            for param in parameters.values()
        )
        
        # Check for file/path parameters
        has_file_param = any(
            param.get("type") == "file"
            for param in parameters.values()
        )
        
        # Check for webhook/callback patterns
        ssrf_patterns = ["/webhook", "/callback", "/fetch", "/proxy", "/download", "/upload"]
        has_ssrf_pattern = any(pattern in url for pattern in ssrf_patterns)
        
        return has_url_param or has_file_param or has_ssrf_pattern
    
    def _requires_crypto_testing(self, endpoint: Dict[str, Any]) -> bool:
        """Determine if endpoint requires cryptographic testing"""
        parameters = endpoint.get("parameters", {})
        
        # Check for password/token parameters
        has_sensitive_params = any(
            param.get("type") in ["password", "token"]
            for param in parameters.values()
        )
        
        return has_sensitive_params
    
    def _has_insecure_design_indicators(self, endpoint: Dict[str, Any]) -> bool:
        """Check for insecure design patterns"""
        url = endpoint.get("url", "").lower()
        method = endpoint.get("method", "GET")
        
        # Check for state-changing GET requests (insecure design)
        state_change_patterns = ["/delete", "/update", "/create", "/modify"]
        is_state_changing_get = (
            method == "GET" and 
            any(pattern in url for pattern in state_change_patterns)
        )
        
        return is_state_changing_get
    
    def _requires_integrity_testing(self, endpoint: Dict[str, Any]) -> bool:
        """Determine if endpoint requires integrity testing"""
        url = endpoint.get("url", "").lower()
        
        # Check for update/upload endpoints
        integrity_patterns = ["/update", "/upload", "/install", "/deploy"]
        return any(pattern in url for pattern in integrity_patterns)
    
    def _requires_logging_testing(self, endpoint: Dict[str, Any]) -> bool:
        """Determine if endpoint requires logging testing"""
        metadata = endpoint.get("metadata", {})
        method = endpoint.get("method", "GET")
        
        # Authentication endpoints should have logging
        has_auth = metadata.get("has_auth", False)
        
        # State-changing operations should be logged
        is_state_changing = method in ["POST", "PUT", "DELETE", "PATCH"]
        
        return has_auth or is_state_changing
    
    def _has_supply_chain_indicators(self, endpoint: Dict[str, Any]) -> bool:
        """Check for supply chain testing indicators"""
        # This is typically application-wide, not endpoint-specific
        # But we can check for dependency/package-related endpoints
        url = endpoint.get("url", "").lower()
        supply_chain_patterns = ["/npm", "/package", "/dependency", "/plugin"]
        return any(pattern in url for pattern in supply_chain_patterns)
    
    def _get_default_mapping_rules(self) -> Dict[str, Any]:
        """Default OWASP mapping rules if YAML not found"""
        return {
            "categories": self.OWASP_CATEGORIES,
            "rules": {
                "A01": {"patterns": ["id=", "/user/", "/admin/"], "requires_auth": True},
                "A02": {"always_test": True},
                "A05": {"always_test": True},
                "A07": {"patterns": ["/auth", "/login", "/signin"]},
                "A10": {"parameter_types": ["url", "file"]}
            }
        }


# Singleton instance
owasp_mapper = OWASPMapper()
