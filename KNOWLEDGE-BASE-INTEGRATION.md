# Knowledge Base Integration Guide

## 📚 Overview

The RakshAI knowledge base contains **96+ YAML files** organized into test cases, payloads, validators, and metadata. The rule engine loads and uses this data to make **100% deterministic, explainable security decisions**.

---

## 📁 Knowledge Base Structure

```
knowledge-base/
├── test-cases/              # 96+ test case files
│   ├── A01-broken-access-control/
│   ├── A02-security-misconfiguration/
│   ├── A03-software-supply-chain/
│   ├── A04-crypto-failures/
│   ├── A05-injection/
│   ├── A06-insecure-design/
│   ├── A07-auth-failures/
│   ├── A08-software-data-integrity/
│   ├── A09-logging-alerting/
│   ├── A10-exceptional-conditions/
│   └── A10-ssrf/
│
├── payloads/                # ~1000 payload entries
│   ├── injection/           # SQL, XSS, XXE, NoSQL
│   ├── auth/                # Auth bypass payloads
│   ├── ssrf/                # SSRF payloads
│   ├── deserialization/     # Insecure deserialization
│   └── misc/                # CORS, CSRF, etc.
│
├── validators/              # 6 validator files
│   ├── sql_errors.yaml      # SQL error detection
│   ├── xss_reflections.yaml # XSS reflection detection
│   ├── status-codes.yaml    # HTTP status analysis
│   ├── error-patterns.yaml  # Generic error patterns
│   ├── auth_indicators.yaml # Auth bypass indicators
│   └── data-leak.yaml       # Data leak detection
│
└── metadata/                # 12 metadata files
    ├── owasp_top10_2025.yaml
    ├── cwe.yaml
    ├── cvss.yaml
    ├── severity.yaml
    └── ...
```

---

## 🔧 How Rule Engine Uses Knowledge Base

### Architecture

```
┌─────────────────────────────────────┐
│   KnowledgeBaseLoader (Singleton)   │
│   Centralizes all YAML loading      │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┼──────────┐
        │         │          │
        ▼         ▼          ▼
  Test Cases  Payloads  Validators
        │         │          │
        ▼         ▼          ▼
┌─────────────────────────────────────┐
│      Rule Engine Components         │
│  [3] TestCaseEvaluator              │
│  [4] PayloadBinder                  │
│  [6] ValidatorSelector              │
└─────────────────────────────────────┘
```

### Data Flow

1. **Initialization** (app startup)
   ```python
   from app.core.knowledge_base import get_knowledge_base_loader
   
   kb = get_knowledge_base_loader("./knowledge-base")
   # Loads ALL YAML files into memory
   ```

2. **Component 3: Test Case Evaluator**
   ```python
   evaluator = TestCaseEvaluator(kb_path)
   # Accesses: kb_loader.get_all_test_cases()
   # Returns: Test cases for OWASP categories
   ```

3. **Component 4: Payload Binder**
   ```python
   binder = PayloadBinder(kb_path)
   # Accesses: kb_loader.get_all_payloads()
   # Returns: Payloads matching vulnerability type
   ```

4. **Component 6: Validator Selector**
   ```python
   selector = ValidatorSelector(kb_path)
   # Accesses: kb_loader.get_all_validators()
   # Returns: Validators for detection
   ```

---

## 🧪 Validation & Testing

### Validate Knowledge Base

```bash
# Windows
cd d:\NeuroPentWeb\backend
python scripts\validate_kb.py

# Linux/macOS
cd backend
python scripts/validate_kb.py
```

**Expected Output:**
```
🔍 NeuroPentWeb Knowledge Base Validation
================================================================================

📁 Knowledge Base Path: d:\NeuroPentWeb\knowledge-base
   Exists: True

📥 Loading knowledge base...
✅ Knowledge base loaded successfully!

🔍 Validating loaded data...
   Validation Results:
   ✅ test_cases_present: True
   ✅ payloads_present: True
   ✅ validators_present: True
   ✅ owasp_metadata_present: True
   ✅ cwe_metadata_present: True
   ✅ cvss_metadata_present: True
   ✅ severity_metadata_present: True
   ✅ all_valid: True

📊 Knowledge Base Statistics:
   Test Case Categories: 11
      - A01-broken-access-control: 3 test files
      - A02-security-misconfiguration: 1 test files
      ... (full list)

   Payload Types: 15+
   Total Payloads: 1000+

   Validators: 6
      - auth_indicators
      - data-leak
      - error-patterns
      - reflection
      - sql_errors
      - xss_reflections

   Metadata Files: 12
      - compliance
      - confidence-scoring
      - cvss
      ... (full list)

✅ KNOWLEDGE BASE VALIDATION SUCCESSFUL
```

### Test Rule Engine Integration

```bash
# Windows
python scripts\test_rule_engine.py

# Linux/macOS
python scripts/test_rule_engine.py
```

**Expected Output:**
```
🧪 Rule Engine Integration Test
================================================================================

🔧 Initializing Rule Engine Components...

[1/7] Context Normalizer...
   ✅ Normalized endpoint

[2/7] OWASP Mapper...
   ✅ Mapped to OWASP categories: ['A01', 'A05']

[3/7] Test Case Evaluator...
   ✅ Selected 15 test cases

[4/7] Payload Binder...
   ✅ Bound payloads to 15 tests
      Total payloads bound: 250

[5/7] Safety Enforcer...
   ✅ Safety enforcer working
      Blocked 2/4 test payloads as expected

[6/7] Validator Selector...
   ✅ Selected validators
      Total validators selected: 30

[7/7] Attack Plan Generator...
   ✅ Generated attack plan
      Total tests: 15
      Estimated time: 450s

✅ RULE ENGINE INTEGRATION TEST SUCCESSFUL
```

---

## 📝 Using Knowledge Base in Code

### Example 1: Get Test Cases for OWASP Category

```python
from app.core.knowledge_base import get_knowledge_base_loader

kb = get_knowledge_base_loader("./knowledge-base")

# Get all SQL injection test cases
sql_tests = kb.get_test_cases_for_category("A05-injection")

for test in sql_tests:
    print(f"Test: {test.get('name')}")
    print(f"File: {test.get('_source_file')}")
```

### Example 2: Search for Specific Payloads

```python
from app.core.knowledge_base import get_knowledge_base_loader

kb = get_knowledge_base_loader("./knowledge-base")

# Find XSS payloads
xss_payloads = kb.search_payloads(vulnerability_type="xss")

print(f"Found {len(xss_payloads)} XSS payloads")

# Find payloads with specific tags
tagged = kb.search_payloads(tags=["reflected", "dom-based"])
```

### Example 3: Get Validators

```python
from app.core.knowledge_base import get_knowledge_base_loader

kb = get_knowledge_base_loader("./knowledge-base")

# Get SQL error validator
sql_validator = kb.get_validator("sql_errors")

# Access error patterns
if sql_validator and "patterns" in sql_validator:
    patterns = sql_validator["patterns"]
    print(f"SQL error patterns: {len(patterns)}")
```

### Example 4: Access Metadata

```python
from app.core.knowledge_base import get_knowledge_base_loader

kb = get_knowledge_base_loader("./knowledge-base")

# Get OWASP Top 10:2025 mapping
owasp = kb.get_owasp_mapping()

# Get CWE mapping
cwe = kb.get_cwe_mapping()

# Get CVSS configuration
cvss = kb.get_cvss_config()

# Get severity levels
severity = kb.get_severity_levels()
```

---

## 🔍 YAML File Format Examples

### Test Case Format

```yaml
# test-cases/A05-injection/sql-injection.yaml
name: "SQL Injection - Union Based"
owasp_category: "A05"
cwe_id: "CWE-89"
severity: "high"

description: "Tests for SQL injection using UNION technique"

preconditions:
  - type: "parameter"
    injectable: true
  - type: "database"
    present: true

test_steps:
  - name: "Basic UNION test"
    payload_type: "injection/sql-injection"
    tags: ["union-based", "mysql"]
    
validation:
  - type: "sql_errors"
  - type: "response_comparison"
```

### Payload Format

```yaml
# payloads/injection/xss.yaml
payloads:
  - value: "<script>alert('XSS')</script>"
    tags: ["reflected", "basic"]
    severity: "medium"
    description: "Basic XSS payload"
    
  - value: "<img src=x onerror=alert('XSS')>"
    tags: ["reflected", "image-based"]
    severity: "medium"
    description: "Image tag XSS"
    
  - value: "javascript:alert('XSS')"
    tags: ["dom-based", "javascript"]
    severity: "high"
    description: "JavaScript protocol XSS"
```

### Validator Format

```yaml
# validators/sql_errors.yaml
name: "SQL Error Detection"
description: "Detects SQL errors in responses"

patterns:
  mysql:
    - "SQL syntax.*MySQL"
    - "Warning.*mysql_.*"
    - "valid MySQL result"
    
  postgresql:
    - "PostgreSQL.*ERROR"
    - "Warning.*\\Wpg_.*"
    - "pg_query\\(\\)"
    
  mssql:
    - "Driver.*SQL[\\ _]*Server"
    - "OLE DB.*SQL Server"
    - "SQLServer JDBC Driver"
```

---

## 🆕 Adding Custom YAML Files

### Add New Test Case

1. Create YAML file in appropriate category:
   ```bash
   # Example: Add custom auth test
   touch knowledge-base/test-cases/A07-auth-failures/my-custom-test.yaml
   ```

2. Follow standard format:
   ```yaml
   name: "My Custom Auth Test"
   owasp_category: "A07"
   cwe_id: "CWE-287"
   severity: "high"
   description: "Tests for custom authentication bypass"
   # ... rest of test definition
   ```

3. Restart backend to reload:
   ```bash
   docker-compose restart backend
   ```

### Add New Payloads

1. Create/edit YAML in payloads directory:
   ```bash
   # Edit existing or create new
   nano knowledge-base/payloads/injection/my-payloads.yaml
   ```

2. Add payload entries:
   ```yaml
   payloads:
     - value: "my custom payload"
       tags: ["custom", "test"]
       severity: "medium"
   ```

### Add New Validator

1. Create validator YAML:
   ```bash
   touch knowledge-base/validators/my-validator.yaml
   ```

2. Define patterns:
   ```yaml
   name: "My Custom Validator"
   patterns:
     - "custom error pattern"
     - "another pattern"
   ```

---

## 🐛 Troubleshooting

### Issue: "Knowledge base directory not found"

**Solution:**
```bash
# Verify path
ls -la knowledge-base/

# Check Docker mount (in docker-compose.yml)
volumes:
  - ./knowledge-base:/app/knowledge-base
```

### Issue: "No test cases loaded"

**Solution:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('knowledge-base/test-cases/A05-injection/sql-injection.yaml'))"

# Check file permissions
chmod -R 644 knowledge-base/**/*.yaml
```

### Issue: "Payloads not binding"

**Solution:**
1. Check payload file format matches expected structure
2. Verify payload tags match test case requirements
3. Run validation script: `python scripts/validate_kb.py`

---

## 📊 Statistics

Current knowledge base contains:

- **Test Cases:** 96+ files across 11 OWASP categories
- **Payloads:** ~1000 entries across 15+ types
- **Validators:** 6 specialized detection validators
- **Metadata:** 12 configuration and mapping files

**Total YAML Files:** 100+ files  
**Total Data Points:** 2000+ individual entries

---

## ✅ Verification Checklist

Before deployment, verify:

- [ ] Run `python scripts/validate_kb.py` - all checks pass
- [ ] Run `python scripts/test_rule_engine.py` - pipeline works end-to-end
- [ ] All YAML files have valid syntax (no parse errors in logs)
- [ ] Test cases cover all OWASP Top 10:2025 categories (A01-A10)
- [ ] Validators include all 6 types (SQL, XSS, status codes, etc.)
- [ ] Metadata files include OWASP, CWE, CVSS mappings

---

*Knowledge Base Integration - Last Updated: 2026-02-06*
