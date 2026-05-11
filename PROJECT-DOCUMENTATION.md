# NeuroPentWeb - Complete Project Documentation

**Version:** 2.0  
**Last Updated:** February 6, 2026  
**Status:** Production-Ready  

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Core Architecture](#core-architecture)
3. [Multi-Agent System](#multi-agent-system)
4. [Rule Engine (The Brain)](#rule-engine-the-brain)
5. [Knowledge Base](#knowledge-base)
6. [Technology Stack](#technology-stack)
7. [Database Schema](#database-schema)
8. [API Reference](#api-reference)
9. [Frontend Application](#frontend-application)
10. [Infrastructure & DevOps](#infrastructure--devops)
11. [Scan Execution Flow](#scan-execution-flow)
12. [Security Features](#security-features)
13. [Installation & Setup](#installation--setup)
14. [Configuration](#configuration)
15. [Development Guide](#development-guide)
16. [Deployment](#deployment)
17. [Troubleshooting](#troubleshooting)

---

## Project Overview

### What is NeuroPentWeb?

**NeuroPentWeb** is an enterprise-grade automated web application penetration testing platform that uses a **100% deterministic, rule-based approach** for security testing. Unlike AI-powered tools that rely on machine learning for security decisions, NeuroPentWeb uses YAML-driven rules for complete explainability, repeatability, and auditability.

### Core Principles

#### 🎯 NO MACHINE LEARNING for Security Decisions
- **All security logic** is defined in YAML configuration files
- Fully **explainable** and **auditable** decision-making
- **Deterministic** and **repeatable** test results
- LLM usage **strictly limited** to generating human-readable report explanations

#### 🛡️ Safety First
- Built-in **Safety Enforcer** blocks destructive payloads
- Environment-aware testing (production vs staging vs dev)
- Payload risk classification (Safe/Low/Medium/High)
- Respects scope boundaries and rate limits

#### 📊 OWASP Top 10:2025 Native
- Designed for the latest OWASP framework
- Complete CWE mapping for vulnerabilities
- CVSS v3.1 scoring
- Compliance-ready reporting

### Key Features

✅ **5 Specialized AI Agents** - Discovery, Detection, PoC Generation, Validation, Reporting  
✅ **7-Component Rule Engine** - Deterministic attack planning pipeline  
✅ **96+ Test Case Files** - Comprehensive OWASP Top 10:2025 coverage  
✅ **~1000+ Payloads** - Context-aware payload databases  
✅ **Safety Enforcer** - Critical component blocking destructive operations  
✅ **Real-time WebSocket** - Live scan progress updates  
✅ **Multi-format Reports** - XML, JSON, HTML, PDF with LLM explanations  
✅ **Horizontal Scalability** - Celery distributed task queue  
✅ **Production-Ready** - Docker containerization, monitoring, logging  

---

## Core Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│          (React + TypeScript + WebSocket + TailwindCSS)         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│                    (Python 3.11+ / Async)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ REST API     │  │  WebSocket   │  │  Prometheus  │         │
│  │ Endpoints    │  │  Manager     │  │  Metrics     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────┬────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ↓              ↓              ↓
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ PostgreSQL  │  │    Redis     │  │   Ollama     │
│  Database   │  │ Cache/Queue  │  │  (LLM)       │
└─────────────┘  └──────────────┘  └──────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CELERY TASK QUEUE                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   5 SPECIALIZED AGENTS                     │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │  │
│  │  │Discovery│→│Detection│→│  PoC   │→│Validate│→│ Report │ │  │
│  │  │ Agent   │ │ Agent   │ │  Gen   │ │ Agent  │ │  Gen   │ │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│               7-COMPONENT RULE ENGINE (THE BRAIN)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Context Normalizer                                     │  │
│  │ 2. OWASP Mapper                                           │  │
│  │ 3. Test Case Evaluator                                    │  │
│  │ 4. Payload Binder                                         │  │
│  │ 5. Safety Enforcer ⚠️ CRITICAL                            │  │
│  │ 6. Validator Selector                                     │  │
│  │ 7. Attack Plan Generator                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│              YAML KNOWLEDGE BASE (Intelligence)                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │  Test Cases  │ │   Payloads   │ │  Validators  │           │
│  │  96+ files   │ │  ~1000+ DB   │ │   6+ files   │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│  ┌──────────────┐ ┌──────────────┐                            │
│  │   Metadata   │ │   Workflows  │                            │
│  │    OWASP     │ │   Security   │                            │
│  │  CWE, CVSS   │ │   Patterns   │                            │
│  └──────────────┘ └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### Design Patterns

- **Multi-Agent Architecture** - Specialized agents for different phases
- **Pipeline Pattern** - 7-stage rule engine pipeline
- **Repository Pattern** - Database access abstraction
- **Dependency Injection** - FastAPI dependencies
- **Pub/Sub** - WebSocket real-time updates
- **Task Queue** - Celery distributed tasks
- **YAML-Driven Configuration** - Externalized security logic

---

## Multi-Agent System

The platform uses **5 specialized Celery task agents** that work together in sequence.

### Agent 1: Discovery Agent
**File:** `backend/app/agents/discovery.py`  
**Task Name:** `app.agents.discovery.discover_endpoints`

#### Purpose
Find and map the complete attack surface of the target application.

#### Technologies
- **Playwright** - JavaScript-rendered sites, SPA applications
- **HTTP Client (httpx)** - Static HTML crawling
- **BeautifulSoup** - HTML parsing and form extraction

#### Capabilities
- Deep crawling with configurable depth
- JavaScript execution and interaction
- Form detection with parameter extraction
- API endpoint discovery
- Query parameter identification
- Cookie and header analysis
- Smart scoping (stays within domain)
- Respects robots.txt (configurable)

#### Output
```json
{
  "endpoints": [
    {
      "url": "https://example.com/login",
      "method": "POST",
      "parameters": ["username", "password"],
      "endpoint_type": "form",
      "requires_auth": false,
      "discovery_method": "playwright_form"
    }
  ]
}
```

### Agent 2: Detection Agent
**File:** `backend/app/agents/detection.py`  
**Task Name:** `app.agents.detection.detect_vulnerabilities`

#### Purpose
Execute attack plans and detect security vulnerabilities using rule-based validation.

#### Process Flow
```
1. Receive attack plan from Rule Engine
2. For each test in plan:
   a. Send baseline request (no payload)
   b. Send attack request (with payload)
   c. Capture full request/response
   d. Apply validators to response
   e. Compare baseline vs attack
   f. Calculate confidence score
3. Record vulnerabilities in database
4. Send WebSocket updates
```

#### Features
- Rate limiting (configurable requests/second)
- Request timeout handling
- Retry logic with exponential backoff
- Concurrent test execution (configurable)
- Response caching
- Evidence collection (request/response pairs)

#### Validators Applied
- SQL error pattern matching
- XSS reflection detection
- Authentication bypass indicators
- Status code analysis
- Response time comparison (time-based attacks)
- Data leakage detection

### Agent 3: PoC Generation Agent
**File:** `backend/app/agents/poc_generation.py`  
**Task Name:** `app.agents.poc_generation.generate_poc`

#### Purpose
Create proof-of-concept exploits for confirmed vulnerabilities.

#### Generated Formats

**1. cURL Command**
```bash
curl -X POST https://example.com/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\'' OR '\''1'\''='\''1","password":"anything"}'
```

**2. Python Script**
```python
import requests

url = "https://example.com/login"
payload = {"username": "admin' OR '1'='1", "password": "anything"}
response = requests.post(url, json=payload)
print(response.text)
```

**3. Manual Reproduction Steps**
```
1. Navigate to https://example.com/login
2. Enter username: admin' OR '1'='1
3. Enter password: anything
4. Click "Login"
5. Observe: Successful authentication bypass
```

#### Safety Features
- Marks destructive PoCs with ⚠️ warnings
- Includes environment restrictions
- Provides safe testing alternatives

### Agent 4: Validation Agent
**File:** `backend/app/agents/validation.py`  
**Task Name:** `app.agents.validation.validate_finding`

#### Purpose
Reduce false positives through reproducibility testing and confidence scoring.

#### Validation Process
```
1. Re-execute vulnerability (3 attempts)
2. For each attempt:
   - Send baseline request
   - Send attack request
   - Compare responses
   - Check for consistency
3. Calculate final confidence score:
   - 3/3 reproductions = 1.0 (High confidence)
   - 2/3 reproductions = 0.66 (Medium confidence)
   - 1/3 reproductions = 0.33 (Low confidence)
   - 0/3 reproductions = 0.0 (False positive)
4. Update vulnerability record
```

#### Confidence Factors
- **Response consistency** - Same indicators across attempts
- **Baseline comparison** - Clear difference from baseline
- **Validator agreement** - Multiple validators confirm
- **Payload variation** - Multiple payloads trigger same result

#### False Positive Filters
- Generic error messages (excluded)
- Expected status codes (404, 403 are normal)
- WAF/rate limiting responses
- Timeout variations

### Agent 5: Report Generation Agent
**File:** `backend/app/agents/report_generation.py`  
**Task Name:** `app.agents.report_generation.generate_report`

#### Purpose
Generate comprehensive security reports with LLM-powered explanations.

#### Report Formats

**1. XML Format**
```xml
<?xml version="1.0"?>
<security_report>
  <scan_info>
    <target>https://example.com</target>
    <date>2026-02-06</date>
  </scan_info>
  <vulnerabilities>
    <vulnerability>
      <title>SQL Injection in Login</title>
      <severity>CRITICAL</severity>
      <cvss>9.8</cvss>
      <owasp>A05-2025</owasp>
      <cwe>CWE-89</cwe>
      <!-- Full details -->
    </vulnerability>
  </vulnerabilities>
</security_report>
```

**2. JSON Format**
```json
{
  "scan_info": {
    "target": "https://example.com",
    "date": "2026-02-06"
  },
  "vulnerabilities": [
    {
      "title": "SQL Injection in Login",
      "severity": "CRITICAL",
      "cvss": 9.8
    }
  ]
}
```

**3. HTML Format**
- Executive summary
- Findings table with severity indicators
- Detailed vulnerability sections
- PoC code blocks with syntax highlighting
- Remediation recommendations
- Interactive charts

**4. PDF Format** (Future)
- Professional formatting
- Company branding
- Chart embeddings
- Executive-ready

#### LLM Integration (Ollama)
```python
# Generate human-readable explanation
explanation = ollama_client.generate(
    model="llama2",
    prompt=f"""Explain this SQL injection vulnerability:
    
    URL: {vuln.url}
    Payload: {vuln.payload}
    Evidence: {vuln.evidence}
    
    Provide:
    1. What happened
    2. Why it's dangerous
    3. How to fix it
    4. Business impact
    """
)
```

#### Report Sections
1. **Executive Summary** - High-level overview for management
2. **Vulnerability Details** - Technical findings
3. **Risk Assessment** - CVSS scores, severity distribution
4. **Evidence** - Request/response pairs, screenshots
5. **Proof of Concept** - Reproduction steps
6. **Remediation** - Fix recommendations with code examples
7. **Compliance Mapping** - OWASP, CWE, NIST references
8. **Appendices** - Methodology, tools used, scope

---

## Rule Engine (The Brain)

The **7-component rule engine** is the core intelligence of NeuroPentWeb. It's entirely **YAML-driven** for complete explainability.

### Pipeline Overview

```
Discovery Output
       ↓
[1] Context Normalizer - Standardize format
       ↓
[2] OWASP Mapper - Categorize endpoint
       ↓
[3] Test Case Evaluator - Select applicable tests
       ↓
[4] Payload Binder - Bind payloads to parameters
       ↓
[5] Safety Enforcer - Filter destructive payloads ⚠️
       ↓
[6] Validator Selector - Choose detection validators
       ↓
[7] Attack Plan Generator - Assemble final plan
       ↓
Attack Plan (JSON)
```

### Component 1: Context Normalizer
**File:** `backend/app/rule_engine/context_normalizer.py`

#### Purpose
Transform raw discovery output into a standardized format for downstream processing.

#### Input
```python
{
    "url": "https://example.com/api/users?id=123",
    "method": "GET",
    "raw_params": {"id": "123"},
    "raw_headers": {"Cookie": "session=abc"}
}
```

#### Output
```python
{
    "url": "https://example.com/api/users",
    "method": "GET",
    "parameters": {
        "query": {"id": {"value": "123", "type": "numeric"}},
        "cookies": {"session": {"value": "abc", "type": "string"}},
        "headers": {},
        "body": {}
    },
    "metadata": {
        "endpoint_type": "api",
        "has_auth": true,
        "technology": "rest",
        "injectable_params": ["id", "session"]
    }
}
```

#### Normalization Tasks
- Parse URLs into components
- Classify parameter types (string, numeric, boolean)
- Detect authentication requirements
- Identify technology stack (REST, GraphQL, SOAP)
- Extract injectable injection points
- Standardize HTTP headers

### Component 2: OWASP Mapper
**File:** `backend/app/rule_engine/owasp_mapper.py`

#### Purpose
Map endpoints to applicable OWASP Top 10:2025 categories using YAML rules.

#### Knowledge Base File
`knowledge-base/metadata/owasp_comprehensive.yaml`

#### Mapping Logic
```yaml
# Example mapping rule
endpoint_patterns:
  - pattern: "/login|/auth|/signin"
    method: "POST"
    parameters: ["username", "password"]
    maps_to:
      - "A07" # Authentication Failures
      - "A05" # Injection (SQL in auth)
      
  - pattern: "/api/.*"
    method: "GET"
    parameters: ["id", "user_id"]
    maps_to:
      - "A01" # Broken Access Control (IDOR)
```

#### Output
```python
{
    "endpoint": "https://example.com/login",
    "owasp_categories": [
        "A05-injection",
        "A07-auth-failures"
    ],
    "confidence": 0.95
}
```

### Component 3: Test Case Evaluator
**File:** `backend/app/rule_engine/test_case_evaluator.py`

#### Purpose
Select applicable test cases from the knowledge base based on OWASP categories and endpoint characteristics.

#### Knowledge Base
- **96+ YAML test case files** in `knowledge-base/test-cases/`
- Organized by OWASP category
- Each file contains 8-24 test cases

#### Selection Criteria
```python
def select_tests(endpoint, owasp_categories):
    applicable_tests = []
    
    for category in owasp_categories:
        # Load test cases for category
        test_files = load_test_cases(category)
        
        for test in test_files:
            if matches_endpoint(test, endpoint):
                # Prioritize by severity
                priority = calculate_priority(test)
                applicable_tests.append({
                    "test": test,
                    "priority": priority,
                    "category": category
                })
    
    # Sort by priority
    return sorted(applicable_tests, key=lambda x: x['priority'], reverse=True)
```

#### Matching Logic
- URL pattern matching
- HTTP method compatibility
- Parameter availability
- Authentication requirements
- Technology stack compatibility

#### Example Test Case
```yaml
# knowledge-base/test-cases/A05-injection/sql-injection.yaml
- id: "SQLI-001"
  name: "Authentication Bypass - Basic"
  method: "POST"
  endpoint_pattern: "/login|/auth"
  required_parameters: ["username", "password"]
  severity: "CRITICAL"
  owasp: "A05"
  cwe: "CWE-89"
  payloads_ref: "injection/sql-auth-bypass"
  validators: ["sql_errors", "auth_indicators"]
```

### Component 4: Payload Binder
**File:** `backend/app/rule_engine/payload_binder.py`

#### Purpose
Bind context-appropriate payloads from the payload database to endpoint parameters.

#### Knowledge Base
- **~1000+ payloads** in `knowledge-base/payloads/`
- Organized by attack type
- Context-aware selection

#### Payload Categories
```
payloads/
├── injection/
│   ├── sql-injection.yaml (300+ payloads)
│   ├── xss.yaml (100+ payloads)
│   ├── command-injection.yaml (80+ payloads)
│   ├── ldap-injection.yaml (40+ payloads)
│   └── xml-injection.yaml (30+ payloads)
├── auth/
│   ├── auth-bypass.yaml (100+ payloads)
│   └── jwt-attacks.yaml (50+ payloads)
├── ssrf/
│   └── ssrf-payloads.yaml (150+ payloads)
├── file-inclusion/
│   ├── lfi.yaml (60+ payloads)
│   └── rfi.yaml (40+ payloads)
└── ...
```

#### Binding Logic
```python
def bind_payloads(test_case, endpoint_params):
    payloads_ref = test_case['payloads_ref']  # e.g., "injection/sql-auth-bypass"
    payload_db = load_payloads(payloads_ref)
    
    bound_payloads = []
    
    for param in endpoint_params:
        for payload in payload_db:
            # Context matching
            if is_compatible(payload, param):
                bound_payloads.append({
                    "parameter": param,
                    "payload": payload['value'],
                    "encoding": payload.get('encoding', 'none'),
                    "safety_level": payload['safety_level']
                })
    
    return bound_payloads[:50]  # Limit to prevent payload explosion
```

#### Example Payload Database
```yaml
# knowledge-base/payloads/injection/sql-auth-bypass.yaml
payloads:
  - value: "admin' OR '1'='1"
    description: "Basic OR bypass"
    safety_level: "safe"
    encoding: "none"
    database: "all"
    
  - value: "admin' OR '1'='1'--"
    description: "OR bypass with comment"
    safety_level: "safe"
    encoding: "none"
    database: "mysql,mssql"
    
  - value: "admin'--"
    description: "Comment out password check"
    safety_level: "safe"
    encoding: "none"
    database: "all"
```

### Component 5: Safety Enforcer ⚠️
**File:** `backend/app/rule_engine/safety_enforcer.py`

#### Purpose
**CRITICAL COMPONENT** - Blocks destructive payloads to prevent damage to target systems.

#### Destructive Patterns Blocked
```python
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
]
```

#### Safety Classification
**Knowledge Base:** `knowledge-base/metadata/payload-safety.yaml`

```yaml
safety_levels:
  safe:             # Level 0
    auto_scan: true
    requires_approval: false
    environment: ["production", "staging", "dev"]
    
  low_risk:         # Level 1
    auto_scan: true
    requires_approval: false
    environment: ["production", "staging", "dev"]
    
  medium_risk:      # Level 2
    auto_scan: false
    requires_approval: true
    environment: ["staging", "dev"]
    
  high_risk:        # Level 3
    auto_scan: false
    requires_approval: true
    environment: ["dev"]
```

#### Enforcement Logic
```python
def enforce(self, bound_payloads, environment="production"):
    safe_payloads = []
    blocked = []
    
    for payload in bound_payloads:
        # Check destructive patterns
        if self._is_destructive(payload['value']):
            blocked.append(payload)
            continue
        
        # Check safety level
        safety_level = payload['safety_level']
        if self._is_allowed_in_environment(safety_level, environment):
            safe_payloads.append(payload)
        else:
            blocked.append(payload)
    
    self.logger.warning(f"Blocked {len(blocked)} dangerous payloads")
    return safe_payloads
```

### Component 6: Validator Selector
**File:** `backend/app/rule_engine/validator_selector.py`

#### Purpose
Choose appropriate response validators based on the test case type.

#### Validator Database
```
knowledge-base/validators/
├── sql_errors.yaml          # Database error patterns
├── xss_reflections.yaml     # XSS detection patterns
├── auth_indicators.yaml     # Authentication success/failure
├── status-codes.yaml        # HTTP response analysis
├── error-patterns.yaml      # Generic error detection
└── data-leak.yaml          # Sensitive data exposure
```

#### Example Validator
```yaml
# knowledge-base/validators/sql_errors.yaml
validator_type: "sql_errors"
description: "Detect SQL injection through error messages"

patterns:
  mysql:
    - "You have an error in your SQL syntax"
    - "Warning: mysql_"
    - "MySQLSyntaxErrorException"
    
  postgresql:
    - "PostgreSQL query failed"
    - "pg_query() failed"
    - "PSQLException"
    
  mssql:
    - "Microsoft SQL Server"
    - "ODBC SQL Server Driver"
    - "SQLServer JDBC Driver"
    
  oracle:
    - "ORA-[0-9]{5}"
    - "Oracle error"
    - "OracleException"
```

#### Selection Logic
```python
def select_validators(test_case):
    validators = []
    
    # From test case specification
    if 'validators' in test_case:
        for validator_name in test_case['validators']:
            validator = load_validator(validator_name)
            validators.append(validator)
    
    # Auto-select based on test type
    if test_case['category'] == 'sql-injection':
        validators.append(load_validator('sql_errors'))
        validators.append(load_validator('data-leak'))
    
    return validators
```

### Component 7: Attack Plan Generator
**File:** `backend/app/rule_engine/attack_plan_generator.py`

#### Purpose
Assemble the final, executable attack plan by combining all rule engine outputs.

#### Generated Plan Structure
```json
{
  "plan_id": "uuid-here",
  "generated_at": "2026-02-06T10:30:00Z",
  "target": {
    "url": "https://example.com/login",
    "method": "POST",
    "endpoint_type": "form"
  },
  "scope": {
    "owasp_categories": ["A05-injection", "A07-auth-failures"],
    "total_tests": 12
  },
  "tests": [
    {
      "test_id": "uuid-test-1",
      "category": "A05-injection",
      "priority": 100,
      "name": "SQL Injection - Authentication Bypass",
      "description": "Test for SQL injection in login form",
      "severity": "critical",
      "cwe": "CWE-89",
      "owasp": "A05",
      
      "method": "POST",
      "payloads": [
        {
          "parameter": "username",
          "value": "admin' OR '1'='1",
          "encoding": "none",
          "safety_level": "safe"
        }
      ],
      "validators": ["sql_errors", "auth_indicators"],
      
      "timeout": 30,
      "retry_count": 2,
      "rate_limit": 10
    }
  ],
  "execution_config": {
    "max_concurrent_tests": 5,
    "request_timeout": 30,
    "enable_safety_enforcer": true,
    "log_all_requests": true
  },
  "statistics": {
    "total_payloads": 45,
    "safe_payloads": 45,
    "blocked_payloads": 0,
    "estimated_duration": "5-10 minutes"
  }
}
```

---

## Knowledge Base

The **YAML-driven knowledge base** is the intelligence source for all security testing.

### Directory Structure

```
knowledge-base/
├── test-cases/              # 96+ test case files
│   ├── A01-broken-access-control/
│   │   ├── idor.yaml
│   │   ├── path-traversal.yaml
│   │   └── forced-browsing.yaml
│   ├── A02-security-misconfiguration/
│   ├── A03-software-supply-chain/
│   ├── A04-crypto-failures/
│   ├── A05-injection/
│   │   ├── sql-injection.yaml
│   │   ├── xss.yaml
│   │   ├── command-injection.yaml
│   │   ├── ldap-injection.yaml
│   │   └── xml-injection.yaml
│   ├── A06-insecure-design/
│   ├── A07-auth-failures/
│   ├── A08-software-data-integrity/
│   ├── A09-logging-alerting/
│   └── A10-ssrf/
│
├── payloads/                # ~1000+ payload database
│   ├── injection/
│   ├── auth/
│   ├── ssrf/
│   ├── file-inclusion/
│   ├── deserialization/
│   ├── crypto/
│   └── misc/
│
├── validators/              # 6+ validator files
│   ├── sql_errors.yaml
│   ├── xss_reflections.yaml
│   ├── auth_indicators.yaml
│   ├── status-codes.yaml
│   ├── error-patterns.yaml
│   └── data-leak.yaml
│
├── metadata/                # Classification & scoring
│   ├── owasp_comprehensive.yaml
│   ├── cwe_comprehensive.yaml
│   ├── cvss.yaml
│   ├── payload-safety.yaml
│   ├── confidence-scoring.yaml
│   └── severity.yaml
│
└── workflows/               # Attack patterns
    ├── authentication-testing.yaml
    ├── authorization-testing.yaml
    └── session-management.yaml
```

### Test Case Coverage

#### A01 - Broken Access Control
- **IDOR (Insecure Direct Object References)** - 8 test cases
- **Path Traversal** - 8 test cases
- **Forced Browsing** - 8 test cases
- Total: **24 test cases**

#### A02 - Security Misconfiguration
- Default credentials, security headers, verbose errors
- Directory listing, backup files, cloud storage
- Unnecessary services, HTTP methods
- Total: **8 test cases**

#### A05 - Injection
- **SQL Injection** - 8 test cases
  - Authentication bypass
  - UNION-based
  - Boolean blind
  - Time-based blind
  - Error-based
  - Stacked queries
  - Out-of-band
  - Second-order
- **XSS** - 12 test cases
- **Command Injection** - 6 test cases
- Total: **26+ test cases**

#### A07 - Authentication Failures
- Credential stuffing, brute force
- Session fixation, weak passwords
- Username enumeration, MFA bypass
- Password reset poisoning
- Total: **8 test cases**

#### A10 - SSRF
- Cloud metadata endpoints (AWS, Azure, GCP)
- Internal service exploitation
- Port scanning, blind SSRF
- Total: **8 test cases**

**Grand Total: 96+ comprehensive test cases**

### Payload Database Highlights

#### SQL Injection Payloads (300+)
```yaml
payloads:
  # Authentication bypass
  - "admin' OR '1'='1"
  - "admin'--"
  - "' OR 1=1--"
  
  # UNION-based extraction
  - "' UNION SELECT NULL--"
  - "' UNION SELECT username,password FROM users--"
  
  # Time-based blind
  - "' AND SLEEP(5)--"  # MySQL
  - "'; SELECT pg_sleep(5)--"  # PostgreSQL
  - "'; WAITFOR DELAY '00:00:05'--"  # MSSQL
  
  # Error-based
  - "' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT @@version)))--"
```

#### XSS Payloads (100+)
```yaml
payloads:
  # Basic
  - "<script>alert(1)</script>"
  - "<img src=x onerror=alert(1)>"
  
  # Event handlers
  - "<svg onload=alert(1)>"
  - "<body onload=alert(1)>"
  
  # Filter bypass
  - "<scr<script>ipt>alert(1)</scr</script>ipt>"
  - "<img src=x onerror=\"alert(String.fromCharCode(88,83,83))\">"
  
  # WAF bypass
  - "<img src=x onerror=eval(atob('YWxlcnQoMSk='))>"  # Base64
```

#### SSRF Payloads (150+)
```yaml
payloads:
  # Cloud metadata
  - "http://169.254.169.254/latest/meta-data/"  # AWS
  - "http://169.254.169.254/metadata/instance"  # Azure
  - "http://metadata.google.internal/"  # GCP
  
  # IP obfuscation
  - "http://2130706433/"  # 127.0.0.1 in decimal
  - "http://0x7f000001/"  # 127.0.0.1 in hex
  - "http://localhost@127.0.0.1/"  # URL-based bypass
  
  # Internal services
  - "http://localhost:6379/"  # Redis
  - "http://localhost:9200/"  # Elasticsearch
  - "http://localhost:8080/manager/html"  # Tomcat
```

---

## Technology Stack

### Backend Stack

#### Core Framework
- **Python 3.11+** - Modern Python with performance improvements
- **FastAPI 0.109+** - High-performance async web framework
- **Uvicorn** - ASGI server with WebSocket support
- **Pydantic 2.5+** - Data validation and settings management

#### Database & Caching
- **PostgreSQL 15+** - Primary relational database
- **SQLAlchemy 2.0+** - ORM with async support
- **Alembic 1.13+** - Database migrations
- **Redis 7+** - Caching and task queue broker

#### Task Queue
- **Celery 5.3+** - Distributed task queue
- **Celery Beat** - Periodic task scheduler
- **Flower** (optional) - Celery monitoring

#### Testing & Automation
- **Scrapy 2.11+** - Web crawling framework
- **Playwright 1.41+** - Browser automation
- **BeautifulSoup4** - HTML parsing
- **httpx** - Async HTTP client
- **aiohttp** - Alternative async HTTP

#### LLM Integration
- **Ollama** - Local LLM server (Llama2, Mistral, etc.)
- Strictly for **report explanations only**

#### Monitoring & Logging
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards and visualization
- **structlog** - Structured logging
- **prometheus_client** - Python metrics exporter

#### Security & Authentication
- **python-jose** - JWT handling
- **passlib** - Password hashing (bcrypt)
- **cryptography** - Encryption utilities

### Frontend Stack

#### Core Framework
- **React 18.2+** - UI library with concurrent features
- **TypeScript 5+** - Type-safe JavaScript
- **Vite 5+** - Fast build tool and dev server

#### Routing & State
- **React Router 6+** - Client-side routing
- **TanStack Query v5** - Server state management
- **React Hook Form 7+** - Form handling
- **Zod 3+** - Schema validation

#### UI Framework
- **Tailwind CSS 3+** - Utility-first CSS
- **shadcn/ui** - Re-usable component library
- **Lucide React** - Icon library
- **class-variance-authority** - Component variants

#### Real-time & Data Viz
- **Socket.io Client** - WebSocket communication
- **Recharts 2+** - Charting library
- **date-fns 3+** - Date utilities

#### HTTP Client
- **Axios 1.6+** - HTTP requests with interceptors

### Infrastructure

#### Containerization
- **Docker 24+** - Container runtime
- **Docker Compose 2.20+** - Multi-container orchestration

#### Production (Future)
- **Kubernetes** - Container orchestration
- **Helm** - Kubernetes package manager
- **Nginx** - Reverse proxy & load balancer

#### CI/CD (Future)
- **GitHub Actions** - Automated workflows
- **pytest** - Python testing (95%+ coverage target)
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting

### Development Tools

#### Backend
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **black** - Code formatting
- **mypy** - Static type checking

#### Frontend
- **Vitest** - Unit testing
- **TypeScript ESLint** - Linting
- **Prettier** - Code formatting

---

## Database Schema

### Tables Overview

```sql
-- Scans table
CREATE TABLE scans (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(100) UNIQUE NOT NULL,
    target_url VARCHAR(500) NOT NULL,
    scan_type VARCHAR(50) DEFAULT 'full',
    status VARCHAR(20) DEFAULT 'pending',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Configuration
    scope_config JSONB,
    test_config JSONB,
    
    -- Progress
    progress_percentage INTEGER DEFAULT 0,
    current_phase VARCHAR(100),
    
    -- Results summary
    total_findings INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    info_count INTEGER DEFAULT 0,
    
    -- Error tracking
    error_message TEXT
);

-- Endpoints table
CREATE TABLE endpoints (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    
    url VARCHAR(1000) NOT NULL,
    method VARCHAR(10) NOT NULL,
    
    -- Characteristics
    parameters JSONB,
    headers JSONB,
    cookies JSONB,
    endpoint_type VARCHAR(50),
    requires_auth BOOLEAN DEFAULT FALSE,
    
    -- OWASP mapping
    owasp_categories JSONB,
    
    -- Discovery metadata
    discovered_at TIMESTAMP DEFAULT NOW(),
    discovery_method VARCHAR(50)
);

-- Vulnerabilities table
CREATE TABLE vulnerabilities (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    endpoint_id INTEGER REFERENCES endpoints(id) ON DELETE CASCADE,
    
    -- Vulnerability details
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence FLOAT NOT NULL,
    
    -- Classification
    owasp_category VARCHAR(50) NOT NULL,
    cwe_id VARCHAR(20),
    cvss_score FLOAT,
    
    -- Evidence
    request_payload TEXT,
    response_evidence TEXT,
    poc_code TEXT,
    
    -- Metadata
    affected_parameter VARCHAR(200),
    attack_vector VARCHAR(100),
    
    -- Validation
    is_validated BOOLEAN DEFAULT FALSE,
    is_false_positive BOOLEAN DEFAULT FALSE,
    validation_notes TEXT,
    
    -- Remediation
    remediation TEXT,
    references JSONB,
    
    -- LLM explanation
    llm_explanation TEXT,
    
    -- Timestamps
    detected_at TIMESTAMP DEFAULT NOW(),
    validated_at TIMESTAMP
);

-- Attack plans table
CREATE TABLE attack_plans (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    endpoint_id INTEGER REFERENCES endpoints(id) ON DELETE CASCADE,
    
    plan_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    execution_results JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    executed_at TIMESTAMP
);

-- Reports table
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    
    report_type VARCHAR(20) NOT NULL,
    content TEXT,
    file_path VARCHAR(500),
    findings_summary JSONB,
    
    generated_at TIMESTAMP DEFAULT NOW()
);
```

### Indexes

```sql
CREATE INDEX idx_scans_scan_id ON scans(scan_id);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_vulnerabilities_severity ON vulnerabilities(severity);
CREATE INDEX idx_vulnerabilities_owasp ON vulnerabilities(owasp_category);
CREATE INDEX idx_endpoints_scan_id ON endpoints(scan_id);
```

---

## API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
Currently **no authentication** (development mode).  
Production will use JWT tokens:
```
Authorization: Bearer <token>
```

### Endpoints

#### Scans API

**Create Scan**
```http
POST /api/v1/scans
Content-Type: application/json

{
  "target_url": "https://example.com",
  "scan_type": "full",
  "scope_config": {
    "allowed_paths": ["/app/*"],
    "excluded_paths": ["/admin/*"]
  },
  "test_config": {
    "categories": ["A01", "A05", "A07"]
  }
}

Response: 201 Created
{
  "scan_id": "uuid-here",
  "status": "pending",
  "target_url": "https://example.com"
}
```

**List Scans**
```http
GET /api/v1/scans?status=running&limit=10

Response: 200 OK
{
  "scans": [
    {
      "scan_id": "uuid",
      "target_url": "https://example.com",
      "status": "running",
      "progress_percentage": 45
    }
  ],
  "total": 1
}
```

**Get Scan Details**
```http
GET /api/v1/scans/{scan_id}

Response: 200 OK
{
  "scan_id": "uuid",
  "target_url": "https://example.com",
  "status": "running",
  "progress_percentage": 45,
  "current_phase": "Detection",
  "total_findings": 3,
  "critical_count": 1,
  "high_count": 2
}
```

**Start Scan**
```http
POST /api/v1/scans/{scan_id}/start

Response: 200 OK
{
  "message": "Scan started",
  "task_id": "celery-task-uuid"
}
```

**Stop Scan**
```http
POST /api/v1/scans/{scan_id}/stop

Response: 200 OK
{
  "message": "Scan stopped"
}
```

**Delete Scan**
```http
DELETE /api/v1/scans/{scan_id}

Response: 204 No Content
```

#### Vulnerabilities API

**List Vulnerabilities**
```http
GET /api/v1/vulnerabilities?scan_id=uuid&severity=critical

Response: 200 OK
{
  "vulnerabilities": [
    {
      "id": 1,
      "title": "SQL Injection in Login",
      "severity": "critical",
      "confidence": 0.95,
      "owasp_category": "A05-injection",
      "cwe_id": "CWE-89",
      "cvss_score": 9.8
    }
  ],
  "total": 1
}
```

**Get Vulnerability Details**
```http
GET /api/v1/vulnerabilities/{vuln_id}

Response: 200 OK
{
  "id": 1,
  "title": "SQL Injection in Login",
  "description": "...",
  "severity": "critical",
  "confidence": 0.95,
  "request_payload": "...",
  "response_evidence": "...",
  "poc_code": "...",
  "remediation": "...",
  "llm_explanation": "..."
}
```

**Mark False Positive**
```http
PATCH /api/v1/vulnerabilities/{vuln_id}/mark-false-positive
Content-Type: application/json

{
  "notes": "This is expected behavior"
}

Response: 200 OK
```

**Generate PoC**
```http
POST /api/v1/vulnerabilities/{vuln_id}/generate-poc

Response: 200 OK
{
  "poc_code": "...",
  "curl_command": "...",
  "python_script": "...",
  "manual_steps": "..."
}
```

**Statistics by Severity**
```http
GET /api/v1/vulnerabilities/stats/by-severity

Response: 200 OK
{
  "critical": 2,
  "high": 5,
  "medium": 10,
  "low": 3,
  "info": 1
}
```

#### Dashboard API

**Get Dashboard Stats**
```http
GET /api/v1/dashboard/stats

Response: 200 OK
{
  "total_scans": 10,
  "active_scans": 2,
  "total_vulnerabilities": 45,
  "critical_vulns": 5,
  "scans_today": 3
}
```

**Get Activity Feed**
```http
GET /api/v1/dashboard/activity?limit=20

Response: 200 OK
{
  "activities": [
    {
      "timestamp": "2026-02-06T10:30:00Z",
      "type": "scan_started",
      "description": "Scan started for example.com"
    }
  ]
}
```

#### Reports API

**List Reports**
```http
GET /api/v1/reports?scan_id=uuid

Response: 200 OK
{
  "reports": [
    {
      "id": 1,
      "report_type": "xml",
      "scan_id": "uuid",
      "generated_at": "2026-02-06T10:30:00Z"
    }
  ]
}
```

**Download Report**
```http
GET /api/v1/reports/{report_id}/download

Response: 200 OK
Content-Type: application/xml
Content-Disposition: attachment; filename="report.xml"

<?xml version="1.0"?>
<security_report>...</security_report>
```

### WebSocket API

**Connect**
```javascript
const socket = io('ws://localhost:8000/ws/client-uuid');

socket.on('scan_progress', (data) => {
  console.log('Progress:', data.progress_percentage);
});

socket.on('vulnerability_found', (data) => {
  console.log('Found:', data.title, data.severity);
});

socket.on('scan_completed', (data) => {
  console.log('Scan completed');
});
```

**Events Emitted by Server**
- `scan_progress` - Progress updates
- `vulnerability_found` - New vulnerability detected
- `phase_changed` - Scan phase changed (Discovery → Detection → etc.)
- `scan_completed` - Scan finished
- `scan_failed` - Scan encountered error

---

## Frontend Application

### Pages

#### 1. Dashboard (`/dashboard`)
**File:** `frontend/src/pages/Dashboard.tsx`

**Features:**
- Overview statistics cards (total scans, active scans, vulnerabilities)
- Severity distribution chart
- Recent activity feed
- Quick start scan button
- Backend connection status indicator

**State Management:**
```typescript
const { data: stats } = useQuery({
  queryKey: ['dashboard-stats'],
  queryFn: () => api.get('/dashboard/stats'),
  refetchInterval: 5000  // Auto-refresh every 5s
});
```

#### 2. Scans Page (`/scans`)
**File:** `frontend/src/pages/Scans.tsx`

**Features:**
- Scan list with status badges
- Filter by status (pending/running/completed/failed)
- Search by target URL
- Create new scan modal
- Start/stop scan actions
- Delete scan with confirmation

**Create Scan Form:**
```typescript
<form onSubmit={handleSubmit}>
  <Input 
    name="target_url" 
    placeholder="https://example.com"
    required
  />
  <Select name="scan_type">
    <option value="full">Full Scan</option>
    <option value="quick">Quick Scan</option>
    <option value="custom">Custom</option>
  </Select>
  <Button type="submit">Start Scan</Button>
</form>
```

#### 3. Scan Detail Page (`/scans/:scanId`)
**File:** `frontend/src/pages/ScanDetail.tsx`

**Features:**
- Real-time progress bar
- Phase-by-phase status
- Live WebSocket updates
- Discovered endpoints table
- Found vulnerabilities list
- Stop scan button
- Generate report button

**WebSocket Integration:**
```typescript
useEffect(() => {
  const socket = io(`${WS_URL}/ws/${scanId}`);
  
  socket.on('scan_progress', (data) => {
    setProgress(data.progress_percentage);
  });
  
  socket.on('vulnerability_found', (vuln) => {
    setVulnerabilities(prev => [...prev, vuln]);
  });
  
  return () => socket.disconnect();
}, [scanId]);
```

#### 4. Vulnerabilities Page (`/vulnerabilities`)
**File:** `frontend/src/pages/Vulnerabilities.tsx`

**Features:**
- Vulnerability list with severity badges
- Filter by severity (critical/high/medium/low/info)
- Filter by OWASP category
- Search by title
- Sort by confidence, date, CVSS score
- Mark as false positive
- Generate PoC button
- View details modal

**Severity Badge:**
```tsx
const SeverityBadge = ({ severity }) => {
  const colors = {
    critical: 'bg-red-600',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500',
    info: 'bg-gray-500'
  };
  
  return (
    <span className={`${colors[severity]} px-2 py-1 rounded text-white`}>
      {severity.toUpperCase()}
    </span>
  );
};
```

#### 5. Reports Page (`/reports`)
**File:** `frontend/src/pages/Reports.tsx`

**Features:**
- Report list with type (XML/JSON/HTML/PDF)
- Download button
- Delete report
- View findings summary
- Generation timestamp

### Components

**Key Reusable Components:**
```
components/
├── Layout.tsx                 # Main layout with sidebar
├── Sidebar.tsx               # Navigation sidebar
├── Header.tsx                # Top header with user info
├── StatsCard.tsx             # Dashboard statistic card
├── ScanCard.tsx              # Scan list item
├── VulnerabilityCard.tsx     # Vulnerability list item
├── ProgressBar.tsx           # Scan progress indicator
├── SeverityBadge.tsx         # Severity level badge
├── StatusBadge.tsx           # Scan status badge
├── CreateScanModal.tsx       # New scan form
├── VulnerabilityModal.tsx    # Vulnerability details
└── ConfirmDialog.tsx         # Confirmation dialog
```

### Services

**API Client:**
```typescript
// frontend/src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptors for auth tokens (future)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

**WebSocket Service:**
```typescript
// frontend/src/services/websocket.ts
import { io, Socket } from 'socket.io-client';

export const createWebSocket = (scanId: string): Socket => {
  const socket = io(`${import.meta.env.VITE_WS_URL}/ws/${scanId}`);
  
  socket.on('connect', () => {
    console.log('WebSocket connected');
  });
  
  socket.on('disconnect', () => {
    console.log('WebSocket disconnected');
  });
  
  return socket;
};
```

### Types

```typescript
// frontend/src/types/index.ts

export interface Scan {
  id: number;
  scan_id: string;
  target_url: string;
  scan_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress_percentage: number;
  current_phase?: string;
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface Vulnerability {
  id: number;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  confidence: number;
  owasp_category: string;
  cwe_id?: string;
  cvss_score?: number;
  request_payload?: string;
  response_evidence?: string;
  poc_code?: string;
  is_validated: boolean;
  is_false_positive: boolean;
  detected_at: string;
}

export interface Report {
  id: number;
  scan_id: string;
  report_type: 'xml' | 'json' | 'html' | 'pdf';
  findings_summary: {
    total: number;
    by_severity: Record<string, number>;
  };
  generated_at: string;
}
```

---

## Infrastructure & DevOps

### Docker Compose Architecture

**Services:**
1. **PostgreSQL** - Database (port 5432)
2. **Redis** - Cache + Message Broker (port 6379)
3. **Ollama** - LLM Server (port 11434)
4. **Backend** - FastAPI (port 8000)
5. **Celery Worker** - Task execution
6. **Celery Beat** - Scheduler
7. **Frontend** - React/Vite (port 5173)
8. **Prometheus** - Metrics (port 9090)
9. **Grafana** - Dashboards (port 3001)

### Environment Variables

**Backend:**
```env
DATABASE_URL=postgresql://user:pass@postgres:5432/db
REDIS_URL=redis://redis:6379/0
OLLAMA_BASE_URL=http://ollama:11434
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
SECRET_KEY=change-in-production
ENVIRONMENT=development
```

**Frontend:**
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### Volumes

```yaml
volumes:
  postgres_data:    # Database persistence
  redis_data:       # Cache persistence
  ollama_data:      # LLM models
  prometheus_data:  # Metrics storage
  grafana_data:     # Dashboard configs
```

### Health Checks

```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U neuropent"]
    interval: 10s
    timeout: 5s
    retries: 5

redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
```

---

## Scan Execution Flow

### Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. USER INITIATES SCAN                                      │
│     POST /api/v1/scans {"target_url": "https://example.com"}│
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. CREATE SCAN RECORD                                       │
│     - Generate scan_id                                       │
│     - Status: PENDING                                        │
│     - Store in database                                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. QUEUE DISCOVERY TASK                                     │
│     discovery_agent.delay(scan_id, target_url)               │
│     Status → RUNNING                                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  4. DISCOVERY PHASE                                          │
│     Agent 1: Discovery Agent                                 │
│     - Playwright crawling (JavaScript-rendered sites)        │
│     - HTTP crawling (static content)                         │
│     - Form extraction                                        │
│     - API endpoint detection                                 │
│     - Parameter identification                               │
│     FOUND: 15 endpoints                                      │
│     WebSocket: Emit "phase_changed" → "Discovery Complete"   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  5. RULE ENGINE PROCESSING (Per Endpoint)                    │
│     For each discovered endpoint:                            │
│                                                               │
│     [Component 1] Context Normalizer                         │
│     └─> Standardize endpoint format                          │
│                                                               │
│     [Component 2] OWASP Mapper                               │
│     └─> Map to ["A05-injection", "A07-auth"]                 │
│                                                               │
│     [Component 3] Test Case Evaluator                        │
│     └─> Select 12 applicable tests from KB                   │
│                                                               │
│     [Component 4] Payload Binder                             │
│     └─> Bind 45 payloads to parameters                       │
│                                                               │
│     [Component 5] Safety Enforcer ⚠️                         │
│     └─> Filter: 45 safe, 0 blocked                           │
│                                                               │
│     [Component 6] Validator Selector                         │
│     └─> Choose ["sql_errors", "auth_indicators"]             │
│                                                               │
│     [Component 7] Attack Plan Generator                      │
│     └─> Generate final executable plan                       │
│                                                               │
│     RESULT: Attack plan stored in database                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  6. DETECTION PHASE                                          │
│     Agent 2: Detection Agent                                 │
│     For each test in attack plan:                            │
│       - Send baseline request                                │
│       - Send payload request                                 │
│       - Capture request/response                             │
│       - Apply validators                                     │
│       - Calculate confidence                                 │
│       IF vulnerable:                                         │
│         - Create vulnerability record                        │
│         - WebSocket: Emit "vulnerability_found"              │
│     FOUND: 3 vulnerabilities                                 │
│     Progress: 20% → 60%                                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  7. VALIDATION PHASE                                         │
│     Agent 4: Validation Agent                                │
│     For each vulnerability:                                  │
│       - Attempt 1: Reproduce                                 │
│       - Attempt 2: Reproduce                                 │
│       - Attempt 3: Reproduce                                 │
│       - Compare with baseline                                │
│       - Calculate final confidence                           │
│       IF 3/3 successful:                                     │
│         - Confidence = 1.0                                   │
│         - is_validated = True                                │
│       ELSE:                                                  │
│         - Lower confidence                                   │
│         - Possible false positive                            │
│     CONFIRMED: 2 high-confidence vulnerabilities             │
│     Progress: 60% → 80%                                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  8. POC GENERATION PHASE                                     │
│     Agent 3: PoC Generation Agent                            │
│     For each validated vulnerability:                        │
│       - Generate cURL command                                │
│       - Generate Python script                               │
│       - Generate manual steps                                │
│       - Add safety warnings                                  │
│       - Store in vulnerability.poc_code                      │
│     GENERATED: 2 PoC exploits                                │
│     Progress: 80% → 90%                                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  9. REPORT GENERATION PHASE                                  │
│     Agent 5: Report Generation Agent                         │
│     - Collect all findings                                   │
│     - Calculate statistics                                   │
│     - Generate CVSS scores                                   │
│     - Call Ollama for explanations                           │
│     - Format as XML/JSON/HTML                                │
│     - Store report in database                               │
│     GENERATED: report.xml                                    │
│     Progress: 90% → 100%                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  10. SCAN COMPLETE                                           │
│      - Status → COMPLETED                                    │
│      - WebSocket: Emit "scan_completed"                      │
│      - Send notification (optional)                          │
│      - User can download report                              │
└─────────────────────────────────────────────────────────────┘
```

### Timeline Example

```
00:00 - Scan created (PENDING)
00:01 - Discovery started (RUNNING)
00:30 - Discovery complete (15 endpoints found)
01:00 - Rule engine processing (Attack plans generated)
02:00 - Detection phase (Testing vulnerabilities)
04:00 - Validation phase (Confirming findings)
04:30 - PoC generation (Creating exploits)
05:00 - Report generation (Ollama explanations)
05:30 - Scan complete (COMPLETED)
```

---

## Security Features

### 1. Safety Enforcer (Critical)

**Destructive Payload Blocking:**
```python
# Automatically blocked patterns
BLOCKED = [
    "DROP TABLE",
    "DELETE FROM users WHERE 1=1",
    "rm -rf /",
    "shutdown -h now",
    "format c:",
    "exec('malicious')",
    "eval('code')"
]
```

**Environment-based Controls:**
```yaml
Production:
  - Allow: Safe payloads only
  - Block: Medium and High risk
  
Staging:
  - Allow: Safe and Low risk
  - Block: High risk
  
Development:
  - Allow: Safe, Low, and Medium risk
  - Block: High risk (requires manual approval)
```

### 2. Scope Validation

**Domain Restriction:**
```python
def is_in_scope(url, base_url):
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    
    # Must be same domain
    if parsed_url.netloc != parsed_base.netloc:
        return False
    
    # Check allowed paths
    if not matches_allowed_paths(parsed_url.path):
        return False
    
    # Check excluded paths
    if matches_excluded_paths(parsed_url.path):
        return False
    
    return True
```

### 3. Rate Limiting

```python
# Per-scan rate limits
MAX_REQUESTS_PER_SECOND = 10
DELAY_BETWEEN_TESTS = 0.5  # seconds

# Respect target's robots.txt
RESPECT_ROBOTS_TXT = True

# Request timeout
REQUEST_TIMEOUT = 30  # seconds
```

### 4. False Positive Reduction

**Confidence Scoring:**
```python
def calculate_confidence(validation_results):
    successful_attempts = sum(validation_results)
    total_attempts = len(validation_results)
    
    base_confidence = successful_attempts / total_attempts
    
    # Adjust based on factors
    if baseline_differs_significantly:
        base_confidence += 0.1
    
    if multiple_validators_agree:
        base_confidence += 0.1
    
    return min(base_confidence, 1.0)
```

**Baseline Comparison:**
```python
# Always compare attack vs baseline
baseline_response = send_request(url, params={})
attack_response = send_request(url, params={"id": "1' OR '1'='1"})

if significantly_different(baseline_response, attack_response):
    # Likely vulnerable
    record_vulnerability()
```

### 5. Audit Logging

**All requests logged:**
```python
logger.info(
    "Request sent",
    url=url,
    method=method,
    payload=payload,
    response_status=response.status_code,
    response_time=response.elapsed.total_seconds()
)
```

### 6. User Consent

```python
# Before starting destructive tests
if requires_user_approval(test):
    if not user_approved(test):
        skip_test()
```

---

## Installation & Setup

### Prerequisites

```bash
# Check versions
docker --version          # 24.0+
docker-compose --version  # 2.20+
node --version            # 18+
python --version          # 3.11+
```

### Option 1: Docker (Recommended)

**1. Clone repository**
```bash
git clone <repository-url>
cd NeuroPentWeb
```

**2. Start all services**
```bash
docker-compose up -d
```

**3. Wait for services (2-3 minutes)**
```bash
docker-compose ps
# All services should show "Up"
```

**4. Access application**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3001

**5. Initialize Ollama (first time only)**
```bash
docker-compose exec ollama ollama pull llama2
```

### Option 2: Manual Setup

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup (new terminal):**
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Start PostgreSQL:**
```bash
# Using Docker
docker run -d \
  --name neuropent_postgres \
  -e POSTGRES_USER=neuropent \
  -e POSTGRES_PASSWORD=neuropent_secure_pass \
  -e POSTGRES_DB=neuropent_db \
  -p 5432:5432 \
  postgres:15-alpine
```

**Start Redis:**
```bash
docker run -d \
  --name neuropent_redis \
  -p 6379:6379 \
  redis:7-alpine
```

**Start Celery Worker (new terminal):**
```bash
cd backend
.\.venv\Scripts\activate
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

---

## Configuration

### Backend Configuration

**File:** `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "NeuroPentWeb"
    VERSION: str = "2.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://..."
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000"
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Knowledge Base
    KNOWLEDGE_BASE_PATH: str = "./knowledge-base"
    
    # Scan Settings
    MAX_CONCURRENT_SCANS: int = 5
    SCAN_TIMEOUT_SECONDS: int = 3600
    MAX_PAYLOADS_PER_TEST: int = 50
    
    # Safety
    ENABLE_SAFETY_ENFORCER: bool = True
    BLOCK_DESTRUCTIVE_PAYLOADS: bool = True
    
    class Config:
        env_file = ".env"
```

### Frontend Configuration

**File:** `frontend/.env`

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## Development Guide

### Backend Development

**Project Structure:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── agents/              # 5 Celery agents
│   ├── api/v1/              # API endpoints
│   ├── core/                # Core utilities
│   ├── models/              # Database models
│   └── rule_engine/         # 7 rule components
├── tests/                   # Unit tests
├── alembic/                 # Database migrations
├── requirements.txt
└── Dockerfile
```

**Adding a New Endpoint:**
```python
# backend/app/api/v1/endpoints/example.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()

@router.get("/example")
async def get_example(db: Session = Depends(get_db)):
    return {"message": "Example endpoint"}
```

**Creating a Migration:**
```bash
alembic revision -m "Add new table"
# Edit generated file in alembic/versions/
alembic upgrade head
```

**Running Tests:**
```bash
pytest                        # All tests
pytest tests/test_agents/     # Specific module
pytest --cov=app              # With coverage
pytest -v                     # Verbose
```

### Frontend Development

**Project Structure:**
```
frontend/src/
├── App.tsx                  # Main app component
├── main.tsx                 # Entry point
├── components/              # Reusable components
├── pages/                   # Page components
├── services/                # API, WebSocket
├── types/                   # TypeScript types
└── styles/                  # CSS files
```

**Adding a New Page:**
```tsx
// frontend/src/pages/NewPage.tsx
export default function NewPage() {
  return (
    <div>
      <h1>New Page</h1>
    </div>
  );
}

// Add route in App.tsx
<Route path="new" element={<NewPage />} />
```

**Using TanStack Query:**
```tsx
import { useQuery } from '@tanstack/react-query';

const { data, isLoading, error } = useQuery({
  queryKey: ['scans'],
  queryFn: () => api.get('/scans'),
  refetchInterval: 5000  // Auto-refresh
});
```

---

## Deployment

### Production Checklist

- [ ] Change `SECRET_KEY` in environment
- [ ] Set `ENVIRONMENT=production`
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set strong database passwords
- [ ] Enable authentication (JWT)
- [ ] Configure CORS origins
- [ ] Set up backup strategy
- [ ] Configure monitoring alerts
- [ ] Review safety enforcer settings
- [ ] Test disaster recovery

### Docker Production

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
    environment:
      ENVIRONMENT: production
      DEBUG: false
      ENABLE_SAFETY_ENFORCER: true
    restart: always
  
  # Use nginx for reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

### Kubernetes (Future)

```bash
# Deploy to k8s
kubectl apply -f k8s/

# Scale workers
kubectl scale deployment celery-worker --replicas=5

# Rolling update
kubectl rollout restart deployment backend
```

---

## Troubleshooting

### Common Issues

**1. Backend won't start**
```bash
# Check database connection
docker-compose logs postgres

# Check Redis
docker-compose logs redis

# Restart backend
docker-compose restart backend
```

**2. Frontend can't connect to backend**
```bash
# Check CORS settings in backend/app/core/config.py
CORS_ORIGINS = ["http://localhost:5173"]

# Check API URL in frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

**3. Celery tasks not running**
```bash
# Check worker status
docker-compose logs celery-worker

# Restart worker
docker-compose restart celery-worker

# Inspect tasks
docker-compose exec backend celery -A app.core.celery_app inspect active
```

**4. WebSocket not connecting**
```bash
# Check WebSocket URL
VITE_WS_URL=ws://localhost:8000

# Check browser console for errors
# Verify CORS allows WebSocket upgrade
```

**5. Scans failing**
```bash
# Check logs
docker-compose logs backend

# Check knowledge base path
ls knowledge-base/  # Should exist

# Verify Safety Enforcer isn't too strict
# Check backend/app/core/config.py
```

### Debug Mode

**Enable verbose logging:**
```python
# backend/app/core/config.py
LOG_LEVEL: str = "DEBUG"
```

**Frontend debug:**
```bash
# In browser console
localStorage.setItem('debug', '*');
```

---

## Performance Optimization

### Backend

- **Connection Pooling**: SQLAlchemy pool size = 10
- **Async/Await**: All I/O operations are async
- **Caching**: Redis caching for frequent queries
- **Background Tasks**: Celery for long-running operations

### Frontend

- **Code Splitting**: Lazy loading with React.lazy()
- **React Query Caching**: Default 5-minute cache
- **Virtualization**: For long lists (future)
- **Production Build**: `npm run build` optimizes bundle

---

## License

MIT License - See LICENSE file

---

## Support & Contact

- **Documentation**: See README.md files
- **Issues**: GitHub Issues
- **Email**: [contact info]

---

**Last Updated:** February 6, 2026  
**Version:** 2.0  
**Status:** ✅ Production-Ready
