# 🎯 Quick Reference: Using the 4 Enterprise Features

## 1️⃣ Payload Safety Classification

### When to Use
- Before executing any payload
- When scanning production environments
- When requiring approval for risky tests

### Quick Check
```python
# Is this payload safe for production?
payload = {
    "value": "<script>alert(1)</script>",
    "safety": "safe",  # ← Check this
    "environment": ["dev", "staging", "prod"],  # ← And this
    "destructive": false  # ← And this
}

if "prod" in payload["environment"] and not payload["destructive"]:
    ✅ SAFE FOR PRODUCTION
```

### Safety Levels
| Level | Auto-Scan? | Environments | Examples |
|-------|-----------|--------------|----------|
| **safe** | ✅ Yes | dev, staging, prod | `alert()`, `1=1` tests |
| **low_risk** | ✅ Yes | dev, staging, prod | Encoded XSS, boolean blind |
| **medium_risk** | ⚠️ Approval | dev, staging | SLEEP(5), SSRF metadata |
| **high_risk** | ⚠️ Approval | dev, staging | External callbacks, XXE |
| **destructive** | ❌ Manual only | isolated | DROP TABLE, file writes |

### File Location
`metadata/payload-safety.yaml`

---

## 2️⃣ Test Case → Payload Binding

### When to Use
- When starting a test case
- To prevent payload explosion
- To get intelligent payload selection

### Quick Usage
```python
# Get payloads for XSS detection
test_binding = {
    "test_id": "XSS-001",
    "allowed_payloads": [
        "xss_basic_alert_1",
        "xss_basic_img_onerror",
        "xss_basic_svg_onload"
    ],
    "max_payloads": 3,  # ← Only 3, not 100+
    "stop_on_success": true  # ← Stop after first success
}

# Execute
for payload_id in test_binding["allowed_payloads"]:
    result = execute_payload(payload_id)
    if result.success and test_binding["stop_on_success"]:
        break  # ✅ Stop, vulnerability confirmed
```

### Execution Orders
| Mode | Use When | Example |
|------|----------|---------|
| **sequential** | Order matters | Boolean blind (true/false pairs) |
| **parallel** | Independent tests | Default credentials (20 combos) |
| **adaptive** | AI decides | Filter bypass (try most successful first) |

### File Location
`metadata/test-payload-binding.yaml`

---

## 3️⃣ Confidence Scoring Logic

### When to Use
- After validator detects something
- To decide if it's a real vulnerability
- To reduce false positives

### Quick Calculation
```python
# Base confidence from validator
base_confidence = 0.40  # Error pattern detected

# Apply modifiers
modifiers = [
    ("repeatable", +0.15),           # Reproduced 3 times
    ("data_leak_confirmed", +0.20),  # Database version leaked
    ("status_code_change", +0.10),   # 401 → 200
]

# Calculate final confidence
final_confidence = base_confidence
for name, modifier in modifiers:
    final_confidence += modifier

# Result: 0.85 → HIGH CONFIDENCE ✅
```

### Decision Tree
| Confidence | Action |
|-----------|--------|
| **≥ 0.90** | ✅ AUTO-REPORT as CONFIRMED |
| **0.75-0.89** | ✅ REPORT as HIGH CONFIDENCE |
| **0.60-0.74** | ⚠️ REPORT + Manual Review |
| **0.40-0.59** | ⚠️ FLAG for Review (LOW) |
| **< 0.40** | ❌ SUPPRESS (likely FP) |

### Common Modifiers
**Positive (Add Confidence)**
- `repeatable: +0.15` - Reproduced 3+ times
- `data_leak_confirmed: +0.20` - Sensitive data leaked
- `session_token_granted: +0.20` - Auth token issued
- `status_code_change: +0.10` - 401 → 200
- `external_callback_confirmed: +0.25` - DNS/HTTP callback

**Negative (Reduce Confidence)**
- `waf_block_suspected: -0.25` - 403 Forbidden
- `response_identical: -0.30` - No behavior change
- `encoding_detected: -0.35` - Payload sanitized
- `payload_not_reflected: -0.25` - Not in response

### File Location
`metadata/confidence-scoring.yaml`

---

## 4️⃣ Baseline vs Attack Comparison

### When to Use
- After executing a payload
- To prove behavior changed
- To generate strong PoC

### Quick Usage
```python
# 1. Capture baseline
baseline_response = send_request({
    "url": "https://example.com/login",
    "body": "username=testuser&password=testpass"
})
# Result: 401 Unauthorized

# 2. Execute attack
attack_response = send_request({
    "url": "https://example.com/login",
    "body": "username=admin' OR '1'='1'--&password=anything"
})
# Result: 200 OK + session cookie

# 3. Compare
diff = compare_responses(baseline_response, attack_response)

if diff["status_code_changed"]:
    print("✅ Status changed:", diff["status_code_diff"])
    # Output: 401 → 200

if diff["cookies_added"]:
    print("✅ Cookies added:", diff["cookies_added"])
    # Output: session=abc123def456

if diff["vulnerability_confirmed"]:
    generate_poc(diff)  # Auto-generate curl PoC
```

### What to Compare
| Field | Significance |
|-------|-------------|
| **status_code** | 401→200 = auth bypass |
| **cookies_set** | Session token = logged in |
| **redirect_chain** | → /dashboard = access granted |
| **content_length** | +4000 bytes = data leaked |
| **response_time** | +5 seconds = SLEEP confirmed |
| **body_diff** | "Login Failed" → "Welcome" = success |

### Diff Hash
```python
# Calculate diff hash
diff_hash = SHA256(normalize(response))

# Compare
if baseline_hash == attack_hash:
    confidence -= 0.30  # ❌ Identical = likely not vulnerable
else:
    confidence += 0.10  # ✅ Different = behavior changed
```

### File Location
`metadata/response-comparison.yaml`

---

## 🔄 Complete Workflow

```python
# 1. Select test case
test_case = get_test_case("SQLI-001")

# 2. Get allowed payloads (GAP 2)
payloads = get_allowed_payloads(
    test_case_id="SQLI-001",
    environment="prod"
)
# Returns: 3 safe payloads (not 100+)

# 3. Capture baseline (GAP 4)
baseline = send_request(test_case.url, normal_params)

for payload in payloads:
    # 4. Check payload safety (GAP 1)
    if not is_safe_for_environment(payload, "prod"):
        continue
    
    # 5. Execute attack (GAP 4)
    attack = send_request(test_case.url, inject_payload(payload))
    
    # 6. Compare responses (GAP 4)
    diff = compare_responses(baseline, attack)
    
    # 7. Calculate confidence (GAP 3)
    confidence = calculate_confidence(
        base=0.40,  # SQL error detected
        modifiers=get_modifiers(diff)
    )
    
    # 8. Decision
    if confidence >= 0.75:
        report_vulnerability(test_case, payload, diff, confidence)
        break  # stop_on_success
    elif confidence < 0.40:
        suppress_finding()  # Likely false positive
```

---

## 📊 Example: SQL Injection Detection

```python
# Test Case: SQLI-001 (Auth Bypass)
test_case = {
    "test_id": "SQLI-001",
    "url": "https://example.com/login",
    "method": "POST"
}

# Step 1: Get allowed payloads (GAP 2)
payloads = [
    {"id": "sqli_auth_basic_1", "value": "admin' OR '1'='1'--", "safety": "safe"},
    {"id": "sqli_auth_basic_2", "value": "' OR 1=1--", "safety": "safe"},
    {"id": "sqli_auth_basic_3", "value": "admin'--", "safety": "safe"}
]
# Only 3 payloads, not 100+

# Step 2: Capture baseline (GAP 4)
baseline = POST("/login", {
    "username": "testuser",
    "password": "testpass"
})
# → 401 Unauthorized

# Step 3: Execute attack (GAP 4)
attack = POST("/login", {
    "username": "admin' OR '1'='1'--",
    "password": "anything"
})
# → 200 OK + session=abc123

# Step 4: Compare (GAP 4)
diff = {
    "status_code_changed": True,  # 401 → 200
    "cookies_added": ["session"],
    "redirect_changed": True,  # → /dashboard
    "behavioral_changes": ["authentication_bypass"]
}

# Step 5: Calculate confidence (GAP 3)
confidence = 0.40  # Base: error pattern
confidence += 0.20  # Session token granted
confidence += 0.15  # Repeatable
confidence += 0.10  # Status code change
# = 0.85 → HIGH CONFIDENCE ✅

# Step 6: Report
report = {
    "vulnerability": "SQL Injection - Authentication Bypass",
    "confidence": 0.85,
    "classification": "HIGH CONFIDENCE",
    "poc": generate_curl_poc(baseline, attack, diff)
}
```

---

## 🎯 Key Takeaways

1. **GAP 1 (Payload Safety)** → Controls WHAT payloads can run WHERE
2. **GAP 2 (Test-Payload Binding)** → Controls HOW MANY payloads per test
3. **GAP 3 (Confidence Scoring)** → Calculates IF it's a real vulnerability
4. **GAP 4 (Response Comparison)** → Proves HOW the behavior changed

**Together:** Fast, safe, accurate, enterprise-ready pentesting 🚀
