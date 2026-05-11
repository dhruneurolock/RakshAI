"""
Rule Engine - Component 1: Context Normalizer
Transforms discovery output to standardized format for rule processing
"""
import yaml
import structlog
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = structlog.get_logger()


class ContextNormalizer:
    """
    Normalizes discovered endpoints and context into a standardized format
    that can be consumed by the rule engine.
    
    Input: Raw discovery data (URLs, forms, APIs, etc.)
    Output: Normalized context with standardized fields
    """
    
    def __init__(self):
        self.logger = logger.bind(component="ContextNormalizer")
    
    def normalize_endpoint(self, raw_endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single endpoint to standard format
        
        Args:
            raw_endpoint: Raw endpoint data from discovery agent
            
        Returns:
            Normalized endpoint context
        """
        normalized = {
            "url": self._normalize_url(raw_endpoint.get("url", "")),
            "method": self._normalize_method(raw_endpoint.get("method", "GET")),
            "parameters": self._normalize_parameters(raw_endpoint.get("parameters", {})),
            "headers": self._normalize_headers(raw_endpoint.get("headers", {})),
            "cookies": self._normalize_cookies(raw_endpoint.get("cookies", {})),
            "body": self._normalize_body(raw_endpoint.get("body")),
            "response": self._normalize_response(raw_endpoint.get("response", {})),
            "metadata": self._extract_metadata(raw_endpoint)
        }
        
        self.logger.info("Endpoint normalized", url=normalized["url"], method=normalized["method"])
        return normalized
    
    def normalize_batch(self, raw_endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize multiple endpoints"""
        return [self.normalize_endpoint(ep) for ep in raw_endpoints]
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL format"""
        url = url.strip()
        # Remove trailing slashes for consistency
        if url.endswith("/") and len(url) > 1:
            url = url[:-1]
        return url
    
    def _normalize_method(self, method: str) -> str:
        """Normalize HTTP method"""
        return method.upper()
    
    def _normalize_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize parameters (query params, form fields, etc.)
        Extracts type information for better test case selection
        """
        normalized_params = {}
        
        for name, value in params.items():
            param_type = self._infer_parameter_type(name, value)
            normalized_params[name] = {
                "value": value,
                "type": param_type,
                "name": name,
                "injectable": self._is_injectable_parameter(name, param_type)
            }
        
        return normalized_params
    
    def _normalize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Normalize HTTP headers"""
        # Convert to lowercase keys for consistency
        return {k.lower(): v for k, v in headers.items()}
    
    def _normalize_cookies(self, cookies: Dict[str, str]) -> Dict[str, Any]:
        """Normalize cookies with security attributes"""
        normalized_cookies = {}
        
        for name, value in cookies.items():
            normalized_cookies[name] = {
                "value": value,
                "name": name,
                "sensitive": self._is_sensitive_cookie(name)
            }
        
        return normalized_cookies
    
    def _normalize_body(self, body: Optional[Any]) -> Optional[Dict[str, Any]]:
        """Normalize request body"""
        if not body:
            return None
        
        if isinstance(body, str):
            return {"raw": body, "type": "text"}
        elif isinstance(body, dict):
            return {"data": body, "type": "json"}
        
        return {"raw": str(body), "type": "unknown"}
    
    def _normalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize response data"""
        return {
            "status_code": response.get("status_code", 200),
            "headers": self._normalize_headers(response.get("headers", {})),
            "body": response.get("body", ""),
            "content_type": response.get("content_type", "text/html"),
            "size": len(response.get("body", "")),
            "time_ms": response.get("response_time", 0)
        }
    
    def _extract_metadata(self, raw_endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata for better categorization"""
        url = raw_endpoint.get("url", "")
        
        return {
            "has_auth": self._has_authentication(raw_endpoint),
            "is_api": self._is_api_endpoint(url, raw_endpoint),
            "is_form": self._has_form_fields(raw_endpoint),
            "technology": self._detect_technology(raw_endpoint),
            "endpoint_type": self._classify_endpoint_type(raw_endpoint)
        }
    
    def _infer_parameter_type(self, name: str, value: Any) -> str:
        """Infer parameter type from name and value"""
        name_lower = name.lower()
        
        # Check common patterns
        if "id" in name_lower:
            return "id"
        elif "email" in name_lower or "mail" in name_lower:
            return "email"
        elif "user" in name_lower or "username" in name_lower:
            return "username"
        elif "pass" in name_lower or "pwd" in name_lower:
            return "password"
        elif "token" in name_lower:
            return "token"
        elif "url" in name_lower or "link" in name_lower:
            return "url"
        elif "file" in name_lower or "path" in name_lower:
            return "file"
        elif "search" in name_lower or "query" in name_lower or "q" == name_lower:
            return "search"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, bool):
            return "boolean"
        
        return "string"
    
    def _is_injectable_parameter(self, name: str, param_type: str) -> bool:
        """Determine if parameter is injectable (suitable for attack payloads)"""
        # IDs, search fields, and URLs are commonly injectable
        injectable_types = {"id", "search", "url", "string", "file"}
        return param_type in injectable_types
    
    def _is_sensitive_cookie(self, name: str) -> bool:
        """Check if cookie contains sensitive data"""
        sensitive_patterns = ["session", "token", "auth", "jwt", "csrf"]
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in sensitive_patterns)
    
    def _has_authentication(self, endpoint: Dict[str, Any]) -> bool:
        """Detect if endpoint requires authentication"""
        headers = endpoint.get("headers", {})
        cookies = endpoint.get("cookies", {})
        
        # Check for auth headers
        auth_headers = ["authorization", "x-auth-token", "x-api-key"]
        has_auth_header = any(h.lower() in headers for h in auth_headers)
        
        # Check for session cookies
        has_session_cookie = any(self._is_sensitive_cookie(c) for c in cookies.keys())
        
        return has_auth_header or has_session_cookie
    
    def _is_api_endpoint(self, url: str, endpoint: Dict[str, Any]) -> bool:
        """Detect if endpoint is an API"""
        # Check URL patterns
        api_patterns = ["/api/", "/v1/", "/v2/", "/rest/", "/graphql"]
        is_api_url = any(pattern in url.lower() for pattern in api_patterns)
        
        # Check content type
        response = endpoint.get("response", {})
        content_type = response.get("content_type", "")
        is_json = "json" in content_type.lower()
        
        return is_api_url or is_json
    
    def _has_form_fields(self, endpoint: Dict[str, Any]) -> bool:
        """Check if endpoint has form fields"""
        parameters = endpoint.get("parameters", {})
        method = endpoint.get("method", "GET")
        
        return method in ["POST", "PUT"] and len(parameters) > 0
    
    def _detect_technology(self, endpoint: Dict[str, Any]) -> str:
        """Detect technology stack from response headers"""
        response = endpoint.get("response", {})
        headers = response.get("headers", {})
        
        # Check server header
        server = headers.get("server", "").lower()
        if "nginx" in server:
            return "nginx"
        elif "apache" in server:
            return "apache"
        elif "iis" in server:
            return "iis"
        
        # Check X-Powered-By
        powered_by = headers.get("x-powered-by", "").lower()
        if "php" in powered_by:
            return "php"
        elif "asp.net" in powered_by:
            return "aspnet"
        elif "express" in powered_by:
            return "nodejs"
        
        return "unknown"
    
    def _classify_endpoint_type(self, endpoint: Dict[str, Any]) -> str:
        """Classify endpoint type"""
        if self._is_api_endpoint(endpoint.get("url", ""), endpoint):
            return "api"
        elif self._has_form_fields(endpoint):
            return "form"
        elif endpoint.get("method") == "GET":
            return "page"
        else:
            return "other"


# Singleton instance
context_normalizer = ContextNormalizer()
