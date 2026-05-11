# Business Requirements Document (BRD)

## Project: RakshAI — Automated Web Application Penetration Testing Platform

---

| Field | Details |
|---|---|
| **Document Version** | 1.0 |
| **Date** | March 18, 2026 |
| **Status** | Draft |
| **Prepared By** | RakshAI Project Team |
| **Classification** | Confidential |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Objectives](#2-business-objectives)
3. [Scope](#3-scope)
4. [Stakeholders](#4-stakeholders)
5. [Business Requirements](#5-business-requirements)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [System Architecture Overview](#8-system-architecture-overview)
9. [User Stories](#9-user-stories)
10. [OWASP Coverage Requirements](#10-owasp-coverage-requirements)
11. [Assumptions & Constraints](#11-assumptions--constraints)
12. [Risks & Mitigations](#12-risks--mitigations)
13. [Out of Scope](#13-out-of-scope)
14. [Glossary](#14-glossary)
15. [Approval](#15-approval)

---

## 1. Executive Summary

### 1.1 Project Overview

**RakshAI** is an enterprise-grade, automated web application penetration testing platform. It automates the full lifecycle of a web application security assessment — from reconnaissance and attack surface mapping through vulnerability detection, proof-of-concept (PoC) generation, validation, and professional report generation.

### 1.2 Problem Statement

Organizations increasingly rely on web applications to deliver business-critical services. Manual penetration testing is:
- **Expensive** — senior security professionals command high day rates
- **Time-consuming** — a full assessment can take days to weeks
- **Inconsistent** — results depend heavily on individual tester expertise
- **Infrequent** — budgets restrict testing to once or twice per year
- **Difficult to audit** — manual testing decisions are opaque and hard to reproduce

### 1.3 Proposed Solution

RakshAI automates the penetration testing workflow using a **deterministic rule-based engine** driven entirely by YAML configuration files. A multi-agent system orchestrates the full assessment lifecycle. An LLM (Ollama, running locally) is used **exclusively** to generate human-readable explanations — ensuring all security decisions are explainable, repeatable, and auditable.

### 1.4 Business Value

| Benefit | Description |
|---------|-------------|
| **Cost Reduction** | Reduce cost per assessment by up to 80% by automating manual effort |
| **Speed** | Compress multi-day assessments to hours |
| **Consistency** | Same rule engine, same decisions — every time |
| **Coverage** | Full OWASP Top 10:2025 coverage on every scan |
| **Auditability** | Every attack decision is traceable to a YAML rule |
| **Frequency** | Enable continuous security testing in CI/CD pipelines |

---

## 2. Business Objectives

| # | Objective | Success Metric |
|---|-----------|----------------|
| BO-01 | Automate full web application pentest lifecycle | End-to-end scan completes without human intervention |
| BO-02 | Achieve full OWASP Top 10:2025 coverage | All 10 OWASP categories tested on every scan |
| BO-03 | Deliver explainable, auditable security decisions | 100% of decisions traceable to YAML rules |
| BO-04 | Reduce false positives in findings | Validation agent reduces FP rate to < 10% |
| BO-05 | Provide professional-grade security reports | Reports exportable in PDF, DOCX, XML formats |
| BO-06 | Enable integration into enterprise CI/CD pipelines | API-accessible; webhook support for pipeline triggers |
| BO-07 | Support concurrent enterprise-scale scanning | System handles ≥ 10 concurrent scans |
| BO-08 | Ensure safe operation in production environments | Safety enforcer blocks all destructive payloads |

---

## 3. Scope

### 3.1 In Scope

- Automated reconnaissance and endpoint discovery
- Rule-based attack surface mapping (OWASP Top 10:2025)
- Automated test case selection, payload binding, and execution
- Vulnerability detection, PoC generation, and validation
- Real-time scan progress monitoring via web UI
- Report generation (PDF, DOCX, XML)
- User authentication and role-based access control
- Docker-based deployment
- REST API for integration
- Prometheus/Grafana monitoring

### 3.2 Out of Scope

- Network-layer penetration testing (port scanning, OS fingerprinting)
- Mobile application testing
- Social engineering or phishing simulations
- Physical security assessment
- Manual override of attack decisions during scan execution
- Zero-day exploit creation

---

## 4. Stakeholders

| Role | Responsibility | Involvement |
|------|---------------|-------------|
| **Security Team / Pentesters** | Primary users; run scans, review findings | High |
| **Development Teams** | Receive reports; remediate vulnerabilities | Medium |
| **CISO / Security Management** | Approve scope, review executive reports | Medium |
| **DevOps / Platform Team** | Deploy and maintain the infrastructure | High |
| **Compliance & Audit Teams** | Use reports for compliance evidence | Medium |
| **Product Owner** | Prioritize features and roadmap | High |

---

## 5. Business Requirements

### BR-01: Automated End-to-End Penetration Testing
The system shall automate the complete penetration testing workflow without requiring manual intervention between phases: reconnaissance → attack planning → execution → validation → reporting.

### BR-02: Deterministic, Auditable Security Decisions
All vulnerability testing decisions (which tests to run, which payloads to use) shall be driven entirely by YAML-defined rules. No machine learning model shall make security decisions. Every decision shall be traceable to a specific YAML rule.

### BR-03: OWASP Top 10:2025 Full Coverage
The platform shall test every scanned application against all 10 OWASP Top 10:2025 vulnerability categories.

### BR-04: Safe Operation in Production Environments
The platform shall include a Safety Enforcer component that prevents any destructive, irreversible, or data-corrupting payloads from being executed against production targets.

### BR-05: Real-Time Monitoring
Users shall be able to monitor the progress of active scans in real time via a web-based dashboard, including current agent activity, discovered endpoints, and live findings.

### BR-06: Professional Report Generation
The system shall generate professional security assessment reports in multiple formats (PDF, DOCX, XML) including executive summaries, technical findings, CVSS scores, remediation guidance, and proof-of-concept details.

### BR-07: Enterprise Multi-Tenancy & Access Control
The platform shall support multiple users with role-based access control ensuring scan data, findings, and reports are properly isolated per organization/team.

### BR-08: API-First Integration
All platform capabilities shall be accessible via a documented REST API, enabling integration with CI/CD pipelines, ticketing systems, and security information & event management (SIEM) platforms.

### BR-09: Knowledge Base Maintainability
Security rules, test cases, and payloads shall be stored as human-readable YAML files and updatable without requiring code changes or platform redeployment.

### BR-10: Local LLM for Data Privacy
The LLM used for generating explanations shall run locally (Ollama) to ensure sensitive target application data never leaves the organization's infrastructure.

---

## 6. Functional Requirements

### 6.1 Scan Management

| ID | Requirement |
|----|-------------|
| FR-001 | Users shall be able to create a new scan by specifying a target URL and scan policy |
| FR-002 | Users shall be able to start, pause, cancel, and delete scans |
| FR-003 | The system shall validate that the target URL is within the authorized scope before scanning |
| FR-004 | Users shall be able to view a list of all scans with status, target, and finding counts |
| FR-005 | The system shall track scan status through defined states: `PENDING → PLANNING → DISCOVERING → ATTACKING → VALIDATING → AGGREGATING → COMPLETED / FAILED` |

### 6.2 Reconnaissance & Discovery Agent

| ID | Requirement |
|----|-------------|
| FR-010 | The system shall crawl the target web application using Scrapy and Playwright |
| FR-011 | The recon agent shall discover all accessible HTTP/HTTPS endpoints |
| FR-012 | The system shall identify parameters (query, body, path, header) for each endpoint |
| FR-013 | The system shall classify parameters by type (id, url, file, token, password, etc.) |
| FR-014 | Discovered endpoints shall be stored in a Neo4j graph database as an attack graph |

### 6.3 Rule Engine

| ID | Requirement |
|----|-------------|
| FR-020 | The context normalizer shall transform raw discovery output into a standardized endpoint schema |
| FR-021 | The OWASP mapper shall assign applicable OWASP Top 10:2025 categories to each endpoint using deterministic rules |
| FR-022 | The test case evaluator shall select applicable test cases from the YAML knowledge base |
| FR-023 | The payload binder shall select and bind payloads from the YAML payload library for each test case |
| FR-024 | The safety enforcer shall block any payload tagged as destructive when the scan policy is set to `PRODUCTION` |
| FR-025 | The validator selector shall choose appropriate detection validators for each test case |
| FR-026 | The attack plan generator shall assemble the final executable attack plan |

### 6.4 Execution & Detection Agent

| ID | Requirement |
|----|-------------|
| FR-030 | The executor shall send HTTP requests with attack payloads to the target |
| FR-031 | The executor shall respect rate limiting configured in the scan policy |
| FR-032 | The executor shall support configurable concurrency (max parallel requests) |
| FR-033 | The system shall detect vulnerability indicators in HTTP responses using YAML validator rules |
| FR-034 | All HTTP requests and responses shall be logged for audit purposes |

### 6.5 PoC Generation & Validation

| ID | Requirement |
|----|-------------|
| FR-040 | For each detected vulnerability, the PoC generator shall create a reproducible proof-of-concept |
| FR-041 | The validation agent shall re-execute findings to confirm they are genuine vulnerabilities |
| FR-042 | The validation agent shall apply false positive filters defined in YAML test cases |

### 6.6 Reporting

| ID | Requirement |
|----|-------------|
| FR-050 | The system shall generate reports in PDF, DOCX, and XML formats |
| FR-051 | Reports shall include: executive summary, CVSS scores, OWASP categories, technical details, PoC, and remediation guidance |
| FR-052 | The LLM (Ollama) shall generate human-readable explanations for each finding |
| FR-053 | Reports shall be downloadable via the web UI and API |

### 6.7 Web UI

| ID | Requirement |
|----|-------------|
| FR-060 | The UI shall provide a Dashboard with scan statistics and severity breakdown |
| FR-061 | The UI shall display real-time scan progress via WebSocket connection |
| FR-062 | The UI shall provide an Attack Surface page showing discovered endpoints |
| FR-063 | The UI shall provide a Vulnerabilities page with filtering by severity, OWASP category, and status |
| FR-064 | The UI shall display full vulnerability details including PoC, CVSS score, and remediation steps |
| FR-065 | The UI shall require authentication (JWT-based login) |

### 6.8 API

| ID | Requirement |
|----|-------------|
| FR-070 | The backend shall expose a RESTful API under `/api/v1/` |
| FR-071 | The API shall include OpenAPI/Swagger documentation |
| FR-072 | All API endpoints shall require authentication (Bearer token) |
| FR-073 | The API shall support webhook callbacks for scan completion events |

---

## 7. Non-Functional Requirements

### 7.1 Performance

| ID | Requirement |
|----|-------------|
| NFR-001 | The system shall support a minimum of 10 concurrent active scans |
| NFR-002 | API response time for non-scanning endpoints shall not exceed 500ms (p95) |
| NFR-003 | WebSocket updates shall be delivered within 2 seconds of scan state changes |
| NFR-004 | Report generation shall complete within 60 seconds for a standard assessment |

### 7.2 Reliability

| ID | Requirement |
|----|-------------|
| NFR-010 | The system shall achieve 99.5% uptime for the web UI and API |
| NFR-011 | A failed agent shall not terminate the entire scan; the coordinator shall retry or fail gracefully |
| NFR-012 | Scan state shall be persisted to the database so scans survive system restarts |

### 7.3 Security

| ID | Requirement |
|----|-------------|
| NFR-020 | All passwords shall be hashed using bcrypt |
| NFR-021 | API sessions shall be managed via short-lived JWT tokens |
| NFR-022 | All inter-service communication shall use TLS in production |
| NFR-023 | Sensitive configuration (API keys, DB passwords) shall be managed via environment variables / secrets management |
| NFR-024 | The system shall log all authentication events and security-relevant actions |

### 7.4 Scalability

| ID | Requirement |
|----|-------------|
| NFR-030 | The architecture shall support horizontal scaling of the backend services via Kubernetes |
| NFR-031 | The Celery task queue shall allow adding worker nodes without downtime |

### 7.5 Maintainability

| ID | Requirement |
|----|-------------|
| NFR-040 | Security rules, payloads, and test cases shall be updatable via YAML file changes without code deployment |
| NFR-041 | Backend code shall maintain ≥ 95% unit test coverage |
| NFR-042 | All APIs shall be documented; all public functions shall include docstrings |

### 7.6 Compliance

| ID | Requirement |
|----|-------------|
| NFR-050 | The platform shall only be used against targets for which explicit written authorization has been obtained |
| NFR-051 | Scan reports shall be suitable for use as evidence in compliance assessments (ISO 27001, SOC 2, PCI-DSS) |
| NFR-052 | Audit logs shall be retained for a minimum of 12 months |

---

## 8. System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Web Browser (User)                   │
│           React 18 + TypeScript + Tailwind CSS           │
│         (Dashboard, Scans, Vulnerabilities, Reports)     │
└──────────────────────────┬──────────────────────────────┘
                           │ REST API + WebSocket
┌──────────────────────────▼──────────────────────────────┐
│                  FastAPI Backend (Python 3.11)           │
│   ┌─────────────┐   ┌──────────────┐  ┌─────────────┐  │
│   │ Coordinator │   │  Rule Engine  │  │   REST API  │  │
│   │   Agent     │   │  (7 Comps)   │  │   /api/v1   │  │
│   └──────┬──────┘   └──────┬───────┘  └─────────────┘  │
│          │ Redis pub/sub    │                            │
│   ┌──────▼──────────────────▼────────────────────────┐  │
│   │  Recon Agent │ Strategy │ Executor │ PoC │ Valid  │  │
│   └──────────────────────────────────────────────────┘  │
└─────────┬─────────────┬──────────────┬──────────────────┘
          │             │              │
   ┌──────▼──┐   ┌──────▼──┐   ┌──────▼──┐
   │PostgreSQL│   │  Redis  │   │  Neo4j  │
   │(scan data)│  │(queue)  │   │(graph)  │
   └──────────┘   └─────────┘   └─────────┘
          │
   ┌──────▼──┐   ┌──────────┐
   │ChromaDB │   │  Ollama  │
   │(vectors)│   │  (LLM)   │
   └─────────┘   └──────────┘
```

### Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript 5, Vite, Tailwind CSS, TanStack Query |
| Backend | Python 3.11, FastAPI, Celery, SQLAlchemy, Alembic |
| Databases | PostgreSQL 15 (relational), Redis 7 (cache/queue), Neo4j (graph), ChromaDB (vector) |
| LLM | Ollama (local, open-source models) |
| Web Scraping | Scrapy, Playwright, httpx, BeautifulSoup |
| Infrastructure | Docker, Docker Compose, Kubernetes, GitHub Actions |
| Monitoring | Prometheus, Grafana, structlog |
| Security | JWT (python-jose), bcrypt (passlib), TLS |

---

## 9. User Stories

### Security Analyst

| ID | Story |
|----|-------|
| US-01 | As a security analyst, I want to submit a target URL and start an automated scan so that I can identify vulnerabilities without manual testing effort |
| US-02 | As a security analyst, I want to monitor scan progress in real time so that I can understand what the system is testing |
| US-03 | As a security analyst, I want to view all discovered vulnerabilities sorted by severity so that I can prioritize remediation |
| US-04 | As a security analyst, I want to view full PoC details for each vulnerability so that I can verify and reproduce the finding |
| US-05 | As a security analyst, I want to download a professional PDF report so that I can share findings with developers and management |

### Development Team

| ID | Story |
|----|-------|
| US-10 | As a developer, I want to receive clear remediation guidance for each vulnerability so that I know exactly how to fix the issue |
| US-11 | As a developer, I want to trigger a scan via API from our CI/CD pipeline so that security testing is automated on every release |

### CISO / Management

| ID | Story |
|----|-------|
| US-20 | As a CISO, I want an executive summary report showing risk posture so that I can make informed security investment decisions |
| US-21 | As a CISO, I want audit logs of all scan activity so that I can demonstrate due diligence to auditors |

### DevOps / Platform Team

| ID | Story |
|----|-------|
| US-30 | As a DevOps engineer, I want to deploy the platform using Docker Compose so that setup is fast and reproducible |
| US-31 | As a DevOps engineer, I want Prometheus metrics exposed so that I can monitor platform health in Grafana |

---

## 10. OWASP Coverage Requirements

The platform **must** cover all OWASP Top 10:2025 categories on every scan:

| Category | ID | Attack Types Covered |
|----------|----|---------------------|
| Broken Access Control | A01 | IDOR, Forced Browsing, Path Traversal, Privilege Escalation |
| Security Misconfiguration | A02 | Default Configs, Verbose Errors, Missing Security Headers |
| Software Supply Chain | A03 | Dependency Scanning, Third-party Component Analysis |
| Cryptographic Failures | A04 | Weak Encryption, TLS Issues, Exposed Secrets |
| Injection | A05 | SQL Injection, NoSQL Injection, XSS, XXE, Command Injection |
| Insecure Design | A06 | Business Logic Flaws, State-Changing GETs, Logic Bypass |
| Authentication Failures | A07 | Brute Force, Weak Passwords, Session Management Issues |
| Software & Data Integrity | A08 | Unsigned Updates, Integrity Validation Failures |
| Security Logging Failures | A09 | Missing Logs on Auth Events, Unmonitored State Changes |
| Server-Side Request Forgery | A10 | SSRF via URL Params, Webhook Abuse, Internal Service Access |

---

## 11. Assumptions & Constraints

### Assumptions

| # | Assumption |
|---|------------|
| A-01 | Users have explicit written authorization from target application owners before initiating scans |
| A-02 | Target web applications are accessible from the system running RakshAI |
| A-03 | Ollama with a compatible LLM model is installed and running locally |
| A-04 | Docker Desktop or Docker Engine is available for deployment |
| A-05 | PostgreSQL, Redis, and Neo4j are available (via Docker Compose or external services) |
| A-06 | The YAML knowledge base is maintained and updated by the security team as new threats emerge |

### Constraints

| # | Constraint |
|---|------------|
| C-01 | The LLM **must** run locally (Ollama) — cloud LLM APIs are not permitted for data privacy reasons |
| C-02 | All security decisions **must** be deterministic and YAML-rule-driven — no ML models for attack planning |
| C-03 | Destructive payloads (data deletion, system corruption) are blocked in `PRODUCTION` scan mode |
| C-04 | The platform will not automatically exploit vulnerabilities beyond controlled PoC confirmation |
| C-05 | Platform must be deployable on Windows (PowerShell scripts provided) and Linux |

---

## 12. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| R-01 | Scans against unauthorized targets cause legal liability | Medium | Critical | Enforce scope validation; require target authorization acknowledgement at scan creation |
| R-02 | False positives damage credibility | High | High | Validation agent re-confirms all findings; false positive filters in YAML test cases |
| R-03 | YAML knowledge base becomes outdated | Medium | High | Modular YAML structure allows updates without code changes; establish regular review cycle |
| R-04 | LLM (Ollama) produces inaccurate explanations | Medium | Medium | LLM is used for explanation only — never for attack logic; security team reviews reports |
| R-05 | Concurrent scans overload target application | Medium | High | Rate limiting enforced per scan; configurable delays between requests |
| R-06 | Neo4j or Redis failure disrupts scanning | Low | High | Service health checks; graceful degradation; scan state persisted in PostgreSQL |
| R-07 | Sensitive finding data is exposed | Low | Critical | Authentication required for all API endpoints; data encrypted at rest and in transit |

---

## 13. Out of Scope

The following items are explicitly **not** in scope for this project:

- Network penetration testing (e.g., nmap, port scanning, OS fingerprinting)
- Mobile application security testing (iOS/Android)
- Social engineering, phishing, or human factor testing
- Physical security assessments
- Cloud infrastructure security audits (AWS/Azure/GCP configuration review)
- Manual override of attack execution mid-scan
- Automatic remediation of discovered vulnerabilities
- Zero-day exploit research or weaponization

---

## 14. Glossary

| Term | Definition |
|------|-----------|
| **Agent** | An autonomous software component responsible for a specific phase of the penetration test lifecycle |
| **Attack Graph** | A Neo4j graph database structure representing discovered endpoints, planned attacks, and their relationships |
| **Attack Plan** | The final executable test plan assembled by the Rule Engine's Attack Plan Generator |
| **BRD** | Business Requirements Document |
| **CVSS** | Common Vulnerability Scoring System — standardized vulnerability severity scoring |
| **CWE** | Common Weakness Enumeration — a community-developed list of software security weaknesses |
| **Deterministic** | Producing the same output for the same input every time; no randomness or ML inference |
| **IDOR** | Insecure Direct Object Reference — an access control attack that manipulates object identifiers |
| **Knowledge Base** | The collection of YAML files containing payloads, test cases, validators, and OWASP mappings |
| **LLM** | Large Language Model — used in this project exclusively for generating human-readable explanations |
| **Ollama** | An open-source tool for running LLMs locally |
| **OWASP** | Open Web Application Security Project — a non-profit producing security standards and guidance |
| **Payload** | A specific attack string or data used to probe an endpoint for vulnerabilities |
| **PoC** | Proof of Concept — a reproducible demonstration that a vulnerability exists and is exploitable |
| **Rule Engine** | The 7-component deterministic decision system that maps endpoints to test cases and payloads |
| **Safety Enforcer** | The rule engine component that blocks destructive payloads in production scan mode |
| **SSRF** | Server-Side Request Forgery — attacker causes the server to make requests to unintended targets |
| **Validator** | A detection rule that inspects HTTP responses to confirm the presence of a vulnerability |

---

## 15. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| CISO / Security Lead | | | |
| Technical Lead | | | |
| DevOps Lead | | | |
| QA Lead | | | |

---

*This document is subject to change. All changes must be reviewed and re-approved by the relevant stakeholders.*

*© 2026 RakshAI Project Team. All Rights Reserved.*
