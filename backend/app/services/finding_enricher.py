"""
FindingEnricher — Enriches scan findings with OWASP, CWE, and CVSS metadata
from the knowledge-base YAML files.

Loaded files:
  - metadata/owasp_top10_2025.yaml
  - metadata/cwe.yaml
  - metadata/cvss.yaml
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

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


# ──────────────────────────────────────────────────────────────────────
# Vulnerability Type → CWE mapping
# ──────────────────────────────────────────────────────────────────────
VULN_TYPE_TO_CWE = {
    "POTENTIAL_REFLECTED_XSS": "CWE-79",
    "REFLECTED_XSS": "CWE-79",
    "STORED_XSS": "CWE-79",
    "POTENTIAL_SQL_INJECTION": "CWE-89",
    "SQL_INJECTION_ERROR": "CWE-89",
    "SQL_INJECTION_TIME": "CWE-89",
    "AUTH_BYPASS": "CWE-287",
    "AUTH_SURFACE": "CWE-287",
    "MISSING_CSRF_TOKEN": "CWE-352",
    "CORS_MISCONFIGURATION": "CWE-942",
    "CLICKJACKING_VULNERABLE": "CWE-1021",
    "PATH_TRAVERSAL": "CWE-22",
    "INFORMATION_DISCLOSURE": "CWE-200",
    "TECHNOLOGY_DETECTED": "CWE-200",
    "SECURITY_MISCONFIGURATION": "CWE-16",
    "INSECURE_TRANSPORT": "CWE-319",
    "INSECURE_SESSION_COOKIE": "CWE-614",
    "SSL_CERTIFICATE_EXPIRED": "CWE-295",
    "SSL_SELF_SIGNED": "CWE-295",
    "SSL_CERTIFICATE_INVALID": "CWE-295",
    "SSL_CERTIFICATE_EXPIRING": "CWE-295",
    "OUTDATED_COMPONENT": "CWE-1104",
    "POTENTIAL_IDOR": "CWE-639",
    "SSRF_DETECTED": "CWE-918",
    "XXE_DETECTED": "CWE-611",
    "NOSQL_INJECTION": "CWE-943",
    "OPEN_REDIRECT": "CWE-601",
    "HTTP_METHOD_OVERRIDE": "CWE-16",
    "DIRECTORY_LISTING": "CWE-548",
    "SENSITIVE_FILE_EXPOSED": "CWE-538",
}

# Vulnerability Type → CVSS vector string mapping (common cases)
VULN_TYPE_TO_CVSS = {
    "POTENTIAL_SQL_INJECTION": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "score": 9.8},
    "SQL_INJECTION_ERROR": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "score": 9.8},
    "POTENTIAL_REFLECTED_XSS": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", "score": 6.1},
    "REFLECTED_XSS": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N", "score": 6.1},
    "AUTH_BYPASS": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N", "score": 9.1},
    "MISSING_CSRF_TOKEN": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:H/A:N", "score": 6.5},
    "PATH_TRAVERSAL": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", "score": 7.5},
    "SSRF_DETECTED": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:L/A:N", "score": 9.3},
    "CLICKJACKING_VULNERABLE": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N", "score": 4.3},
    "CORS_MISCONFIGURATION": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:N/A:N", "score": 6.5},
    "INFORMATION_DISCLOSURE": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N", "score": 5.3},
    "SECURITY_MISCONFIGURATION": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N", "score": 5.3},
    "INSECURE_TRANSPORT": {"vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N", "score": 5.9},
    "INSECURE_SESSION_COOKIE": {"vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N", "score": 5.9},
    "XXE_DETECTED": {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N", "score": 7.5},
}


class FindingEnricher:
    """Enriches vulnerability findings with OWASP, CWE, and CVSS metadata."""

    def __init__(self):
        self._loaded = False
        self._owasp_data: Dict[str, Any] = {}
        self._cwe_data: Dict[str, Any] = {}
        self._cvss_data: Dict[str, Any] = {}
        # Indexed lookups
        self._owasp_by_id: Dict[str, Dict[str, Any]] = {}
        self._cwe_by_id: Dict[str, Dict[str, Any]] = {}

    def load(self) -> None:
        """Load OWASP, CWE, and CVSS YAML files."""
        if self._loaded:
            return
        if yaml is None:
            logger.warning("PyYAML not installed — finding enricher disabled")
            self._loaded = True
            return

        logger.info("FindingEnricher: loading OWASP/CWE/CVSS from knowledge-base")
        self._owasp_data = _load_yaml("metadata/owasp_top10_2025.yaml")
        self._cwe_data = _load_yaml("metadata/cwe.yaml")
        self._cvss_data = _load_yaml("metadata/cvss.yaml")

        self._build_owasp_index()
        self._build_cwe_index()

        logger.info(
            f"FindingEnricher: {len(self._owasp_by_id)} OWASP categories, "
            f"{len(self._cwe_by_id)} CWE entries loaded"
        )
        self._loaded = True

    def enrich(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single finding with OWASP, CWE, and CVSS metadata.

        Adds the following keys to the finding dict:
          - owasp_details: {category, rank, prevention, references, incidence_rate}
          - cwe_id: "CWE-79"
          - cwe_details: {name, description, cvss_score}
          - cvss: {vector_string, score, severity_rating}
        """
        if not self._loaded:
            self.load()

        vuln_type = finding.get("vulnerability_type", "")
        owasp_cat = finding.get("owasp_category", "")

        # Helper to safely flatten lists or dicts of lists
        def _safe_slice(val: Any, limit: int) -> list:
            if isinstance(val, list):
                return val[:limit]
            if isinstance(val, dict):
                flattened = []
                for v in val.values():
                    if isinstance(v, list):
                        flattened.extend(v)
                    else:
                        flattened.append(str(v))
                return flattened[:limit]
            if val is None:
                return []
            return [str(val)][:limit]

        # OWASP enrichment
        owasp_info = self._owasp_by_id.get(owasp_cat, {})
        if owasp_info:
            finding["owasp_details"] = {
                "category": owasp_info.get("category", ""),
                "rank": owasp_info.get("rank", 0),
                "prevention": _safe_slice(owasp_info.get("prevention"), 5),
                "references": _safe_slice(owasp_info.get("references"), 3),
                "incidence_rate": owasp_info.get("avg_incidence_rate", ""),
                "total_cves": owasp_info.get("total_cves", 0),
                "notable_cwes": _safe_slice(owasp_info.get("notable_cwes"), 5),
            }

        # CWE enrichment
        cwe_id = VULN_TYPE_TO_CWE.get(vuln_type, "")
        if cwe_id:
            finding["cwe_id"] = cwe_id
            cwe_info = self._cwe_by_id.get(cwe_id, {})
            if cwe_info:
                finding["cwe_details"] = {
                    "name": cwe_info.get("name", ""),
                    "description": cwe_info.get("description", ""),
                    "cvss_score": cwe_info.get("cvss_score"),
                }

        # CVSS enrichment
        cvss_entry = VULN_TYPE_TO_CVSS.get(vuln_type)
        if cvss_entry:
            score = cvss_entry["score"]
            finding["cvss"] = {
                "vector_string": cvss_entry["vector"],
                "score": score,
                "severity_rating": self._cvss_severity(score),
            }
        elif cwe_id and self._cwe_by_id.get(cwe_id, {}).get("cvss_score"):
            score = self._cwe_by_id[cwe_id]["cvss_score"]
            finding["cvss"] = {
                "vector_string": "",
                "score": score,
                "severity_rating": self._cvss_severity(score),
            }

        return finding

    def enrich_batch(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich a list of findings."""
        return [self.enrich(f) for f in findings]

    def get_owasp_category(self, category_id: str) -> Dict[str, Any]:
        """Get full OWASP category details by ID (e.g., 'A01')."""
        return self._owasp_by_id.get(category_id, {})

    def get_cwe_info(self, cwe_id: str) -> Dict[str, Any]:
        """Get CWE details by ID (e.g., 'CWE-79')."""
        return self._cwe_by_id.get(cwe_id, {})

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_owasp_index(self):
        """Index OWASP categories by ID for O(1) lookup."""
        for entry in self._owasp_data.get("top_10_2025", []):
            cat_id = entry.get("id", "")
            if cat_id:
                self._owasp_by_id[cat_id] = entry

    def _build_cwe_index(self):
        """Flatten all CWE entries into a single lookup dict."""
        # Top 25
        for cwe_id, data in self._cwe_data.get("top_25_dangerous", {}).items():
            if isinstance(data, dict):
                self._cwe_by_id[cwe_id] = data
        # Web application CWEs
        for category, cwes in self._cwe_data.get("web_application_cwes", {}).items():
            if isinstance(cwes, dict):
                for cwe_id, data in cwes.items():
                    if isinstance(data, dict):
                        self._cwe_by_id[cwe_id] = data

    def _cvss_severity(self, score: float) -> str:
        """Map CVSS score to severity rating using KB definitions."""
        if score >= 9.0:
            return "CRITICAL"
        elif score >= 7.0:
            return "HIGH"
        elif score >= 4.0:
            return "MEDIUM"
        elif score >= 0.1:
            return "LOW"
        return "NONE"


# Singleton
_enricher: Optional[FindingEnricher] = None


def get_finding_enricher() -> FindingEnricher:
    """Get or create the global FindingEnricher singleton."""
    global _enricher
    if _enricher is None:
        _enricher = FindingEnricher()
        _enricher.load()
    return _enricher
