"""
AdvancedDiscoveryEngine — plugs into orchestrator Phase 2 + Phase 4.
Generates 15-25+ findings per scan using only existing Python deps.
"""
import logging, ssl, socket, re, time, json
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse, urljoin, parse_qs
from pathlib import Path
from datetime import datetime

import requests, yaml
from bs4 import BeautifulSoup

from app.models.models import VulnerabilitySeverity

logger = logging.getLogger(__name__)

KB_ROOT = Path(__file__).resolve().parents[3] / "knowledge-base"

def _load_yaml(rel: str) -> dict:
    try:
        with open(KB_ROOT / rel, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


class AdvancedDiscoveryEngine:
    """Drop-in enhancement engine for the orchestrator pipeline."""

    # ── directory brute-force wordlist ──
    COMMON_PATHS = [
        "/robots.txt", "/sitemap.xml", "/.env", "/.git/HEAD",
        "/admin", "/admin/", "/administrator/", "/login", "/wp-admin/",
        "/wp-login.php", "/api", "/api/v1", "/api/v2", "/graphql",
        "/swagger", "/swagger-ui.html", "/docs", "/redoc", "/openapi.json",
        "/.DS_Store", "/.svn/entries", "/backup", "/backup.zip",
        "/config.php.bak", "/phpinfo.php", "/test.php", "/debug",
        "/server-status", "/server-info", "/.well-known/security.txt",
        "/actuator/health", "/actuator/info", "/actuator/env",
        "/wp-content/", "/wp-includes/", "/xmlrpc.php",
        "/console", "/elmah.axd", "/trace.axd",
        "/cgi-bin/", "/.htaccess", "/.htpasswd",
        "/crossdomain.xml", "/clientaccesspolicy.xml",
        "/package.json", "/composer.json", "/Gemfile",
        "/CHANGELOG.md", "/VERSION", "/readme.html",
    ]

    PATH_TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\win.ini",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    ]

    SQL_ERROR_SIGNATURES = [
        "sql syntax", "mysql", "warning: mysql", "unclosed quotation mark",
        "quoted string not properly terminated", "pg_query", "postgresql",
        "sqlite error", "odbc sql", "oracle error", "sqlstate",
        "microsoft ole db", "ora-00933", "ora-01756",
    ]

    SQLI_PAYLOADS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "1' AND '1'='1",
        "' UNION SELECT NULL--",
        "1; SELECT 1--",
    ]

    SQLI_TIME_PAYLOADS = [
        ("' OR SLEEP(3)-- ", 3),
        ("'; WAITFOR DELAY '00:00:03'-- ", 3),
        ("' OR pg_sleep(3)-- ", 3),
    ]

    OPEN_REDIRECT_PARAMS = ["url", "redirect", "next", "return", "returnUrl",
                            "redirect_uri", "continue", "dest", "destination", "go", "out"]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "NeuroPent-Scanner/2.0"
        self.session.verify = False
        self.fingerprint_db = _load_yaml("reconnaissance/fingerprinting.yaml")
        self.xss_payloads_db = _load_yaml("payloads/injection/xss.yaml")
        self.findings: List[Dict[str, Any]] = []

    # ─────────────────────────────────────────
    # PUBLIC API — called from orchestrator
    # ─────────────────────────────────────────

    def run_phase2_recon(self, target_url: str, max_depth: int = 2) -> Dict[str, Any]:
        """Phase 2 enhancement: deep crawl + dir brute + fingerprint."""
        parsed = urlparse(target_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        crawled: Set[str] = set()
        discovered_urls: Set[str] = set()
        discovered_urls.add(target_url)

        # 1 — multi-depth BS4 crawl
        self._bs4_crawl(target_url, base, parsed.netloc, crawled, discovered_urls, 0, max_depth)

        # 2 — robots.txt / sitemap.xml parsing
        self._parse_robots(base, parsed.netloc, discovered_urls)
        self._parse_sitemap(base, parsed.netloc, discovered_urls)

        # 3 — directory brute-force
        dir_results = self._dir_bruteforce(base)
        for r in dir_results:
            discovered_urls.add(r["url"])

        # 4 — technology fingerprinting (root page)
        tech_results = self._fingerprint_tech(target_url)

        return {
            "discovered_urls": discovered_urls,
            "crawled_pages": len(crawled),
            "dir_brute_hits": dir_results,
            "technologies": tech_results,
        }

    def run_phase4_checks(self, target_url: str, discovered_urls: Set[str]) -> List[Dict[str, Any]]:
        """Phase 4 enhancement: SSL, CORS, clickjacking, redirect, traversal, XSS fuzz."""
        self.findings = []
        parsed = urlparse(target_url)

        # 1 — SSL/TLS checks
        self._check_ssl(parsed.hostname, 443 if parsed.scheme == "https" else None)

        # 2 — per-URL checks (limit to 40 endpoints)
        root_resp = self._safe_get(target_url)
        if root_resp:
            self._check_cors(target_url, root_resp)
            self._check_clickjacking(target_url, root_resp)
            self._check_http_methods(target_url)

        for url in list(discovered_urls)[:40]:
            resp = self._safe_get(url)
            if not resp:
                continue
            self._check_directory_listing(url, resp)
            self._check_sensitive_file(url, resp)
            self._check_robots_disclosure(url, resp)
            self._check_cors(url, resp)
            self._check_clickjacking(url, resp)
            self._check_open_redirect(url)
            self._check_path_traversal(url)
            self._check_xss_fuzz(url, resp)
            self._check_sqli_error_based(url)
            self._check_sqli_time_blind(url)

        return self.findings

    # ─────────────────────────────────────────
    # PHASE 2 HELPERS
    # ─────────────────────────────────────────

    def _bs4_crawl(self, url, base, netloc, crawled, discovered, depth, max_depth):
        if depth > max_depth or url in crawled or len(crawled) > 80:
            return
        crawled.add(url)
        resp = self._safe_get(url)
        if not resp or "html" not in (resp.headers.get("content-type") or ""):
            return
        try:
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception:
            soup = BeautifulSoup(resp.text, "html.parser")

        for tag, attr in [("a","href"),("script","src"),("link","href"),("img","src"),("form","action")]:
            for el in soup.find_all(tag):
                val = el.get(attr)
                if not val:
                    continue
                abs_url = urljoin(url, val)
                p = urlparse(abs_url)
                if p.scheme in ("http","https") and p.netloc == netloc:
                    clean = f"{p.scheme}://{p.netloc}{p.path or '/'}"
                    if clean not in discovered:
                        discovered.add(clean)
                        if tag == "a" and depth + 1 <= max_depth:
                            self._bs4_crawl(clean, base, netloc, crawled, discovered, depth+1, max_depth)

        # meta/script fingerprint hints already handled in _fingerprint_tech

    def _parse_robots(self, base, netloc, discovered):
        resp = self._safe_get(f"{base}/robots.txt")
        if not resp or resp.status_code != 200:
            return
        for line in resp.text.splitlines():
            line = line.strip()
            if line.lower().startswith(("allow:", "disallow:", "sitemap:")):
                path = line.split(":", 1)[1].strip()
                if path.startswith("/"):
                    discovered.add(f"{base}{path}")
                elif path.startswith("http"):
                    discovered.add(path)

    def _parse_sitemap(self, base, netloc, discovered):
        resp = self._safe_get(f"{base}/sitemap.xml")
        if not resp or resp.status_code != 200:
            return
        for match in re.findall(r"<loc>(.*?)</loc>", resp.text, re.I):
            p = urlparse(match)
            if p.netloc == netloc:
                discovered.add(match)

    def _dir_bruteforce(self, base) -> List[Dict[str, Any]]:
        hits = []
        for path in self.COMMON_PATHS:
            url = f"{base}{path}"
            try:
                r = self.session.head(url, timeout=5, allow_redirects=False)
                if r.status_code in (200, 301, 302, 403):
                    if r.status_code != 200:
                        r2 = self._safe_get(url)
                        status = r2.status_code if r2 else r.status_code
                    else:
                        status = 200
                    hits.append({"url": url, "status": status, "path": path})
            except Exception:
                pass
        return hits

    def _fingerprint_tech(self, target_url) -> List[Dict[str, Any]]:
        techs = []
        resp = self._safe_get(target_url)
        if not resp:
            return techs
        headers = {k.lower(): v for k, v in resp.headers.items()}
        body = resp.text or ""
        lower_body = body.lower()

        # Server/X-Powered-By
        for hdr in ("server", "x-powered-by", "x-aspnet-version"):
            if headers.get(hdr):
                techs.append({"name": hdr, "value": headers[hdr], "source": "header"})
                self._add_finding(
                    title=f"Technology Detected: {hdr}={headers[hdr]}",
                    desc=f"Server exposes {hdr} header revealing technology stack.",
                    sev=VulnerabilitySeverity.INFO, owasp="A05",
                    vtype="TECHNOLOGY_DETECTED", conf=0.90,
                    url=target_url, vector="fingerprint",
                    evidence=f"{hdr}: {headers[hdr]}")

        # Framework signatures from KB
        sigs = self.fingerprint_db.get("framework_signatures", {})
        for lang, frameworks in sigs.items():
            if not isinstance(frameworks, dict):
                continue
            for fw_name, fw_data in frameworks.items():
                if not isinstance(fw_data, dict):
                    continue
                indicators = fw_data.get("indicators", [])
                for ind in indicators:
                    ind_lower = str(ind).lower()
                    # Check body and headers
                    if ind_lower in lower_body or any(ind_lower in v.lower() for v in headers.values()):
                        techs.append({"name": fw_name, "indicator": ind, "source": "body/header"})
                        self._add_finding(
                            title=f"Framework Detected: {fw_name}",
                            desc=f"Indicator '{ind}' matches {fw_name} ({lang}).",
                            sev=VulnerabilitySeverity.INFO, owasp="A05",
                            vtype="TECHNOLOGY_DETECTED", conf=0.82,
                            url=target_url, vector="fingerprint",
                            evidence=f"Matched indicator: {ind}")
                        break

        # Meta generator tag + outdated component detection
        try:
            soup = BeautifulSoup(body, "html.parser")
            gen = soup.find("meta", attrs={"name": re.compile(r"generator", re.I)})
            if gen and gen.get("content"):
                gen_val = gen["content"]
                techs.append({"name": "generator", "value": gen_val, "source": "meta"})
                self._add_finding(
                    title=f"CMS/Generator Disclosed: {gen_val}",
                    desc="Meta generator tag reveals CMS or framework version.",
                    sev=VulnerabilitySeverity.LOW, owasp="A05",
                    vtype="TECHNOLOGY_DETECTED", conf=0.92,
                    url=target_url, vector="meta_tag",
                    evidence=f"<meta name=generator content='{gen_val}'>")
                # Check for outdated versions
                version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', gen_val)
                if version_match:
                    self._check_outdated_component(gen_val, version_match.group(1), target_url)
        except Exception:
            pass

        # Check server header for version-based outdated component
        server_val = headers.get("server", "")
        if server_val:
            version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', server_val)
            if version_match:
                self._check_outdated_component(server_val, version_match.group(1), target_url)

        return techs

    # ─────────────────────────────────────────
    # PHASE 4 CHECKS
    # ─────────────────────────────────────────

    def _check_ssl(self, hostname, port):
        if not hostname or not port:
            return
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    if cert:
                        not_after = ssl.cert_time_to_seconds(cert.get("notAfter", ""))
                        if not_after < time.time():
                            self._add_finding(
                                title=f"SSL Certificate Expired on {hostname}",
                                desc="The TLS certificate has expired, causing browser warnings and MITM risk.",
                                sev=VulnerabilitySeverity.HIGH, owasp="A02",
                                vtype="SSL_CERTIFICATE_EXPIRED", conf=0.98,
                                url=f"https://{hostname}", vector="ssl",
                                evidence=f"notAfter: {cert.get('notAfter')}")
                        days_left = (not_after - time.time()) / 86400
                        if 0 < days_left < 30:
                            self._add_finding(
                                title=f"SSL Certificate Expiring Soon ({int(days_left)}d) on {hostname}",
                                desc=f"Certificate expires in {int(days_left)} days.",
                                sev=VulnerabilitySeverity.MEDIUM, owasp="A02",
                                vtype="SSL_CERTIFICATE_EXPIRING", conf=0.95,
                                url=f"https://{hostname}", vector="ssl",
                                evidence=f"notAfter: {cert.get('notAfter')}, days_left={int(days_left)}")
        except ssl.SSLCertVerificationError as e:
            err = str(e).lower()
            if "self-signed" in err or "self signed" in err:
                self._add_finding(
                    title=f"Self-Signed SSL Certificate on {hostname}",
                    desc="Self-signed certificate detected — browsers will show security warnings.",
                    sev=VulnerabilitySeverity.MEDIUM, owasp="A02",
                    vtype="SSL_SELF_SIGNED", conf=0.96,
                    url=f"https://{hostname}", vector="ssl",
                    evidence=str(e)[:300])
            else:
                self._add_finding(
                    title=f"SSL Certificate Verification Failed on {hostname}",
                    desc="TLS certificate failed validation.",
                    sev=VulnerabilitySeverity.MEDIUM, owasp="A02",
                    vtype="SSL_CERTIFICATE_INVALID", conf=0.90,
                    url=f"https://{hostname}", vector="ssl",
                    evidence=str(e)[:300])
        except Exception:
            pass

    def _check_cors(self, url, resp):
        # Only check once per url
        try:
            r = self.session.get(url, headers={"Origin": "https://evil-cors-test.com"}, timeout=8, allow_redirects=True)
            acao = r.headers.get("access-control-allow-origin", "")
            acac = r.headers.get("access-control-allow-credentials", "").lower()
            if acao == "*" or "evil-cors-test.com" in acao:
                sev = VulnerabilitySeverity.HIGH if acac == "true" else VulnerabilitySeverity.MEDIUM
                self._add_finding(
                    title=f"CORS Misconfiguration at {url}",
                    desc=f"Origin reflected/wildcard ACAO={acao}, credentials={acac}.",
                    sev=sev, owasp="A01", vtype="CORS_MISCONFIGURATION", conf=0.88,
                    url=url, vector="cors",
                    evidence=f"ACAO: {acao}, ACAC: {acac}")
        except Exception:
            pass

    def _check_clickjacking(self, url, resp):
        h = {k.lower(): v for k, v in resp.headers.items()}
        xfo = h.get("x-frame-options", "")
        csp = h.get("content-security-policy", "")
        if not xfo and "frame-ancestors" not in csp:
            self._add_finding(
                title=f"Clickjacking Vulnerable: {url}",
                desc="Missing X-Frame-Options and CSP frame-ancestors, allowing iframe embedding.",
                sev=VulnerabilitySeverity.MEDIUM, owasp="A05",
                vtype="CLICKJACKING_VULNERABLE", conf=0.85,
                url=url, vector="http_response_headers",
                evidence="No X-Frame-Options or frame-ancestors directive")

    def _check_http_methods(self, url):
        for method in ("TRACE", "OPTIONS"):
            try:
                r = self.session.request(method, url, timeout=5)
                if method == "TRACE" and r.status_code == 200:
                    self._add_finding(
                        title=f"HTTP TRACE Method Enabled at {url}",
                        desc="TRACE is enabled, potentially allowing XST attacks.",
                        sev=VulnerabilitySeverity.LOW, owasp="A05",
                        vtype="HTTP_METHOD_OVERRIDE", conf=0.88,
                        url=url, vector="http_method",
                        evidence=f"TRACE returned {r.status_code}")
                if method == "OPTIONS" and r.status_code == 200:
                    allow = r.headers.get("Allow", "")
                    if any(m in allow.upper() for m in ("PUT", "DELETE", "TRACE")):
                        self._add_finding(
                            title=f"Dangerous HTTP Methods Allowed at {url}",
                            desc=f"OPTIONS reveals risky methods: {allow}",
                            sev=VulnerabilitySeverity.LOW, owasp="A05",
                            vtype="HTTP_METHOD_OVERRIDE", conf=0.80,
                            url=url, vector="http_method",
                            evidence=f"Allow: {allow}")
            except Exception:
                pass

    def _check_directory_listing(self, url, resp):
        body = (resp.text or "").lower()
        if resp.status_code == 200 and any(sig in body for sig in
            ["index of /", "directory listing", "<title>index of", "parent directory"]):
            self._add_finding(
                title=f"Directory Listing Enabled: {url}",
                desc="Open directory index exposes file structure.",
                sev=VulnerabilitySeverity.MEDIUM, owasp="A01",
                vtype="DIRECTORY_LISTING", conf=0.92,
                url=url, vector="directory_listing",
                evidence="Directory listing signature in response body")

    def _check_sensitive_file(self, url, resp):
        lower_path = urlparse(url).path.lower()
        sensitive = {
            "/.env": "Environment configuration (may contain secrets)",
            "/.git/head": "Git repository metadata exposed",
            "/.htpasswd": "Apache password file exposed",
            "/.htaccess": "Apache configuration exposed",
            "/config.php.bak": "Backup config file with potential credentials",
            "/phpinfo.php": "PHP info page exposes server configuration",
            "/package.json": "Node.js dependencies exposed",
            "/composer.json": "PHP dependencies exposed",
            "/web.config": "ASP.NET configuration exposed",
        }
        for path, desc in sensitive.items():
            if lower_path.endswith(path) and resp.status_code == 200 and len(resp.text or "") > 10:
                self._add_finding(
                    title=f"Sensitive File Exposed: {path}",
                    desc=desc,
                    sev=VulnerabilitySeverity.HIGH, owasp="A01",
                    vtype="SENSITIVE_FILE_EXPOSURE", conf=0.93,
                    url=url, vector="sensitive_file",
                    evidence=f"HTTP 200 on {path}, body length={len(resp.text)}")
                break

    def _check_robots_disclosure(self, url, resp):
        if not urlparse(url).path.rstrip("/").endswith("robots.txt"):
            return
        if resp.status_code != 200:
            return
        sensitive_kw = ["admin", "backup", "config", "secret", "internal", "private", "api", "debug", ".env", ".git"]
        body = resp.text or ""
        found = [kw for kw in sensitive_kw if kw in body.lower()]
        if found:
            self._add_finding(
                title=f"Robots.txt Discloses Sensitive Paths",
                desc=f"robots.txt reveals potentially sensitive paths containing: {', '.join(found)}",
                sev=VulnerabilitySeverity.LOW, owasp="A01",
                vtype="ROBOTS_TXT_DISCLOSURE", conf=0.82,
                url=url, vector="robots_txt",
                evidence=f"Sensitive keywords found: {', '.join(found)}")

    def _check_open_redirect(self, url):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        targets = [p for p in params if p.lower() in self.OPEN_REDIRECT_PARAMS]
        if not targets:
            return
        for param in targets[:1]:
            evil = "https://evil-redirect-test.com"
            try:
                r = self.session.get(url, params={param: evil}, timeout=8, allow_redirects=False)
                loc = r.headers.get("location", "")
                if evil in loc:
                    self._add_finding(
                        title=f"Open Redirect via '{param}' at {url}",
                        desc=f"Parameter '{param}' redirects to arbitrary external URLs.",
                        sev=VulnerabilitySeverity.MEDIUM, owasp="A01",
                        vtype="OPEN_REDIRECT", conf=0.85,
                        url=url, vector="open_redirect",
                        evidence=f"Location: {loc[:200]}",
                        payload=f"{param}={evil}")
            except Exception:
                pass

    def _check_path_traversal(self, url):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        file_params = [p for p in params if any(k in p.lower() for k in
            ["file", "path", "page", "include", "doc", "template", "dir", "folder"])]
        if not file_params:
            return
        for param in file_params[:1]:
            for payload in self.PATH_TRAVERSAL_PAYLOADS[:2]:
                try:
                    r = self.session.get(url, params={param: payload}, timeout=8)
                    body = (r.text or "").lower()
                    if any(sig in body for sig in ["root:", "[extensions]", "daemon:", "bin/bash"]):
                        self._add_finding(
                            title=f"Path Traversal via '{param}' at {url}",
                            desc=f"File inclusion detected through '{param}' parameter.",
                            sev=VulnerabilitySeverity.CRITICAL, owasp="A01",
                            vtype="PATH_TRAVERSAL", conf=0.90,
                            url=url, vector="path_traversal",
                            evidence="System file content detected in response",
                            payload=f"{param}={payload}")
                        return
                except Exception:
                    pass

    def _check_xss_fuzz(self, url, resp):
        """Multi-payload XSS fuzzing from KB."""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if not params:
            return
        payloads = self.xss_payloads_db.get("basic_payloads", [])[:5]
        fb = self.xss_payloads_db.get("filter_bypass", {})
        payloads += fb.get("no_script_tag", [])[:2]
        if not payloads:
            payloads = ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"]

        for pname in list(params.keys())[:2]:
            for payload in payloads[:4]:
                try:
                    r = self.session.get(url, params={pname: payload}, timeout=8, allow_redirects=True)
                    if payload in (r.text or ""):
                        self._add_finding(
                            title=f"Reflected XSS via '{pname}' at {url}",
                            desc=f"XSS payload reflected unencoded in response through parameter '{pname}'.",
                            sev=VulnerabilitySeverity.HIGH, owasp="A03",
                            vtype="REFLECTED_XSS", conf=0.85,
                            url=url, vector="xss_fuzz",
                            evidence=f"Payload reflected: {payload[:80]}",
                            payload=f"{pname}={payload}")
                        return  # one per URL
                except Exception:
                    pass

    # ─────────────────────────────────────────
    # SQL INJECTION CHECKS
    # ─────────────────────────────────────────

    def _check_sqli_error_based(self, url):
        """Error-based SQL injection using multiple payloads."""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if not params:
            return
        for pname in list(params.keys())[:2]:
            for payload in self.SQLI_PAYLOADS[:3]:
                try:
                    r = self.session.get(url, params={pname: payload}, timeout=8)
                    body = (r.text or "").lower()
                    if any(sig in body for sig in self.SQL_ERROR_SIGNATURES):
                        self._add_finding(
                            title=f"SQL Injection (Error-Based) via '{pname}' at {url}",
                            desc=f"SQL error signature detected after injecting payload into '{pname}'.",
                            sev=VulnerabilitySeverity.CRITICAL, owasp="A03",
                            vtype="SQL_INJECTION_ERROR", conf=0.88,
                            url=url, vector="sqli_error_based",
                            evidence="Database error signature in response",
                            payload=f"{pname}={payload}")
                        return
                except Exception:
                    pass

    def _check_sqli_time_blind(self, url):
        """Time-based blind SQL injection detection."""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if not params:
            return
        for pname in list(params.keys())[:1]:
            # Baseline timing
            try:
                t0 = time.time()
                self.session.get(url, params={pname: "1"}, timeout=10)
                baseline = time.time() - t0
            except Exception:
                continue
            for payload, delay in self.SQLI_TIME_PAYLOADS[:2]:
                try:
                    t0 = time.time()
                    self.session.get(url, params={pname: payload}, timeout=delay + 8)
                    elapsed = time.time() - t0
                    if elapsed >= baseline + delay - 0.5:
                        self._add_finding(
                            title=f"SQL Injection (Time-Based Blind) via '{pname}' at {url}",
                            desc=f"Response delayed by ~{int(elapsed)}s with SLEEP/WAITFOR payload in '{pname}'.",
                            sev=VulnerabilitySeverity.CRITICAL, owasp="A03",
                            vtype="SQL_INJECTION_TIME_BLIND", conf=0.80,
                            url=url, vector="sqli_time_blind",
                            evidence=f"Baseline={baseline:.1f}s, Injected={elapsed:.1f}s, Expected delay={delay}s",
                            payload=f"{pname}={payload}")
                        return
                except Exception:
                    pass

    def _check_outdated_component(self, product: str, version: str, url: str):
        """Flag potentially outdated components by checking known EOL/old versions."""
        outdated_patterns = {
            "apache": "2.2", "nginx": "1.18", "php": "7.4",
            "wordpress": "5.", "jquery": "1.", "drupal": "8.",
            "iis": "8.", "openssl": "1.0", "tomcat": "8.",
        }
        product_lower = product.lower()
        for name, old_prefix in outdated_patterns.items():
            if name in product_lower and version.startswith(old_prefix):
                self._add_finding(
                    title=f"Outdated Component: {product}",
                    desc=f"{product} version {version} may be outdated/EOL. Check for security patches.",
                    sev=VulnerabilitySeverity.MEDIUM, owasp="A06",
                    vtype="OUTDATED_COMPONENT", conf=0.78,
                    url=url, vector="version_detection",
                    evidence=f"Detected: {product}, version: {version}")
                return

    # ─────────────────────────────────────────
    # UTILITIES
    # ─────────────────────────────────────────

    def _safe_get(self, url, **kw) -> Optional[requests.Response]:
        try:
            return self.session.get(url, timeout=kw.pop("timeout", 10), allow_redirects=True, **kw)
        except Exception:
            return None

    def _add_finding(self, *, title, desc, sev, owasp, vtype, conf, url, vector, evidence, payload=None):
        # Dedupe by (vtype, url)
        key = (vtype, url)
        if any((f["vulnerability_type"], f["endpoint_url"]) == key for f in self.findings):
            return
        self.findings.append({
            "title": title,
            "description": desc,
            "severity": sev,
            "owasp_category": owasp,
            "vulnerability_type": vtype,
            "confidence": conf,
            "endpoint_url": url,
            "attack_vector": vector,
            "response_evidence": evidence,
            "request_payload": payload,
        })
