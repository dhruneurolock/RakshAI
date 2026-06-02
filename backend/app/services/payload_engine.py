"""
Payload Engine — Loads test cases and payloads from knowledge-base YAML files.

This module replaces the 2 hardcoded inline payloads with the full knowledge-base
library covering OWASP Top 10 categories:
  - A01: IDOR, Path Traversal, Forced Browsing
  - A02: Security Misconfiguration
  - A05: SQL Injection, XSS, NoSQL Injection, XXE
  - A07: Auth Bypass
  - A10: SSRF

Usage:
    engine = PayloadEngine()
    engine.load()   # reads all YAMLs once
    payloads = engine.get_xss_payloads(limit=20)
    payloads = engine.get_sqli_payloads(limit=15)
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

logger = logging.getLogger(__name__)


class PayloadEngine:
    """Loads and serves payloads/test-cases from knowledge-base YAML files."""

    def __init__(self, knowledge_base_path: Optional[str] = None):
        if knowledge_base_path:
            self._kb_root = Path(knowledge_base_path)
        else:
            # Try multiple possible locations
            candidates = [
                Path(__file__).resolve().parents[3] / "knowledge-base",  # backend/app/services -> project root
                Path(os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge-base")),
                Path("/app/knowledge-base"),
            ]
            self._kb_root = next((p for p in candidates if p.exists()), candidates[0])

        self._test_cases_dir = self._kb_root / "test-cases"
        self._payloads_dir = self._kb_root / "payloads"
        self._metadata_dir = self._kb_root / "metadata"

        # Loaded data caches
        self._loaded = False
        self._xss_payloads: List[str] = []
        self._sqli_payloads: List[str] = []
        self._sqli_test_cases: List[Dict[str, Any]] = []
        self._nosqli_payloads: List[str] = []
        self._xxe_payloads: List[str] = []
        self._ssrf_payloads: List[str] = []
        self._path_traversal_payloads: List[str] = []
        self._auth_bypass_payloads: List[str] = []
        self._idor_test_cases: List[Dict[str, Any]] = []
        self._default_config_checks: List[Dict[str, Any]] = []
        self._sqli_detection_patterns: List[str] = []

        # KB metadata caches (previously unused — now wired)
        self._confidence_scoring: Dict[str, Any] = {}
        self._payload_safety: Dict[str, Any] = {}
        self._test_payload_bindings: Dict[str, Any] = {}
        self._auth_test_cases: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load all YAML files from knowledge-base. Safe to call multiple times."""
        if self._loaded:
            return
        if yaml is None:
            logger.warning("PyYAML not installed — payload engine disabled")
            self._loaded = True
            return
        if not self._kb_root.exists():
            logger.warning(f"Knowledge-base not found at {self._kb_root}")
            self._loaded = True
            return

        logger.info(f"PayloadEngine: loading from {self._kb_root}")
        self._load_xss_payloads()
        self._load_sqli_payloads()
        self._load_nosqli_payloads()
        self._load_xxe_payloads()
        self._load_ssrf_payloads()
        self._load_path_traversal()
        self._load_auth_bypass()
        self._load_idor_tests()
        self._load_default_config_checks()
        # Load previously-unused KB metadata files
        self._load_confidence_scoring()
        self._load_payload_safety()
        self._load_test_payload_bindings()
        self._load_auth_test_cases()

        total = (
            len(self._xss_payloads) + len(self._sqli_payloads)
            + len(self._nosqli_payloads) + len(self._xxe_payloads)
            + len(self._ssrf_payloads) + len(self._path_traversal_payloads)
            + len(self._auth_bypass_payloads)
        )
        logger.info(f"PayloadEngine: loaded {total} payloads across all categories")
        self._loaded = True

    # --- Getters (with optional limit) --------------------------------

    def get_xss_payloads(self, limit: int = 20) -> List[str]:
        self._ensure_loaded()
        return self._xss_payloads[:limit]

    def get_sqli_payloads(self, limit: int = 15) -> List[str]:
        self._ensure_loaded()
        return self._sqli_payloads[:limit]

    def get_sqli_test_cases(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        return self._sqli_test_cases

    def get_nosqli_payloads(self, limit: int = 10) -> List[str]:
        self._ensure_loaded()
        return self._nosqli_payloads[:limit]

    def get_xxe_payloads(self, limit: int = 5) -> List[str]:
        self._ensure_loaded()
        return self._xxe_payloads[:limit]

    def get_ssrf_payloads(self, limit: int = 10) -> List[str]:
        self._ensure_loaded()
        return self._ssrf_payloads[:limit]

    def get_path_traversal_payloads(self, limit: int = 15) -> List[str]:
        self._ensure_loaded()
        return self._path_traversal_payloads[:limit]

    def get_auth_bypass_payloads(self, limit: int = 10) -> List[str]:
        self._ensure_loaded()
        return self._auth_bypass_payloads[:limit]

    def get_idor_test_cases(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        return self._idor_test_cases

    def get_default_config_checks(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        return self._default_config_checks

    def get_sqli_detection_patterns(self) -> List[str]:
        """SQL error signatures to search for in responses (loaded from KB only)."""
        self._ensure_loaded()
        if not self._sqli_detection_patterns:
            logger.warning("No SQL detection patterns loaded from KB — SQL error matching may be limited")
        return self._sqli_detection_patterns

    # ------------------------------------------------------------------
    # Internal loaders
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def _read_yaml(self, path: Path) -> Optional[Dict[str, Any]]:
        """Safely read and parse a YAML file."""
        if not path.exists() or yaml is None:
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load {path}: {e}")
            return None

    def _flatten_strings(self, obj: Any, depth: int = 0) -> List[str]:
        """Recursively extract all string values from a nested YAML structure."""
        if depth > 10:
            return []
        results: List[str] = []
        if isinstance(obj, str):
            cleaned = obj.strip()
            if cleaned and len(cleaned) > 2:
                results.append(cleaned)
        elif isinstance(obj, list):
            for item in obj:
                results.extend(self._flatten_strings(item, depth + 1))
        elif isinstance(obj, dict):
            for v in obj.values():
                results.extend(self._flatten_strings(v, depth + 1))
        return results

    # --- XSS ---
    def _load_xss_payloads(self) -> None:
        data = self._read_yaml(self._payloads_dir / "injection" / "xss.yaml")
        if not data:
            return
        payloads: List[str] = []
        # Prioritized order: basic → filter_bypass → event_handlers → context → polyglot
        for key in ["basic_payloads", "filter_bypass", "event_handlers",
                     "reflected_xss", "stored_xss", "context_specific",
                     "waf_bypass", "dom_xss", "polyglot_payloads"]:
            if key in data:
                payloads.extend(self._flatten_strings(data[key]))
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: List[str] = []
        for p in payloads:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        self._xss_payloads = unique
        logger.info(f"  XSS payloads: {len(self._xss_payloads)}")

    # --- SQL Injection ---
    def _load_sqli_payloads(self) -> None:
        # From test-cases
        tc_data = self._read_yaml(self._test_cases_dir / "A05-injection" / "sql-injection.yaml")
        if tc_data:
            self._sqli_test_cases = tc_data.get("test_cases", [])
            # Extract all payloads from test cases
            payloads: List[str] = []
            for tc in self._sqli_test_cases:
                if "payloads" in tc:
                    payloads.extend(self._flatten_strings(tc["payloads"]))
                if "database_specific" in tc:
                    payloads.extend(self._flatten_strings(tc["database_specific"]))
            # Also add WAF bypass payloads
            if "waf_bypass_techniques" in tc_data:
                payloads.extend(self._flatten_strings(tc_data["waf_bypass_techniques"]))

            seen: set[str] = set()
            for p in payloads:
                if p not in seen:
                    seen.add(p)
                    self._sqli_payloads.append(p)
        logger.info(f"  SQLi payloads: {len(self._sqli_payloads)}")

    # --- NoSQL Injection ---
    def _load_nosqli_payloads(self) -> None:
        data = self._read_yaml(self._payloads_dir / "injection" / "nosql-injection.yaml")
        if not data:
            return
        payloads: List[str] = []
        for key in ["mongodb_authentication_bypass", "mongodb_operator_injection",
                     "mongodb_injection_methods", "login_bypass", "data_extraction",
                     "mongodb_blind", "mongodb_time_based"]:
            if key in data:
                payloads.extend(self._flatten_strings(data[key]))
        seen: set[str] = set()
        for p in payloads:
            if p not in seen:
                seen.add(p)
                self._nosqli_payloads.append(p)
        logger.info(f"  NoSQLi payloads: {len(self._nosqli_payloads)}")

    # --- XXE ---
    def _load_xxe_payloads(self) -> None:
        data = self._read_yaml(self._payloads_dir / "injection" / "xxe.yaml")
        if not data:
            return
        payloads: List[str] = []
        for key in ["xxe_basic", "xxe_ssrf", "xxe_blind_oob", "xxe_error_based",
                     "xxe_soap", "xxe_svg"]:
            if key in data:
                payloads.extend(self._flatten_strings(data[key]))
        seen: set[str] = set()
        for p in payloads:
            if p not in seen and len(p) > 10:
                seen.add(p)
                self._xxe_payloads.append(p)
        logger.info(f"  XXE payloads: {len(self._xxe_payloads)}")

    # --- SSRF ---
    def _load_ssrf_payloads(self) -> None:
        data = self._read_yaml(self._payloads_dir / "ssrf" / "ssrf-payloads.yaml")
        if not data:
            return
        payloads: List[str] = []
        for key in ["basic_ssrf", "cloud_metadata", "bypass_filters"]:
            if key in data:
                payloads.extend(self._flatten_strings(data[key]))
        seen: set[str] = set()
        for p in payloads:
            if p not in seen and (p.startswith("http") or p.startswith("file") or p.startswith("gopher") or p.startswith("dict")):
                seen.add(p)
                self._ssrf_payloads.append(p)
        logger.info(f"  SSRF payloads: {len(self._ssrf_payloads)}")

    # --- Path Traversal ---
    def _load_path_traversal(self) -> None:
        data = self._read_yaml(self._test_cases_dir / "A01-broken-access-control" / "path-traversal.yaml")
        if not data:
            return
        for tc in data.get("test_cases", []):
            if "payloads" in tc:
                self._path_traversal_payloads.extend(self._flatten_strings(tc["payloads"]))
        # Deduplicate
        self._path_traversal_payloads = list(dict.fromkeys(self._path_traversal_payloads))
        logger.info(f"  Path traversal payloads: {len(self._path_traversal_payloads)}")

    # --- Auth Bypass ---
    def _load_auth_bypass(self) -> None:
        data = self._read_yaml(self._payloads_dir / "auth" / "auth-bypass.yaml")
        if not data:
            return
        payloads: List[str] = []
        for key in ["sql_injection_auth", "default_credentials", "brute_force"]:
            if key in data:
                payloads.extend(self._flatten_strings(data[key]))
        seen: set[str] = set()
        for p in payloads:
            if p not in seen:
                seen.add(p)
                self._auth_bypass_payloads.append(p)
        logger.info(f"  Auth bypass payloads: {len(self._auth_bypass_payloads)}")

    # --- IDOR ---
    def _load_idor_tests(self) -> None:
        data = self._read_yaml(self._test_cases_dir / "A01-broken-access-control" / "idor.yaml")
        if not data:
            return
        self._idor_test_cases = data.get("test_cases", [])
        logger.info(f"  IDOR test cases: {len(self._idor_test_cases)}")

    # --- Default Config ---
    def _load_default_config_checks(self) -> None:
        data = self._read_yaml(self._test_cases_dir / "A02-security-misconfiguration" / "default-config.yaml")
        if not data:
            return
        self._default_config_checks = data.get("test_cases", [])
        logger.info(f"  Default config checks: {len(self._default_config_checks)}")

    # ------------------------------------------------------------------
    # KB Metadata Loaders (previously unused — now wired)
    # ------------------------------------------------------------------

    def _load_confidence_scoring(self) -> None:
        data = self._read_yaml(self._metadata_dir / "confidence-scoring.yaml")
        if not data:
            return
        self._confidence_scoring = data
        logger.info("  Confidence scoring rules: loaded")

    def _load_payload_safety(self) -> None:
        data = self._read_yaml(self._metadata_dir / "payload-safety.yaml")
        if not data:
            return
        self._payload_safety = data
        logger.info("  Payload safety classifications: loaded")

    def _load_test_payload_bindings(self) -> None:
        data = self._read_yaml(self._metadata_dir / "test-payload-binding.yaml")
        if not data:
            return
        self._test_payload_bindings = data
        logger.info("  Test-payload bindings: loaded")

    def _load_auth_test_cases(self) -> None:
        data = self._read_yaml(self._test_cases_dir / "A07-auth-failures" / "authentication-testing.yaml")
        if not data:
            return
        self._auth_test_cases = data.get("test_cases", [])
        logger.info(f"  Auth test cases (A07): {len(self._auth_test_cases)}")

    # ------------------------------------------------------------------
    # KB Metadata Public API
    # ------------------------------------------------------------------

    def get_base_confidence(self, vuln_type: str, detection_method: str) -> float:
        """Get base confidence score from confidence-scoring.yaml.

        Falls back to a sensible default (0.70) if not found.
        """
        base_conf = self._confidence_scoring.get("base_confidence", {})
        type_section = base_conf.get(vuln_type, {})
        method_data = type_section.get(detection_method, {})
        return float(method_data.get("base", 0.70))

    def get_confidence_modifier(self, modifier_name: str, polarity: str = "positive") -> float:
        """Get a confidence modifier value from confidence-scoring.yaml.

        Args:
            modifier_name: e.g. "repeatable", "waf_block_suspected"
            polarity: "positive" or "negative"
        """
        modifiers = self._confidence_scoring.get("confidence_modifiers", {})
        section_key = f"{polarity}_indicators"
        section = modifiers.get(section_key, {})
        entry = section.get(modifier_name, {})
        raw = entry.get("modifier", 0.0)
        return float(str(raw).replace("+", ""))

    def get_confidence_thresholds(self) -> Dict[str, float]:
        """Get confidence classification thresholds from confidence-scoring.yaml."""
        score_def = self._confidence_scoring.get("confidence_score", {})
        return {
            "vulnerable": float(score_def.get("threshold_vulnerable", 0.75)),
            "likely": float(score_def.get("threshold_likely", 0.60)),
            "possible": float(score_def.get("threshold_possible", 0.40)),
            "uncertain": float(score_def.get("threshold_uncertain", 0.20)),
        }

    def get_payload_safety_level(self, payload_text: str, category: str = "") -> Dict[str, Any]:
        """Look up safety classification for a payload from payload-safety.yaml.

        Returns dict with keys: safety, destructive, risk_level, auto_scan, environment.
        Falls back to safe defaults if not found.
        """
        default = {"safety": "safe", "destructive": False, "risk_level": 0,
                    "auto_scan": True, "environment": ["dev", "staging", "prod"]}
        # Search all payload sections in the safety YAML
        for section_key in ("xss_payloads", "sql_injection_payloads", "auth_bypass_payloads",
                            "ssrf_payloads", "path_traversal_payloads", "command_injection_payloads"):
            section = self._payload_safety.get(section_key, {})
            for _sub_key, entries in section.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    if isinstance(entry, dict) and entry.get("payload") == payload_text:
                        return {
                            "safety": entry.get("safety", "safe"),
                            "destructive": entry.get("destructive", False),
                            "risk_level": entry.get("risk_level", 0),
                            "auto_scan": entry.get("auto_scan", True),
                            "environment": entry.get("environment", ["dev", "staging", "prod"]),
                        }
        return default

    def is_payload_allowed(self, payload_text: str, environment: str = "prod") -> bool:
        """Check if a payload is allowed in the given environment per payload-safety.yaml."""
        safety = self.get_payload_safety_level(payload_text)
        env_rules = self._payload_safety.get("environment_rules", {})
        env_config = env_rules.get(environment, env_rules.get("production", {}))
        max_risk = env_config.get("max_risk_level", 1)
        if safety["destructive"] and environment not in ("isolated", "dev"):
            return False
        if safety["risk_level"] > max_risk:
            return False
        if environment not in safety["environment"]:
            return False
        return True

    def get_binding_rules(self, test_id: str) -> Dict[str, Any]:
        """Get payload-binding rules for a test case from test-payload-binding.yaml.

        Returns dict with max_payloads, stop_on_success, execution_order.
        Falls back to sensible defaults.
        """
        default = {"max_payloads": 10, "stop_on_success": True, "execution_order": "sequential"}
        # Search across all binding sections
        for section_key in ("xss_test_bindings", "sql_injection_bindings",
                            "auth_bypass_bindings", "ssrf_bindings"):
            section = self._test_payload_bindings.get(section_key, {})
            for _binding_name, binding in section.items():
                if isinstance(binding, dict) and binding.get("test_id") == test_id:
                    return {
                        "max_payloads": binding.get("max_payloads", 10),
                        "stop_on_success": binding.get("stop_on_success", True),
                        "execution_order": binding.get("execution_order", "sequential"),
                    }
        return default

    def get_auth_test_methodology(self, test_id: str = "AUTH-001") -> Dict[str, Any]:
        """Get auth test methodology from authentication-testing.yaml."""
        for tc in self._auth_test_cases:
            if tc.get("id") == test_id:
                return tc
        return {}

    def get_safety_levels(self) -> Dict[str, Any]:
        """Get safety level definitions from payload-safety.yaml."""
        return self._payload_safety.get("safety_levels", {})


# Singleton
_engine: Optional[PayloadEngine] = None


def get_payload_engine() -> PayloadEngine:
    """Get or create the global PayloadEngine singleton."""
    global _engine
    if _engine is None:
        _engine = PayloadEngine()
        _engine.load()
    return _engine
