"""
ValidatorEngine — Loads and applies detection patterns from knowledge-base/validators/*.yaml.

Replaces hardcoded error strings and detection patterns with KB-driven lookups.
Loaded files:
  - validators/sql_errors.yaml
  - validators/xss_reflections.yaml
  - validators/auth_indicators.yaml
  - validators/data-leak.yaml
  - validators/error-patterns.yaml
  - validators/reflection.yaml
  - validators/status-codes.yaml
"""
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

KB_ROOT = Path(__file__).resolve().parents[3] / "knowledge-base"


def _load_yaml(rel: str) -> dict:
    try:
        with open(KB_ROOT / rel, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


class ValidatorEngine:
    """KB-driven response validation engine.

    Loads detection patterns from knowledge-base/validators/ YAML files
    and exposes methods to validate HTTP responses against them.
    """

    def __init__(self):
        self._loaded = False
        self._sql_errors: Dict[str, Any] = {}
        self._xss_reflections: Dict[str, Any] = {}
        self._auth_indicators: Dict[str, Any] = {}
        self._data_leak: Dict[str, Any] = {}
        self._error_patterns: Dict[str, Any] = {}
        self._reflection: Dict[str, Any] = {}
        self._status_codes: Dict[str, Any] = {}
        # Flattened pattern caches (built on first load)
        self._sql_error_patterns: List[Dict[str, Any]] = []
        self._xss_reflection_patterns: List[Dict[str, Any]] = []
        self._auth_success_patterns: List[Dict[str, Any]] = []
        self._auth_failure_patterns: List[Dict[str, Any]] = []
        self._fp_filters: List[Dict[str, Any]] = []

    def load(self) -> None:
        """Load all validator YAML files. Safe to call multiple times."""
        if self._loaded:
            return
        if yaml is None:
            logger.warning("PyYAML not installed — validator engine disabled")
            self._loaded = True
            return

        logger.info("ValidatorEngine: loading from knowledge-base/validators/")
        self._sql_errors = _load_yaml("validators/sql_errors.yaml")
        self._xss_reflections = _load_yaml("validators/xss_reflections.yaml")
        self._auth_indicators = _load_yaml("validators/auth_indicators.yaml")
        self._data_leak = _load_yaml("validators/data-leak.yaml")
        self._error_patterns = _load_yaml("validators/error-patterns.yaml")
        self._reflection = _load_yaml("validators/reflection.yaml")
        self._status_codes = _load_yaml("validators/status-codes.yaml")

        self._build_sql_error_cache()
        self._build_xss_cache()
        self._build_auth_cache()

        logger.info(
            f"ValidatorEngine: loaded {len(self._sql_error_patterns)} SQL patterns, "
            f"{len(self._xss_reflection_patterns)} XSS patterns, "
            f"{len(self._auth_success_patterns)} auth patterns"
        )
        self._loaded = True

    # ------------------------------------------------------------------
    # SQL Injection Validation
    # ------------------------------------------------------------------

    def check_sql_errors(self, response_body: str) -> List[Dict[str, Any]]:
        """Check response body against all KB SQL error patterns.

        Returns list of matches with: pattern, database, confidence, severity.
        """
        if not response_body:
            return []
        matches = []
        body_lower = response_body.lower()
        for entry in self._sql_error_patterns:
            pattern = entry["pattern"]
            try:
                if entry.get("is_regex"):
                    if re.search(pattern, response_body, re.IGNORECASE):
                        matches.append(entry)
                else:
                    if pattern.lower() in body_lower:
                        matches.append(entry)
            except re.error:
                if pattern.lower() in body_lower:
                    matches.append(entry)

        # Apply false-positive filters
        for fp in self._fp_filters:
            fp_pattern = fp.get("pattern", "")
            if fp_pattern.lower() in body_lower:
                penalty = fp.get("confidence_penalty", -0.3)
                for m in matches:
                    m = dict(m)  # copy
                    m["confidence"] = max(0, m.get("confidence", 0.5) + penalty)
        return matches

    def get_sql_error_patterns_flat(self) -> List[str]:
        """Get flattened list of SQL error pattern strings (for backward compat)."""
        return [e["pattern"] for e in self._sql_error_patterns if not e.get("is_regex")]

    # ------------------------------------------------------------------
    # XSS Reflection Validation
    # ------------------------------------------------------------------

    def check_xss_reflection(self, response_body: str, payload: str,
                              content_type: str = "", csp_header: str = "") -> Dict[str, Any]:
        """Check if an XSS payload is reflected in the response.

        Returns: {reflected, encoded, confidence, context, details}
        """
        result = {
            "reflected": False,
            "encoded": "none",
            "confidence": 0.0,
            "context": "unknown",
            "details": [],
        }
        if not response_body or not payload:
            return result

        # Check unencoded reflection
        if payload in response_body:
            result["reflected"] = True
            result["encoded"] = "none"
            result["confidence"] = 0.85

        # Check HTML-encoded
        import html
        encoded_payload = html.escape(payload)
        if encoded_payload in response_body and not result["reflected"]:
            result["reflected"] = True
            result["encoded"] = "html_entities"
            result["confidence"] = 0.0  # Safe

        if not result["reflected"]:
            return result

        # Context detection from KB
        if result["encoded"] == "none":
            # Check unsafe contexts
            contexts = self._xss_reflections.get("context_validation", {})
            unsafe = contexts.get("html_body_context", {}).get("unsafe_contexts", [])
            for ctx in unsafe:
                ctx_pattern = ctx.get("pattern", "")
                if ctx_pattern:
                    try:
                        if re.search(ctx_pattern, response_body, re.IGNORECASE | re.DOTALL):
                            result["context"] = ctx.get("description", "unsafe")
                            result["confidence"] = ctx.get("confidence", 0.90)
                            break
                    except re.error:
                        pass

        # Content-Type adjustment from KB
        ct_validation = self._xss_reflections.get("response_headers_validation", {})
        ct_check = ct_validation.get("content_type_check", {})
        if content_type:
            for safe_ct in ct_check.get("safe", []):
                if safe_ct.get("header", "").split(": ", 1)[-1].lower() in content_type.lower():
                    result["confidence"] *= safe_ct.get("confidence_multiplier", 0.2)

        # CSP adjustment from KB
        sec_headers = ct_validation.get("security_headers", {})
        csp_rules = sec_headers.get("csp_check", [])
        if csp_header:
            for rule in csp_rules:
                if rule.get("header") and rule["header"].split(": ", 1)[-1].lower() in csp_header.lower():
                    penalty = rule.get("confidence_penalty", 0)
                    result["confidence"] = max(0, result["confidence"] + penalty)
        elif not csp_header:
            # No CSP present — bonus from KB
            for rule in csp_rules:
                if rule.get("header_missing") == "Content-Security-Policy":
                    result["confidence"] = min(1.0, result["confidence"] + rule.get("confidence_bonus", 0.2))

        return result

    # ------------------------------------------------------------------
    # Auth Bypass Validation
    # ------------------------------------------------------------------

    def check_auth_bypass(self, response_body: str, status_code: int,
                           headers: Dict[str, str]) -> Dict[str, Any]:
        """Validate if an auth bypass occurred using KB auth_indicators.yaml.

        Returns: {bypassed, confidence, indicators_matched, details}
        """
        result = {
            "bypassed": False,
            "confidence": 0.0,
            "indicators_matched": [],
            "details": [],
        }

        total_confidence = 0.0
        count = 0

        # Check success response patterns from KB
        for pattern_entry in self._auth_success_patterns:
            pattern = pattern_entry.get("pattern", "")
            if not pattern:
                continue
            try:
                if re.search(pattern, response_body, re.IGNORECASE):
                    conf = pattern_entry.get("confidence", 0.7)
                    total_confidence = max(total_confidence, conf)
                    count += 1
                    result["indicators_matched"].append({
                        "type": "response_pattern",
                        "pattern": pattern,
                        "confidence": conf,
                        "description": pattern_entry.get("description", ""),
                    })
            except re.error:
                pass

        # Check status codes from KB
        status_entries = self._auth_indicators.get("successful_auth_indicators", {}).get("http_status_codes", [])
        for entry in status_entries:
            if entry.get("status") == status_code:
                conf = entry.get("confidence", 0.7)
                total_confidence = max(total_confidence, conf)
                count += 1
                result["indicators_matched"].append({
                    "type": "status_code",
                    "status": status_code,
                    "confidence": conf,
                })
                # Check redirect location
                location = headers.get("location", "")
                loc_pattern = entry.get("location", "")
                if location and loc_pattern:
                    try:
                        if re.search(loc_pattern, location, re.IGNORECASE):
                            total_confidence = max(total_confidence, conf + 0.1)
                    except re.error:
                        pass

        # Check session indicators (cookies, JWT)
        set_cookie = headers.get("set-cookie", "")
        session_indicators = self._auth_indicators.get("session_indicators", {})
        for cookie_entry in session_indicators.get("cookie_patterns", []):
            cookie_pattern = cookie_entry.get("pattern", "")
            if cookie_pattern:
                try:
                    if re.search(cookie_pattern, set_cookie, re.IGNORECASE):
                        conf = cookie_entry.get("confidence", 0.8)
                        total_confidence = max(total_confidence, conf)
                        count += 1
                        result["indicators_matched"].append({
                            "type": "session_cookie",
                            "name": cookie_entry.get("name", ""),
                            "confidence": conf,
                        })
                except re.error:
                    pass

        # Check for false positive patterns
        fp_patterns = self._auth_indicators.get("false_positive_detection", {}).get("misleading_indicators", [])
        for fp in fp_patterns:
            fp_pattern = fp.get("pattern", "")
            if fp_pattern and fp_pattern.lower() in response_body.lower():
                penalty = fp.get("confidence_penalty", -0.5)
                total_confidence = max(0, total_confidence + penalty)
                result["details"].append(f"FP filter: {fp.get('description', fp_pattern)}")

        result["confidence"] = min(1.0, total_confidence)
        result["bypassed"] = count >= 2 and total_confidence >= 0.7
        return result

    # ------------------------------------------------------------------
    # CORS Validation (from payloads/misc/cors-csrf.yaml)
    # ------------------------------------------------------------------

    def get_cors_test_origins(self) -> List[str]:
        """Get CORS test Origin headers from KB."""
        cors_yaml = _load_yaml("payloads/misc/cors-csrf.yaml")
        origins = []
        detection = cors_yaml.get("cors_testing", {}).get("detection", {})
        for h in detection.get("headers", []):
            if h.startswith("Origin:"):
                origins.append(h.split(": ", 1)[1])
        # Add bypass techniques
        bypass = cors_yaml.get("cors_bypass_techniques", {})
        for key in ("subdomain_takeover", "regex_bypass", "pre_domain", "post_domain"):
            entries = bypass.get(key, [])
            if isinstance(entries, list):
                for e in entries:
                    if isinstance(e, str) and e.startswith("Origin:"):
                        origins.append(e.split(": ", 1)[1])
        return origins

    def check_cors_vulnerable(self, response_headers: Dict[str, str], test_origin: str) -> Dict[str, Any]:
        """Check if CORS response indicates vulnerability."""
        acao = response_headers.get("access-control-allow-origin", "")
        acac = response_headers.get("access-control-allow-credentials", "")
        result = {"vulnerable": False, "confidence": 0.0, "issue": ""}

        if acao == "*" and acac.lower() == "true":
            result = {"vulnerable": True, "confidence": 0.95, "issue": "Wildcard origin with credentials"}
        elif acao == test_origin and acac.lower() == "true":
            result = {"vulnerable": True, "confidence": 0.90, "issue": "Reflected origin with credentials"}
        elif acao == "null" and acac.lower() == "true":
            result = {"vulnerable": True, "confidence": 0.85, "issue": "Null origin allowed with credentials"}
        elif acao == test_origin:
            result = {"vulnerable": True, "confidence": 0.70, "issue": "Origin reflected without credential check"}

        return result

    # ------------------------------------------------------------------
    # Data Leak Detection
    # ------------------------------------------------------------------

    def get_data_leak_patterns(self) -> List[Dict[str, Any]]:
        """Get data leak detection patterns from KB."""
        patterns = []
        for section_key, section in self._data_leak.items():
            if not isinstance(section, dict):
                continue
            for sub_key, entries in section.items():
                if isinstance(entries, list):
                    for entry in entries:
                        if isinstance(entry, dict) and "pattern" in entry:
                            patterns.append(entry)
        return patterns

    # ------------------------------------------------------------------
    # Status Code Analysis
    # ------------------------------------------------------------------

    def get_status_code_meaning(self, status_code: int) -> Dict[str, Any]:
        """Look up status code meaning from KB."""
        for section_key, section in self._status_codes.items():
            if not isinstance(section, (dict, list)):
                continue
            if isinstance(section, list):
                for entry in section:
                    if isinstance(entry, dict) and entry.get("code") == status_code:
                        return entry
            elif isinstance(section, dict):
                for sub_key, entries in section.items():
                    if isinstance(entries, list):
                        for entry in entries:
                            if isinstance(entry, dict) and entry.get("code") == status_code:
                                return entry
        return {"code": status_code, "meaning": "Unknown"}

    # ------------------------------------------------------------------
    # Cache Builders (internal)
    # ------------------------------------------------------------------

    def _build_sql_error_cache(self):
        """Flatten all SQL error patterns from nested YAML structure."""
        for db_key in ("mysql_errors", "postgresql_errors", "mssql_errors",
                       "oracle_errors", "sqlite_errors", "mongodb_errors", "generic_sql_patterns"):
            section = self._sql_errors.get(db_key, {})
            db_name = db_key.replace("_errors", "").replace("_patterns", "").upper()
            if isinstance(section, dict):
                for sub_key, entries in section.items():
                    if isinstance(entries, list):
                        for entry in entries:
                            if isinstance(entry, dict) and "pattern" in entry:
                                is_regex = "\\\\" in entry["pattern"] or any(
                                    c in entry["pattern"] for c in "()[]{}+*?|"
                                )
                                self._sql_error_patterns.append({
                                    "pattern": entry["pattern"],
                                    "database": entry.get("database", db_name),
                                    "confidence": entry.get("confidence", 0.7),
                                    "severity": entry.get("severity", "MEDIUM"),
                                    "description": entry.get("description", ""),
                                    "is_regex": is_regex,
                                })
        # Load false-positive filters
        fp_section = self._sql_errors.get("false_positive_filters", {})
        for fp_key, entries in fp_section.items():
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict):
                        self._fp_filters.append(entry)

    def _build_xss_cache(self):
        """Flatten XSS reflection patterns."""
        reflection = self._xss_reflections.get("reflection_patterns", {})
        for category, entries in reflection.items():
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict) and "pattern" in entry:
                        self._xss_reflection_patterns.append(entry)

    def _build_auth_cache(self):
        """Flatten auth indicator patterns."""
        success = self._auth_indicators.get("successful_auth_indicators", {})
        for entry in success.get("response_patterns", []):
            if isinstance(entry, dict):
                self._auth_success_patterns.append(entry)

        failed = self._auth_indicators.get("failed_auth_indicators", {})
        for entry in failed.get("response_patterns", []):
            if isinstance(entry, dict):
                self._auth_failure_patterns.append(entry)


# Singleton
_engine: Optional[ValidatorEngine] = None


def get_validator_engine() -> ValidatorEngine:
    """Get or create the global ValidatorEngine singleton."""
    global _engine
    if _engine is None:
        _engine = ValidatorEngine()
        _engine.load()
    return _engine
