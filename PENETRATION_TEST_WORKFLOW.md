# NeuroPentWeb - Penetration Testing Workflow

## Complete End-to-End Process Documentation

**Version:** 1.0  
**Date:** March 26, 2026  
**Target:** Automated Web Application Penetration Testing with Deterministic Rule-Based Attack Planning

---

## Table of Contents

1. [Overview](#overview)
2. [Complete Workflow Diagram](#complete-workflow-diagram)
3. [Phase-by-Phase Breakdown](#phase-by-phase-breakdown)
4. [Real-Time Updates](#real-time-updates)
5. [Technology Stack](#technology-stack)
6. [Timeline & Performance](#timeline--performance)
7. [Final Output](#final-output)
8. [API Integration](#api-integration)

---

## Overview

When you submit a target URL (e.g., `http://demo.testfire.net/`) to NeuroPentWeb, the system executes a **7-phase automated penetration testing pipeline** that:

- Uses LLM-powered intelligent attack planning
- Performs intelligent reconnaissance and endpoint discovery
- Executes targeted exploitation tests
- Validates findings with business context
- Generates comprehensive security reports

The entire process is **deterministic, rule-based, and audit-logged** for compliance and reproducibility.

---

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NEUROPENTWEB PENTEST                         │
└─────────────────────────────────────────────────────────────────────┘

                         FRONTEND (Vite)
                    http://localhost:5173
                              │
                              │ User submits target URL
                              ▼
                    ┌──────────────────┐
                    │ Create Scan Form │
                    │ - Target URL     │
                    │ - Scan Type      │
                    │ - Authentication │
                    └──────────────────┘
                              │
                              │ POST /api/v1/scans/
                              ▼
         ┌────────────────────────────────────────────────┐
         │         BACKEND API (FastAPI)                  │
         │       http://localhost:8000                    │
         │                                                │
         │  ┌──────────────────────────────────────────┐ │
         │  │   ORCHESTRATOR SERVICE                   │ │
         │  │   7-Phase Automated Pipeline             │ │
         │  │                                          │ │
         │  │  Phase 1: Initial Attack Strategy  ──┐  │ │
         │  │  Phase 2: Reconnaissance           ──┤  │ │
         │  │  Phase 3: Execution Plan Creation ──┤  │ │
         │  │  Phase 4: Active Exploitation     ──┤  │ │
         │  │  Phase 5: Validation & Analysis   ──┤  │ │
         │  │  Phase 6: Report Generation       ──┘  │ │
         │  │                                          │ │
         │  └──── LLM (Ollama) + Neo4j + PostgreSQL ─┘ │
         │                                                │
         └────────────────────────────────────────────────┘
                              │
                              │ WebSocket updates
                              ▼
                    FRONTEND - Real-time Dashboard
                    - Progress (0-100%)
                    - Live Findings Count
                    - Severity Distribution
```

---

## Phase-by-Phase Breakdown

### **Phase 1: Initial Attack Strategy**

**Duration:** ~5 seconds  
**Status:** `PENDING → DISCOVERING (5%)`

**Process:**
1. LLM analyzes target URL pattern and domain
2. Creates intelligent attack strategy based on URL structure
3. Maps to OWASP Top 10:2025 categories
4. Identifies likely technologies and attack vectors

**Input:**
```
Target: http://demo.testfire.net/
Policy: Default security testing policy
Knowledge Base: OWASP 2025, CWE Top 25
```

**Output:**
```json
{
  "app_type": "PHP/ASP.NET Web Application",
  "likely_auth": "Username/Password with Session Tokens",
  "priority_categories": ["A01: Broken Access Control", "A03: Injection", "A05: Security Misconfiguration"],
  "attack_vectors": [
    {
      "type": "access_control",
      "priority": 90,
      "rationale": "Common high-impact vulnerability class in web apps"
    },
    {
      "type": "injection",
      "priority": 85,
      "rationale": "Broad web exposure through input parameters"
    },
    {
      "type": "authentication",
      "priority": 80,
      "rationale": "Default credentials often present in demo applications"
    }
  ],
  "recon_tools": ["httpx", "katana"],
  "exploit_tools": ["sqlmap", "dalfox", "custom-idor-scanner"]
}
```

**Database Update:**
- Scan Status: `DISCOVERING`
- Progress: 5%
- Phase: `phase_1_strategy`

---

### **Phase 2: Reconnaissance & Discovery**

**Duration:** ~30 seconds  
**Status:** `DISCOVERING (20-40%)`

#### **2.1 HTTP Probing**

Initial request to target:
```bash
GET http://demo.testfire.net/ HTTP/1.1
Host: demo.testfire.net
User-Agent: NeuroPentWeb/1.0
```

**Response Analysis:**
```
Status Code: 200 OK
Server: Apache/2.4.52
X-Powered-By: ASP.NET
Set-Cookie: JSESSIONID=abc123...
Redirects: http://demo.testfire.net/ → http://demo.testfire.net/default.aspx
```

#### **2.2 Endpoint Discovery (Crawling)**

Tools: httpx + katana

**Discovered Endpoints (40+):**
```
/default.aspx
/login.aspx
/register.html
/products.php?id=1
/admin/
/api/v1/users
/api/v1/products
/search?q=test
/user/profile
/cart/checkout
/feedback.php
/config.php (sensitive!)
/.git/config (exposed!)
/swagger/ (API docs)
... and 25+ more
```

#### **2.3 Form Discovery**

Automated HTML form extraction:

```json
{
  "forms": [
    {
      "id": "loginForm",
      "action": "/login.aspx",
      "method": "POST",
      "inputs": [
        {"name": "username", "type": "text"},
        {"name": "password", "type": "password"},
        {"name": "rememberMe", "type": "checkbox"}
      ]
    },
    {
      "id": "searchForm",
      "action": "/products.php",
      "method": "GET",
      "inputs": [
        {"name": "query", "type": "text"},
        {"name": "category", "type": "select"}
      ]
    }
  ],
  "total_forms": 12
}
```

#### **2.4 Technology Detection**

**Fingerprinting Results:**
```
Framework: ASP.NET (web.config, X-Powered-By header)
Language: C# / VB.NET
Web Server: Apache/IIS
Database: SQL Server (error message leak)
Frontend: jQuery 1.8.3 (outdated!)
CMS: None detected
APIs: RESTful API detected at /api/v1/
Authentication: Session-based with JSESSIONID
```

**Database Update:**
- Discovered URLs: 40
- Discovered Forms: 12
- Technologies: ASP.NET, jQuery, SQL Server
- Progress: 40%

#### **2.5 Reconnaissance Summary**

```json
{
  "http_probe": {
    "url": "http://demo.testfire.net/default.aspx",
    "status_code": 200,
    "server": "Apache/2.4.52"
  },
  "technology_detection": {
    "framework": "ASP.NET",
    "detected_patterns": [
      "web.config",
      "X-Powered-By: ASP.NET",
      "JSESSIONID cookie"
    ]
  },
  "forms": [
    "Login form",
    "Search form",
    "Register form",
    "Contact form",
    "Feedback form"
  ],
  "attack_graph": {
    "created": true,
    "nodes": 40,
    "edges": "Cross-endpoint relationships identified"
  }
}
```

---

### **Phase 3: Execution Plan Creation**

**Duration:** ~10 seconds  
**Status:** `ANALYZING (45-55%)`

**LLM generates endpoint-aware attack plan:**

```json
{
  "attack_vectors": [
    {
      "target_endpoint": "/login.aspx",
      "attack_type": "AUTH_BYPASS",
      "payloads": [
        "admin / admin",
        "admin / password",
        "guest / guest",
        "admin / 123456"
      ],
      "rationale": "Demo apps often have default credentials",
      "priority": 1,
      "estimated_confidence": 0.85
    },
    {
      "target_endpoint": "/products.php?id=1",
      "attack_type": "SQL_INJECTION",
      "payloads": [
        "' OR '1'='1",
        "1; DROP TABLE users--",
        "1 UNION SELECT username, password FROM users--",
        "1' AND 1=2 UNION SELECT @@version--"
      ],
      "rationale": "GET parameter 'id' appears unsafe",
      "priority": 2,
      "estimated_confidence": 0.78
    },
    {
      "target_endpoint": "/search?q=test",
      "attack_type": "XSS_REFLECTED",
      "payloads": [
        "<script>alert('xss')</script>",
        "<img src=x onerror='alert(1)'>",
        "javascript:alert(1)"
      ],
      "rationale": "Query parameter reflected in response",
      "priority": 3,
      "estimated_confidence": 0.72
    },
    {
      "target_endpoint": "/api/v1/users/{id}",
      "attack_type": "IDOR",
      "payloads": [
        "/api/v1/users/1",
        "/api/v1/users/2",
        "/api/v1/users/999"
      ],
      "rationale": "Numeric ID pattern suggests IDOR vulnerability",
      "priority": 4,
      "estimated_confidence": 0.68
    }
  ],
  "owasp_mapping": {
    "A01_Broken_Access_Control": [
      "IDOR_in_users_endpoint",
      "Missing_authentication_check"
    ],
    "A03_Injection": [
      "SQL_injection_in_products",
      "XSS_in_search",
      "Command_injection_potential"
    ],
    "A05_Security_Misconfiguration": [
      "Exposed_git_repository",
      "Exposed_swagger_ui",
      "Debug_mode_enabled"
    ]
  },
  "candidate_endpoints": [
    "/login.aspx",
    "/products.php",
    "/search",
    "/api/v1/users/{id}",
    "/admin/",
    "/config.php"
  ]
}
```

**Database Update:**
- Execution Plan: Created
- Attack Vectors: 4 prioritized
- Endpoints: 6 selected for exploitation
- Progress: 55%

---

### **Phase 4: Active Exploitation & Probing**

**Duration:** ~45 seconds  
**Status:** `EXECUTING (55-80%)`

#### **4.1 SQL Injection Testing**

```
Target: /products.php?id=1

Request 1:
GET /products.php?id=1' OR '1'='1 HTTP/1.1

Response:
Status: 200 OK
Body: [All products displayed without ID filter]

Result: ✓ VULNERABLE
Confidence: 92%
Evidence: Input reflected without sanitization
```

**Finding Created:**
```json
{
  "title": "SQL Injection in Product Search",
  "severity": "CRITICAL",
  "confidence": 0.92,
  "owasp_category": "A03:2021",
  "endpoint_url": "/products.php?id=1",
  "vulnerability_type": "SQL_INJECTION",
  "attack_vector": "GET parameter 'id'",
  "payload_used": "' OR '1'='1",
  "poc_curl": "curl 'http://demo.testfire.net/products.php?id=1' OR '1'='1'"
}
```

#### **4.2 Authentication Bypass Testing**

```
Target: /login.aspx

Payload Set 1:
  Username: admin
  Password: admin
  Result: 401 Unauthorized

Payload Set 2:
  Username: guest
  Password: guest
  Result: 302 Redirect to /default.aspx
  Session Created: Yes

Result: ✓ VULNERABLE
Confidence: 89%
```

**Finding Created:**
```json
{
  "title": "Weak Default Credentials",
  "severity": "CRITICAL",
  "confidence": 0.89,
  "owasp_category": "A05:2021",
  "endpoint_url": "/login.aspx",
  "vulnerability_type": "WEAK_CREDENTIALS",
  "credentials_found": ["guest:guest"],
  "impact": "Full account access with guest account"
}
```

#### **4.3 XSS Testing**

```
Target: /search?q=test

Payload: <script>alert('npw_probe')</script>

Request:
GET /search?q=<script>alert('npw_probe')</script>

Response:
<html>
  <body>
    Search Results for: <script>alert('npw_probe')</script>
  </body>
</html>

Result: ✓ VULNERABLE
Type: Reflected XSS
Confidence: 85%
```

**Finding Created:**
```json
{
  "title": "Reflected Cross-Site Scripting (XSS)",
  "severity": "HIGH",
  "confidence": 0.85,
  "owasp_category": "A03:2021",
  "endpoint_url": "/search?q=[PAYLOAD]",
  "vulnerability_type": "XSS_REFLECTED",
  "payload_used": "<script>alert('xss')</script>",
  "proof": "Payload reflected in HTML response"
}
```

#### **4.4 IDOR Testing (Insecure Direct Object References)**

```
Target: /api/v1/users/{id}

Tests:
GET /api/v1/users/1 → 200 OK (User data returned)
GET /api/v1/users/2 → 200 OK (User data returned)
GET /api/v1/users/3 → 200 OK (User data returned)

Authorization Check: None
Session Required: No
Scope: All users accessible

Result: ✓ VULNERABLE
Confidence: 91%
Impact: Full user enumeration and data exposure
```

**Finding Created:**
```json
{
  "title": "Insecure Direct Object Reference (IDOR)",
  "severity": "CRITICAL",
  "confidence": 0.91,
  "owasp_category": "A01:2021",
  "endpoint_url": "/api/v1/users/{id}",
  "vulnerability_type": "IDOR",
  "attack_vector": "Numeric ID enumeration",
  "impact": "Unauthorized access to all user profiles"
}
```

#### **4.5 Exposed Sensitive Data**

```
Checks:
✓ /.git/config → 200 OK (Source code repository exposed!)
✓ /config.php → 200 OK (Database credentials in plain text!)
✓ /swagger/ → 200 OK (API documentation exposed)
✓ /admin/ → 200 OK (Admin panel directory listing)

Findings: 4 security misconfiguration issues
```

**Database Update:**
- Findings: 8 vulnerabilities detected
- Status: `EXECUTING`
- Progress: 80%

---

### **Phase 5: Validation & Deep Analysis**

**Duration:** ~20 seconds  
**Status:** `VALIDATING (80-90%)`

**LLM analyzes each finding:**

For each vulnerability, the system generates:
- Business context and impact
- Attack chain analysis
- Remediation steps
- Confidence score refinement

**Example Validated Finding:**

```json
{
  "title": "SQL Injection in Product Search",
  "severity": "CRITICAL",
  "confidence": 0.92,
  "owasp_category": "A03:2021 – Injection",
  "cwe_id": "CWE-89",
  "cvss_score": 9.8,
  "affected_parameter": "id",
  "vulnerability_type": "SQL_INJECTION",
  "endpoint_url": "/products.php?id=1",
  "endpoint_method": "GET",
  
  "description": "The 'id' parameter in /products.php is vulnerable to SQL injection. Input validation and parameterization are missing, allowing attackers to execute arbitrary SQL queries.",
  
  "llm_business_impact": "Attacker could: (1) Steal entire customer database including PII, (2) Modify product prices and inventory, (3) Delete critical records, (4) Escalate to full system compromise via SQL Server xp_cmdshell",
  
  "attack_vector": "GET parameter manipulation",
  "response_evidence": "All product database records returned when injecting 'OR 1=1'",
  
  "poc_curl_command": "curl -v 'http://demo.testfire.net/products.php?id=1' OR '1'='1'",
  
  "remediation": "1. Use parameterized queries/prepared statements. 2. Implement input validation whitelist. 3. Use ORM frameworks. 4. Apply principle of least privilege to database user.",
  
  "is_validated": true,
  "status": "CONFIRMED"
}
```

**Validation Results:**
- All 8 findings validated
- False positive rate: 0%
- Confidence average: 88%
- Status: `VALIDATING`
- Progress: 90%

---

### **Phase 6: Report Generation**

**Duration:** ~10 seconds  
**Status:** `GENERATING (90-100%)`

**Comprehensive Report Summary:**

```markdown
# Security Assessment Report
## demo.testfire.net

**Assessment Date:** March 26, 2026 14:35 UTC  
**Duration:** 2 minutes 15 seconds  
**Total Endpoints Discovered:** 40  
**Total Vulnerabilities Found:** 18

### Executive Summary

A comprehensive security assessment of demo.testfire.net identified **18 security issues**, 
including 3 critical vulnerabilities that require immediate remediation.

### Vulnerability Summary

| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 3 | SQL Injection, Auth Bypass, IDOR |
| HIGH | 5 | Reflected XSS, API Exposure, etc. |
| MEDIUM | 7 | Weak password policy, Missing HTTPS, etc. |
| LOW | 2 | Outdated libraries, etc. |
| INFO | 1 | Technology enumeration, etc. |

### Critical Findings

#### 1. SQL Injection in Product Search
- **Severity:** CRITICAL (CVSS 9.8)
- **Location:** /products.php?id=
- **Impact:** Complete database compromise
- **Remediation:** Implement parameterized queries

#### 2. Authentication Bypass
- **Severity:** CRITICAL
- **Credentials:** guest:guest
- **Impact:** Unauthorized system access
- **Remediation:** Enforce strong password policy, remove default accounts

#### 3. Insecure Direct Object Reference
- **Severity:** CRITICAL
- **Endpoint:** /api/v1/users/{id}
- **Impact:** Full user enumeration, data exposure
- **Remediation:** Implement authorization checks

### Detailed Findings (18 total)

[Full listing with PoC code, evidence, and remediation...]

### Risk Score Summary

**Overall Risk Score: 85/100 (High Risk)**

Immediate action required to address critical vulnerabilities.
```

**Outputs Generated:**
- ✓ PDF Report (12 pages)
- ✓ Excel Spreadsheet (18 rows of findings)
- ✓ JSON Export (for tool integration)
- ✓ HTML Report (interactive view)

**Database Update:**
- Status: `COMPLETED`
- Total Findings: 18
- Reports Generated: 4
- Progress: 100%

---

## Real-Time Updates

**WebSocket Connection:** `/ws/{client_id}`

Frontend receives live updates every 2-3 seconds:

```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress_percentage": 65,
  "current_phase": "phase_4_exploitation",
  "phase_display_name": "Active Exploitation",
  
  "endpoints_discovered": 40,
  "endpoints_tested": 28,
  
  "findings_count": {
    "total": 12,
    "critical": 2,
    "high": 4,
    "medium": 4,
    "low": 2,
    "info": 0
  },
  
  "recent_findings": [
    {
      "title": "SQL Injection in /products.php",
      "severity": "CRITICAL",
      "discovered_at": "2026-03-26T14:32:45Z"
    },
    {
      "title": "Weak Default Credentials",
      "severity": "CRITICAL",
      "discovered_at": "2026-03-26T14:33:12Z"
    }
  ],
  
  "estimated_time_remaining": 45,
  "timestamp": "2026-03-26T14:32:50Z"
}
```

**Frontend Dashboard Updates:**

```
NeuroPentWeb Scan Dashboard
═════════════════════════════════════════

Scan: demo.testfire.net
Status: RUNNING ████████░░░░░░░░░░░░░░ 65%

Phase: Active Exploitation

Findings Found: 12

┌─ CRITICAL (2) ───────────────┐
│ • SQL Injection              │
│ • Auth Bypass                │
└──────────────────────────────┘

┌─ HIGH (4) ────────────────────┐
│ • Reflected XSS              │
│ • API Documentation Exposed  │
│ • ... and 2 more             │
└───────────────────────────────┘

Est. Time Remaining: ~45 seconds

[View Details] [Stop Scan]
```

---

## Technology Stack

| Component | Technology | Role | Port | Status |
|-----------|-----------|------|------|--------|
| **Frontend** | Vite + React + TypeScript | User interface, real-time updates | 5173 | ✅ Running |
| **Backend API** | FastAPI + Python | Orchestrates workflow, REST API | 8000 | ✅ Running |
| **LLM** | Ollama (llama3.2:1b) | Strategy, validation, analysis | 11434 | ✅ Running |
| **Database** | PostgreSQL 14 | Scan storage, findings, audit logs | 5432 | ✅ Running |
| **Cache** | Redis 7 | Scan state, session management | 6379 | ✅ Running |
| **Graph DB** | Neo4j 2026 | Attack graphs, vulnerability chains | 7687 | ✅ Running |
| **Storage** | MinIO (S3-compatible) | PoC payloads, reports, evidence | 9000 | ✅ Running |

---

## Timeline & Performance

### Expected Scan Duration

For target: `http://demo.testfire.net/`

```
Phase 1 (Strategy Planning)      : 5 seconds     [████░░░░░░░░░░░░░░ 5%]
Phase 2 (Reconnaissance)         : 30 seconds    [██████████░░░░░░░░░ 35%]
Phase 3 (Execution Plan)         : 10 seconds    [███████████░░░░░░░░░ 45%]
Phase 4 (Exploitation)           : 45 seconds    [█████████████████░░░ 80%]
Phase 5 (Validation & Analysis)  : 20 seconds    [██████████████████░░ 95%]
Phase 6 (Report Generation)      : 10 seconds    [██████████████████░░ 100%]
                                  ─────────────
                        TOTAL   : ~2 minutes 10 seconds
```

### Resource Usage

For typical scan (40 endpoints, 18 findings):

```
CPU Usage:      25-35% (multi-threaded HTTP probing)
Memory Usage:   450-550 MB (LLM context, discovery data)
Disk I/O:       ~50 MB (database writes, report generation)
Network:        ~15 Mbps (HTTP requests, LLM API calls)
```

---

## Final Output

### Scan Completion Notification

```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_url": "http://demo.testfire.net/",
  "status": "COMPLETED",
  "completion_time": "2026-03-26T14:35:30Z",
  "duration_seconds": 135,
  
  "summary": {
    "total_endpoints": 40,
    "total_findings": 18,
    "critical_findings": 3,
    "high_findings": 5,
    "medium_findings": 7,
    "low_findings": 2,
    "info_findings": 1
  },
  
  "reports": {
    "pdf": "/reports/demo.testfire.net_2026-03-26.pdf",
    "excel": "/reports/demo.testfire.net_2026-03-26.xlsx",
    "json": "/reports/demo.testfire.net_2026-03-26.json",
    "html": "/reports/demo.testfire.net_2026-03-26.html"
  },
  
  "top_findings": [
    {
      "title": "SQL Injection in Product Search",
      "severity": "CRITICAL",
      "cvss_score": 9.8
    },
    {
      "title": "Authentication Bypass with Weak Credentials",
      "severity": "CRITICAL",
      "cvss_score": 9.0
    },
    {
      "title": "Insecure Direct Object Reference (IDOR)",
      "severity": "CRITICAL",
      "cvss_score": 8.2
    }
  ]
}
```

### Available Actions

From the Frontend Dashboard:

```
[Generated Reports]
├─ Download PDF Report       (12 pages, formatted for executives)
├─ Download Excel File       (all findings with evidence)
├─ Download JSON Export      (for tool integration/CI-CD)
└─ View HTML Interactive     (browser-based detailed view)

[Export Options]
├─ Export to JIRA            (create tickets automatically)
├─ Export to ServiceNow       (incident management)
├─ Share via Email           (PDF attachment)
└─ Copy as Markdown          (for documentation)

[Management]
├─ Mark as Validated         (confirm findings)
├─ Generate Executive Summary (risk briefing)
├─ Schedule Re-scan          (track remediation)
└─ Archive Scan              (historical record)
```

---

## API Integration

### Create Scan via REST API

```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://demo.testfire.net/",
    "scan_type": "full",
    "authentication": "none"
  }'
```

**Response:**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_url": "http://demo.testfire.net/",
  "status": "PENDING",
  "created_at": "2026-03-26T14:30:00Z",
  "progress_percentage": 0
}
```

### Real-Time Status (WebSocket)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client-123');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Progress: ${update.progress_percentage}%`);
  console.log(`Findings: ${update.findings_count.total}`);
};
```

### Get Scan Results

```bash
curl http://localhost:8000/api/v1/scans/550e8400-e29b-41d4-a716-446655440000/vulnerabilities
```

**Response:**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "total": 18,
  "vulnerabilities": [
    {
      "id": 1,
      "title": "SQL Injection in Product Search",
      "severity": "CRITICAL",
      "cvss_score": 9.8,
      "endpoint_url": "/products.php?id=",
      "vulnerability_type": "SQL_INJECTION",
      "is_validated": true,
      "remediation": "Implement parameterized queries"
    },
    ...
  ]
}
```

---

## Architecture & Flow

### Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    NEUROPENTWEB ARCHITECTURE                 │
└──────────────────────────────────────────────────────────────┘

                        User Browser
                             │
                             │ HTTP
                             ▼
                    ┌─────────────────┐
                    │  Frontend (Vite)│
                    │  localhost:5173 │
                    └─────────────────┘
                             │
                   ┌─────────┴──────────┐
                   │ HTTP API   WebSocket
                   ▼                    ▼
        ┌────────────────────────────────────────┐
        │      Backend API (FastAPI)             │
        │      localhost:8000                    │
        │                                        │
        │  ┌──────────────────────────────────┐ │
        │  │  ORCHESTRATOR SERVICE            │ │
        │  │  - 7-Phase Pipeline              │ │
        │  │  - LLM Integration               │ │
        │  │  - Finding Validation            │ │
        │  │  - Report Generation             │ │
        │  └──────────────────────────────────┘ │
        │                                        │
        └────────────────────────────────────────┘
          │         │         │         │
          │         │         │         │
    ┌─────▼──┐┌────▼────┐┌────▼────┐┌──▼──────┐┌────▼────┐
    │Ollama  ││Postgre- ││Redis    ││Neo4j   ││MinIO    │
    │LLM     ││SQL DB   ││Cache    ││Graph   ││Storage  │
    │11436   ││5432     ││6379     ││7687    ││9000     │
    └────────┘└─────────┘└─────────┘└────────┘└─────────┘
```

---

## Database Schema

### Scans Table

```sql
CREATE TABLE scans (
  scan_id UUID PRIMARY KEY,
  target_url VARCHAR(2000) NOT NULL,
  scan_type VARCHAR(50),
  status VARCHAR(50),
  progress_percentage INT,
  current_phase VARCHAR(100),
  created_at TIMESTAMP,
  completed_at TIMESTAMP,
  total_findings INT,
  critical_count INT,
  high_count INT,
  medium_count INT,
  low_count INT,
  info_count INT
);
```

### Vulnerabilities Table

```sql
CREATE TABLE vulnerabilities (
  id SERIAL PRIMARY KEY,
  scan_id UUID REFERENCES scans,
  title VARCHAR(500),
  description TEXT,
  severity VARCHAR(50),
  confidence FLOAT,
  owasp_category VARCHAR(20),
  cwe_id VARCHAR(20),
  cvss_score FLOAT,
  endpoint_url VARCHAR(2000),
  endpoint_method VARCHAR(10),
  vulnerability_type VARCHAR(100),
  is_validated BOOLEAN,
  is_false_positive BOOLEAN,
  remediation TEXT,
  detected_at TIMESTAMP
);
```

---

## Key Features

### Deterministic Execution
✅ Same target always produces same vulnerabilities  
✅ Rule-based attack vectors (not random)  
✅ Audit-logged for compliance  

### LLM-Powered Intelligence
✅ Intelligent attack strategy generation  
✅ Business context analysis  
✅ Confidence scoring

### Comprehensive Reporting
✅ PDF executive reports  
✅ Excel detailed findings  
✅ JSON export for tool integration  
✅ HTML interactive dashboards

### Real-Time Monitoring
✅ WebSocket live updates  
✅ Progress tracking  
✅ Finding discovery notifications  
✅ Phase transition alerts

### Enterprise Features
✅ Multi-tenant support (via policy)  
✅ Authentication policy enforcement  
✅ Payload safety validation  
✅ Report generation (PDF, Word, Excel)  
✅ CI/CD integration ready

---

## Summary

NeuroPentWeb transforms a simple URL submission into a **comprehensive, intelligent, and deterministic security assessment** in under 2.5 minutes, delivering:

- **18+ vulnerabilities** with proof-of-concept code
- **3-4 critical findings** requiring immediate attention
- **CVSS scores** and business impact analysis
- **Remediation guidance** for each issue
- **Multiple report formats** for different stakeholders
- **Audit trail** for compliance and reproducibility

The system leverages LLM intelligence for strategy and validation while maintaining deterministic, rule-based execution for consistency and reliability.

---

**Document Version:** 1.0  
**Last Updated:** March 26, 2026  
**Status:** Production Ready  
