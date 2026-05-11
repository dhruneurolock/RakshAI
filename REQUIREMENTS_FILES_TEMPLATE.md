# 📦 Production Requirements Files Template

Create these two files in the `backend/` directory:

---

## File 1: `backend/requirements-base.txt`
**Common dependencies for all environments**

```
# Core Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database & ORM
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
sqlalchemy-utils==0.41.1

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
authlib==1.3.0
cryptography==41.0.7
itsdangerous==2.1.2

# Configuration & Validation
pydantic==2.5.3
pydantic-settings==2.1.0
marshmallow==3.20.1

# Caching & Queuing
redis==5.0.1
celery==5.3.6

# HTTP Clients
httpx==0.25.2
aiohttp==3.9.1
requests==2.31.0
tenacity==8.2.3

# Web Scraping & Browser Automation
scrapy==2.11.0
playwright==1.41.1
beautifulsoup4==4.12.2
lxml==5.1.0

# LLM & AI Integration
langchain==0.1.6
langchain-community==0.0.19
ollama==0.1.7
chromadb==0.4.22
sentence-transformers==2.3.1
tiktoken==0.5.2

# Graph Database
neo4j==5.17.0
py2neo==2021.2.4

# Object Storage
minio==7.2.3
boto3==1.34.34

# Report Generation
jinja2==3.1.3
weasyprint==60.2
python-docx==1.1.0
openpyxl==3.1.2
markdown2==2.4.12

# Configuration
pyyaml==6.0.1

# Real-time Communication
websockets==12.0
python-socketio==5.11.0

# Monitoring & Observability
prometheus-client==0.19.0
structlog==24.1.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-jaeger==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
python-json-logger==2.0.7

# Email & Notifications
aiosmtplib==2.1.1
email-validator==2.1.0

# API Security
slowapi==0.1.9

# File Handling
pillow==10.1.0
python-magic==0.4.27

# Scheduling
APScheduler==3.10.4
croniter==2.0.1

# CLI Tools
typer==0.9.0
click==8.1.7

# Data Processing (Optional - for analytics)
pandas==2.1.4
numpy==1.26.3

# Advanced Caching
diskcache==5.6.3

# Message Queuing Alternative
pika==1.3.2

# keycloak Integration (Optional - for enterprise auth)
python-keycloak==3.14.0
```

---

## File 2: `backend/requirements-dev.txt`
**Development & testing dependencies**

```
# Include base requirements
-r requirements-base.txt

# Testing Framework
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-xdist==3.5.0
pytest-benchmark==4.0.0
faker==22.0.0
coverage==7.4.0

# Code Quality
black==23.12.1
isort==5.13.2
flake8==7.0.0
mypy==1.8.0
pylint==3.0.3
pycodestyle==2.11.1
pydocstyle==6.3.0

# Security Analysis
bandit==1.7.5
safety==2.3.5

# Documentation
pdoc==14.1.1
sphinx==7.2.6
sphinx-rtd-theme==2.0.0
apispec==6.5.0
apispec-webframeworks==0.5.2

# Debugging & Development
ipython==8.18.1
ipdb==0.13.13
debugpy==1.8.0

# Performance Profiling
line-profiler==4.1.1
memory-profiler==0.61.0

# Mock HTTP Responses
responses==0.24.1
```

---

## File 3: `backend/requirements-prod.txt`
**Production-only dependencies (minimal bloat)**

```
# Include base requirements
-r requirements-base.txt

# Gunicorn for production ASGI server (alternative to uvicorn)
gunicorn==21.2.0

# Production security
python-keycloak==3.14.0

# Sentry for error tracking (optional but recommended)
sentry-sdk==1.39.1

# Production monitoring
prometheus-client==0.19.0

# Optional: APM
datadog==0.47.1
```

---

## File 4: `backend/requirements-security.txt`
**Security & compliance scanning**

```
# Security scanning
bandit==1.7.5
safety==2.3.5
semgrep==1.44.1

# Dependency checking
pip-audit==2.6.1
```

---

## Update Instructions

### Step 1: Replace existing requirements.txt

```bash
# Backup current
cp backend/requirements.txt backend/requirements.txt.backup

# Replace with base requirements
cp backend/requirements-base.txt backend/requirements.txt
```

### Step 2: Create dependency structure

```bash
# Create the new files in backend/
touch backend/requirements-{dev,prod,security}.txt
# (Fill with content above)
```

### Step 3: Install for your environment

```bash
# Development
pip install -r backend/requirements-dev.txt

# Production
pip install -r backend/requirements-prod.txt

# Security audit
pip install -r backend/requirements-security.txt
```

### Step 4: Add to .gitignore

```
backend/requirements.txt.backup
backend/*.egg-info/
backend/dist/
backend/build/
```

---

## Version Pinning Strategy

### Development
- Use exact versions (==X.Y.Z) for reproducibility
- Update monthly with `pip list --outdated`

### Production
- Use compatible-release clauses (>=X.Y.Z,<X+1)
- Pin major versions only
- Test updates in staging first

### Example Production Pins
```
fastapi>=0.109.0,<2.0.0
sqlalchemy>=2.0.0,<3.0.0
pydantic>=2.0.0,<3.0.0
```

---

## Maintenance

### Monthly Check
```bash
# Check for outdated packages
pip list --outdated

# Check for security vulnerabilities
safety check
semgrep /path/to/backend

# Run security diagnostics
bandit -r backend/app
```

### Quarterly Updates
```bash
# Update patch versions in dev
pip install --upgrade -r requirements-dev.txt
pytest  # Make sure tests pass
```

### Emergency Updates
```bash
# Critical security patch
pip install --upgrade package-name==version
tests and deploy immediately
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Dependencies Check

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements-security.txt
      
      - name: Run bandit
        run: bandit -r backend/app
      
      - name: Run safety check
        run: safety check
```

---

## Troubleshooting

### Issue: Conflicting versions
```bash
# Use pip-tools to resolve
pip install pip-tools
pip-compile backend/requirements-base.txt
```

### Issue: Binary package installation fails
```bash
# On Windows, use wheels
pip install --only-binary=:all: pillow

# Or pre-built binary from wheels
pip install pillow --no-build-isolation
```

### Issue: Old version conflicts
```bash
# Create fresh virtualenv
python -m venv clean_venv
source clean_venv/bin/activate  # or on Windows: clean_venv\Scripts\activate
pip install -r requirements-prod.txt
```

---

## Dependency Size Reference

| Requirement File | Packages | Size | Purpose |
|------------------|----------|------|---------|
| requirements-base.txt | 45 | ~500MB | Core + production |
| requirements-dev.txt | +25 | +300MB | Testing + quality |
| requirements-prod.txt | +3 | +50MB | Production only |
| requirements-security.txt | +4 | +100MB | Scanning only |

---

## Docker Build Optimization

### Dockerfile with layer caching
```dockerfile
# Copy only requirements first (cache this layer)
COPY backend/requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Then copy source code
COPY backend/ .
```

---

## Migration from Single requirements.txt

```bash
# Current setup uses:
# requirements.txt (65 packages mixed)

# New setup will use:
# - requirements-base.txt (45 packages)
# - requirements-dev.txt (includes base + 25 dev)
# - requirements-prod.txt (includes base + 3 prod)

# No breaking changes - just better organized!

# Old:
pip install -r requirements.txt

# New (same effect):
pip install -r requirements-dev.txt  # for dev
pip install -r requirements-prod.txt # for prod
```

---

## Next Steps

1. ✅ Create the new requirements files
2. ✅ Test with each file
3. ✅ Update CI/CD pipelines
4. ✅ Document in README
5. ✅ Update deployment scripts
6. ✅ Train team on new structure

---

**Document Version**: 1.0  
**Created**: April 12, 2026
