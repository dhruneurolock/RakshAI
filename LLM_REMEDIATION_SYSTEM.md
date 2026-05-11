# LLM-Based Instant Remediation System for RakshAI

## Overview

The remediation system automatically generates **instant, actionable remediation solutions** when vulnerabilities are found in your security scans. Users can immediately patch vulnerabilities with AI-generated code examples and best practices.

---

## Features

✅ **Instant Remediation Generation**
- Triggered immediately after vulnerability detection/completion
- LLM-powered analysis using Ollama (llama3.2:1b)
- Uses knowledge base for context-aware solutions

✅ **Technology Detection**
- Automatically detects: PHP, Python, Node.js, Java, ASP.NET
- Tailors remediation code to specific technology stack
- Provides framework-specific solutions (Laravel, Django, Spring, etc.)

✅ **Comprehensive Solutions Include:**
1. Executive Summary (business impact)
2. Root Cause Analysis
3. Step-by-Step Remediation Instructions
4. **Production-Ready Code Examples**
5. Best Practices
6. Testing Instructions
7. Remediation Timeline (effort estimate)
8. Business Risk Analysis
9. References (OWASP, CWE, CVE links)

✅ **Severity-Based Urgency**
- CRITICAL: Apply within 24 hours
- HIGH: Apply within 1 week  
- MEDIUM: Apply within 2 weeks
- LOW: Apply within 1 month

---

## API Usage

### Generate Remediation Solution

**Endpoint:** `POST /api/v1/vulnerabilities/{vulnerability_id}/generate-remediation`

**Parameters:**
- `vulnerability_id` (required): Database ID of the vulnerability

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/vulnerabilities/621/generate-remediation \
  -H "Content-Type: application/json"
```

**Example Response:**
```json
{
  "message": "Remediation generated successfully",
  "vulnerability_id": 621,
  "vulnerability_type": "MISSING_CSRF_TOKEN",
  "severity": "medium",
  "technology_detected": "PHP",
  "remediation_solution": {
    "executive_summary": "The application lacks CSRF token protection...",
    "root_cause": "Forms do not implement synchronized token pattern...",
    "remediation_steps": [
      "Generate unique CSRF token per session",
      "Embed token in all forms as hidden input",
      "Validate token on form submission",
      "Regenerate token after validation",
      "Set SameSite=Strict on cookies",
      "Use HTTPS only with Secure flag"
    ],
    "code_example": "<?php session_start(); if (empty($_SESSION['csrf_token'])) { ... }",
    "best_practices": [...],
    "testing_instructions": [...],
    "timeline": "2-4 hours implementation",
    "business_impact": "CRITICAL - Attackers can perform unauthorized actions",
    "urgency": "MEDIUM - Apply within 2 weeks",
    "references": [
      "https://owasp.org/www-community/attacks/csrf",
      "https://cwe.mitre.org/data/definitions/352.html"
    ]
  },
  "generated_at": "2026-04-05T18:05:00.123456"
}
```

---

## Integration into Frontend

### 1. Add Remediation Button to Vulnerability Details View

```typescript
// src/components/VulnerabilityDetails.tsx
import { useState, useEffect } from 'react';
import axios from 'axios';

export function VulnerabilityDetails({ vulnId }) {
  const [remediation, setRemediation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateRemediation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `/api/v1/vulnerabilities/${vulnId}/generate-remediation`
      );
      setRemediation(response.data.remediation_solution);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate remediation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="vulnerability-details">
      <button 
        onClick={generateRemediation}
        disabled={loading}
        className="btn btn-primary"
      >
        {loading ? 'Generating...' : 'Generate Remediation Solution'}
      </button>

      {remediation && (
        <div className="remediation-solution p-4 mt-4 bg-blue-50 rounded-lg">
          <h3 className="text-lg font-bold mb-2">Instant Remediation Solution</h3>
          
          <div className="mb-4">
            <h4 className="font-semibold">Executive Summary</h4>
            <p>{remediation.executive_summary}</p>
          </div>

          <div className="mb-4">
            <h4 className="font-semibold">Root Cause</h4>
            <p>{remediation.root_cause}</p>
          </div>

          <div className="mb-4">
            <h4 className="font-semibold">Steps to Remediate</h4>
            <ol className="list-decimal list-inside space-y-2">
              {remediation.remediation_steps?.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </div>

          <div className="mb-4">
            <h4 className="font-semibold">Code Example</h4>
            <pre className="bg-gray-800 text-white p-4 rounded overflow-auto">
              {remediation.code_example}
            </pre>
          </div>

          <div className="flex gap-4">
            <div>
              <strong>Timeline:</strong> {remediation.timeline}
            </div>
            <div>
              <strong>Urgency:</strong> <span className="text-red-600">{remediation.urgency}</span>
            </div>
          </div>
        </div>
      )}

      {error && <div className="error alert alert-danger">{error}</div>}
    </div>
  );
}
```

### 2. Display in Findings List

```typescript
// src/components/FindingsList.tsx
{findings.map(finding => (
  <div key={finding.id} className="finding-card">
    <div className="finding-header">
      <h3>{finding.title}</h3>
      <button 
        onClick={() => openRemediationModal(finding.id)}
        className="btn btn-sm btn-info"
      >
        📋 Get Remediation
      </button>
    </div>
    {/* ... rest of finding details ... */}
  </div>
))}
```

---

## Supported Vulnerability Types

The system has built-in remediation solutions for:

- **MISSING_CSRF_TOKEN** - CSRF protection implementation
- **SQL_INJECTION** - SQL injection prevention
- **XSS** - Cross-site scripting prevention
- **BROKEN_ACCESS_CONTROL** - IDOR and access control fixes
- **AUTHENTICATION_BYPASS** - Authentication hardening
- **INSECURE_DESERIALIZATION** - Serialization security
- And more via LLM analysis

---

## How It Works

```
┌─────────────────────────────────────┐
│  Vulnerability Found                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  POST /vulnerabilities/{id}/        │
│  generate-remediation               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  RemediationAgent initializes       │
│  - Load LLMService                  │
│  - Prepare vulnerability data       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Detect Technology Stack            │
│  (PHP, Python, Node, Java, etc.)    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  LLMService.generate_remediation()  │
│  - Create comprehensive prompt      │
│  - Query Ollama LLM with KB context │
│  - Parse and structure response     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Enhance with Additional Context    │
│  - Add urgency based on severity    │
│  - Add relevant references (OWASP)  │
│  - Format code examples             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Return Complete Solution           │
│  - All above + references           │
│  - Ready to share with developers   │
└─────────────────────────────────────┘
```

---

## Configuration

### LLM Settings (in `app/services/llm_service.py`)

```python
# Configure Ollama connection
OLLAMA_BASE_URL = "http://localhost:11434"  # Default
OLLAMA_MODEL = "llama3.2:1b"  # Analysis model
TEMPERATURE = 0.5  # Balance between creativity and consistency
```

### Redis Configuration

Remediation generation is logged via Redis:
```python
await agent.emit_progress(scan_id, {
    "type": "remediation_generated",
    "vulnerability_type": "CSRF_TOKEN",
    "severity": "medium"
})
```

---

## Example: Instant CSRF Remediation

**Finding:** Form Missing Anti-CSRF Controls (Medium Severity)
**Technology:** PHP
**Endpoint:** GET /user_new.php

**API Call:**
```bash
POST /api/v1/vulnerabilities/621/generate-remediation
```

**Instant Solution Provided:**

1. **Executive Summary**
   - The application lacks CSRF token protection allowing attackers to perform unauthorized actions on behalf of authenticated users.

2. **Root Cause**
   - Forms do not implement synchronized token pattern

3. **Code Example (PHP)**
   ```php
   <?php
   session_start();
   if (empty($_SESSION['csrf_token'])) {
       $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
   }
   ?>
   <!-- Add to form -->
   <input type="hidden" name="csrf_token" value="<?php echo htmlspecialchars($_SESSION['csrf_token']); ?>">
   
   <!-- Validate on submission -->
   if ($_POST['csrf_token'] !== $_SESSION['csrf_token']) {
       http_response_code(403);
       die('CSRF token validation failed');
   }
   ```

4. **Best Practices**
   - Use framework CSRF middleware
   - Implement token rotation
   - Log validation failures
   - Test with OWASP ZAP

5. **Timeline:** 2-4 hours implementation
6. **Testing:** Capture form tokens, replace with invalid value, verify rejection

---

## Benefits

✅ **For Security Teams:**
- Instant remediation guidance
- Reduced time to present findings
- Better stakeholder communication
- Clear business impact explanations

✅ **For Developers:**
- Ready-to-use code examples
- Technology-specific solutions
- Best practices guidance
- Testing instructions

✅ **For Organizations:**
- Faster vulnerability remediation
- Improved security posture
- Reduced security debt
- Better compliance tracking

---

## Performance Notes

- **First call (~5-10 seconds):** LLM model loading
- **Subsequent calls (~2-3 seconds):** Direct LLM query
- **Mock mode (if LLM unavailable):** <500ms (uses templates)
- All responses are cached in remediation database field (optional)

---

## Troubleshooting

### LLM Service Not Available

If you see "LLM service not initialized" error:

1. Verify Ollama is running: `http://localhost:11434`
2. Check Python dependencies: `pip install langchain ollama chromadb`
3. System falls back to mock mode with template solutions

### Remediation Not Generating Code Examples

Ensure Ollama model is available:
```bash
ollama pull llama3.2:1b
```

### Timeout Issues

Increase timeout in endpoint if needed:
```python
# Modify remediation agent timeout
timeout = 30  # seconds
```

---

## Next Steps

1. ✅ **Backend running** - API endpoints ready
2. ✅ **Frontend integration** - Add buttons to findings view
3. ✅ **LLM configured** - Ollama llama3.2:1b running
4. 🔄 **Monitor usage** - Track remediation generation stats
5. 📊 **Iterate solutions** - Improve prompts based on feedback

---

## Support & Documentation

- **LLMService:** `app/services/llm_service.py`
- **RemediationAgent:** `app/agents/remediation_agent.py`
- **API Endpoint:** `app/api/v1/endpoints/vulnerabilities.py`
- **Knowledge Base:** `knowledge-base/` (YAML files for RAG)

---

**Last Updated:** April 5, 2026
**Status:** ✅ Production Ready
