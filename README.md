# RakshAI 🛡️

**Automated Web Application Penetration Testing with Deterministic Rule-Based Attack Planning**

## 🎯 Core Principle
**NO MACHINE LEARNING** - 100% YAML-driven rules for explainable, repeatable security decisions.
LLM usage is strictly limited to generating human-readable explanations, NOT security decisions.

## 🏗️ Architecture

### Multi-Agent System
```
User → Orchestrator → Scope Validation → Discovery Agent → 
Attack Surface Map → Rule Engine → Detection Agent → PoC Generation → 
Validation Agent → Report Generation → LLM Explanations → User
```

### 5 Specialized Agents
1. **Discovery Agent** - Scrapy + Playwright (endpoint discovery)
2. **Detection Agent** - Execute test cases, detect vulnerabilities
3. **PoC Generation Agent** - Create proof-of-concept exploits
4. **Validation Agent** - Confirm findings, reduce false positives
5. **Report Generation Agent** - XML reports with LLM explanations

### 7 Rule Engine Components (THE BRAIN 🧠)
1. **Context Normalizer** - Transform discovery output to standardized format
2. **OWASP Mapper** - Map endpoints to OWASP categories
3. **Test Case Evaluator** - Select applicable test cases from 96 YAML files
4. **Payload Binder** - Bind safe payloads from ~1000 YAML entries
5. **Safety Enforcer** - Block destructive payloads in production
6. **Validator Selector** - Choose detectors from 6 YAML validators
7. **Attack Plan Generator** - Assemble final attack execution plan

## 🚀 Technology Stack

### Backend
- **Language**: Python 3.11+
- **Web Framework**: FastAPI (async/await)
- **Database**: SQLite (local) or PostgreSQL
- **Cache**: Local Memory or Redis
- **LLM**: Ollama (local, open-source)

### Frontend
- **Framework**: React 18+ with TypeScript 5+
- **UI**: Tailwind CSS + shadcn/ui
- **State**: React Query (TanStack Query v5)

## 📦 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Ollama (installed locally)

### Launch All Services
```bash
# Clone repository
git clone <repository-url>
cd NeuroPentWeb

# Run the local startup script
# This script will verify prerequisites, set up the database, and launch both frontend and backend
.\start-local.ps1
```

### Access Points
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs

## 🎯 OWASP Top 10:2025 Coverage

✅ **A01** - Broken Access Control (IDOR, forced browsing, path traversal)  
✅ **A02** - Security Misconfiguration (default configs, headers)  
✅ **A03** - Software Supply Chain (dependency scanning)  
✅ **A04** - Cryptographic Failures (weak crypto, TLS issues)  
✅ **A05** - Injection (SQL, NoSQL, XSS, XXE, Command)  
✅ **A06** - Insecure Design (business logic flaws)  
✅ **A07** - Authentication Failures (brute force, session management)  
✅ **A08** - Software & Data Integrity (unsigned updates)  
✅ **A09** - Security Logging & Alerting Failures  
✅ **A10** - Server-Side Request Forgery (SSRF)  

## 📊 Project Structure
```
NeuroPentWeb/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── agents/       # 5 specialized agents
│   │   ├── rule_engine/  # 7 rule engine components
│   │   ├── models/       # SQLAlchemy models
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Config, security
│   │   └── services/     # Business logic
│   ├── tests/            # pytest tests
│   └── alembic/          # DB migrations
├── frontend/             # React + TypeScript
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/        # Route pages
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API clients
│   │   └── types/        # TypeScript types
│   └── public/
├── knowledge-base/       # YAML rules (existing)
└── start-local.ps1       # Local startup script
```

## 🧪 Testing
```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm run test

# E2E tests
npm run test:e2e
```

## 📝 License
MIT License

## 🤝 Contributing
See CONTRIBUTING.md

## 📚 Documentation
- [API Documentation](./docs/api.md)
- [Rule Engine Guide](./docs/rule-engine.md)
- [Agent Architecture](./docs/agents.md)
- [Deployment Guide](./docs/deployment.md)
