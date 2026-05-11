"""
Rule Engine - Component 5: Safety Enforcer
Blocks destructive payloads in production environments
"""
import structlog
from typing import Dict, List, Any, Optional
import re

logger = structlog.get_logger()


class SafetyEnforcer:
    """
    Enforces safety constraints on payloads to prevent destructive testing.
    This is a critical security component.
    
    Input: Bound payloads
    Output: Filtered safe payloads
    """
    
    # Destructive patterns that should NEVER be executed
    DESTRUCTIVE_PATTERNS = [
        # SQL destructive operations
        r'DROP\s+TABLE',
        r'DROP\s+DATABASE',
        r'DELETE\s+FROM.*WHERE\s+1\s*=\s*1',
        r'TRUNCATE\s+TABLE',
        r'UPDATE.*SET.*WHERE\s+1\s*=\s*1',
        
        # Command injection destructive
        r'rm\s+-rf',
        r'del\s+/f\s+/q',
        r'format\s+[a-z]:',
        r'shutdown',
        r'reboot',
        
        # File operations
        r'unlink',
        r'rmdir',
        
        # System commands
        r'exec\s*\(',
        r'system\s*\(',
        r'eval\s*\(',
        
        # Network operations
        r'nc\s+-l',  # Netcat listener
        r'ncat\s+-l',
    ]
    
    # Dangerous functions/keywords
    DANGEROUS_KEYWORDS = [
        "DROP",
        "DELETE",
        "TRUNCATE",
        "shutdown",
        "format",
        "rm -rf",
        "exec(",
        "eval(",
        "__import__",
    ]
    
    def __init__(self, enable_enforcer: bool = True):
        self.enable_enforcer = enable_enforcer
        self.logger = logger.bind(component="SafetyEnforcer")
        
        # Compile patterns for performance
        self.destructive_regexes = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.DESTRUCTIVE_PATTERNS
        ]
    
    def enforce(self, bound_payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enforce safety on bound payloads
        
        Args:
            bound_payloads: List of payloads bound to parameters
            
        Returns:
            Filtered list of safe payloads
        """
        if not self.enable_enforcer:
            self.logger.warning("Safety enforcer is DISABLED - testing may be destructive!")
            return bound_payloads
        
        safe_payloads = []
        blocked_count = 0
        
        for payload_data in bound_payloads:
            payload = payload_data.get("payload", "")
            
            if self._is_safe(payload, payload_data):
                safe_payloads.append(payload_data)
            else:
                blocked_count += 1
                self.logger.warning(
                    "Blocked destructive payload",
                    payload=payload[:100],  # Log first 100 chars
                    reason="Matched destructive pattern"
                )
        
        self.logger.info(
            "Safety enforcement complete",
            total_payloads=len(bound_payloads),
            safe_payloads=len(safe_payloads),
            blocked=blocked_count
        )
        
        return safe_payloads
    
    def _is_safe(self, payload: str, payload_data: Dict[str, Any]) -> bool:
        """
        Determine if a payload is safe to execute
        
        Safety checks:
        1. Not marked as destructive in metadata
        2. Doesn't match destructive patterns
        3. Doesn't contain dangerous keywords
        4. Meets length constraints
        """
        # Check metadata
        metadata = payload_data.get("metadata", {})
        if metadata.get("destructive", False):
            return False
        
        if metadata.get("safety") == "destructive":
            return False
        
        # Check against destructive patterns
        for regex in self.destructive_regexes:
            if regex.search(payload):
                return False
        
        # Check dangerous keywords
        payload_upper = payload.upper()
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword.upper() in payload_upper:
                # Some keywords are OK in specific contexts
                if not self._is_keyword_safe_in_context(keyword, payload, payload_data):
                    return False
        
        # Length check (prevent DOS through massive payloads)
        if len(payload) > 10000:  # 10KB max
            self.logger.warning("Payload too long", length=len(payload))
            return False
        
        return True
    
    def _is_keyword_safe_in_context(
        self,
        keyword: str,
        payload: str,
        payload_data: Dict[str, Any]
    ) -> bool:
        """
        Check if a dangerous keyword is safe in this specific context
        
        For example, "DROP" might be acceptable in an XSS payload like:
        "DROP-DOWN MENU" but not in SQL injection context
        """
        metadata = payload_data.get("metadata", {})
        payload_type = metadata.get("type", "")
        
        # SQL keywords should only appear in SQL payloads as detection tests
        sql_keywords = ["DROP", "DELETE", "TRUNCATE"]
        if keyword.upper() in sql_keywords:
            # Allow in SQL testing context, but only for detection, not execution
            if "sql" in payload_type.lower():
                # Must be a detection payload, not an execution payload
                return metadata.get("test_type") == "detection"
            # Not a SQL context, so keyword is suspicious
            return False
        
        return True
    
    def validate_test_config(self, test_config: Dict[str, Any]) -> bool:
        """
        Validate test configuration for safety
        
        Args:
            test_config: Test configuration to validate
            
        Returns:
            True if configuration is safe, False otherwise
        """
        # Check for dangerous test types
        dangerous_tests = test_config.get("dangerous_tests", [])
        if dangerous_tests:
            self.logger.error("Configuration includes dangerous tests", tests=dangerous_tests)
            return False
        
        # Validate rate limits
        rate_limit = test_config.get("rate_limit", 10)
        if rate_limit > 100:  # Max 100 requests per second
            self.logger.error("Rate limit too high", rate_limit=rate_limit)
            return False
        
        # Validate timeout
        timeout = test_config.get("timeout", 30)
        if timeout > 300:  # Max 5 minutes
            self.logger.error("Timeout too long", timeout=timeout)
            return False
        
        return True


# Singleton instance
safety_enforcer = SafetyEnforcer()
