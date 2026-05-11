# 🚀 Quick Reference: Dependencies to Add

**For fastest production-readiness implementation, add these in order:**

---

## IMMEDIATE (Do First) 🔴

### Backend: requirements.txt additions
```
# Email & Notifications
aiosmtplib==2.1.1
email-validator==2.1.0

# Authentication & Authorization
authlib==1.3.0
python-keycloak==3.14.0

# Security
slowapi==0.1.9
bandit==1.7.5
safety==2.3.5

# Logging & Tracing
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-jaeger==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
python-json-logger==2.0.7

# Resilience
tenacity==8.2.3

# Data Validation
marshmallow==3.20.1

# File Handling
pillow==10.1.0
python-magic==0.4.27
```

### Docker Services: docker-compose.yml additions
```yaml
# Add these services:
postgres:      # Production DB (instead of SQLite)
elasticsearch: # Centralized logging
kibana:        # Log visualization
grafana:       # Metrics dashboard
jaeger:        # Distributed tracing
```

---

## VERY IMPORTANT (Do Second) 🟠

### Backend: requirements.txt
```
# Scheduling
APScheduler==3.10.4
croniter==2.0.1

# Connection Pooling
sqlalchemy-utils==0.41.1

# Alternative Message Queue
pika==1.3.2
```

### Frontend: package.json (devDependencies)
```json
{
  "@sentry/react": "^7.91.0",
  "@sentry/tracing": "^7.91.0",
  "react-toastify": "^9.1.3",
  "@radix-ui/react-dialog": "^1.1.1",
  "web-vitals": "^3.5.2"
}
```

---

## SHOULD HAVE (Nice-to-have) 🟡

### Backend: requirements.txt
```
# CLI Tools
typer==0.9.0

# Data Analytics
pandas==2.1.4
numpy==1.26.3

# Advanced Caching
diskcache==5.6.3

# API Proxy
httpx-retry==0.1.1
```

### Frontend: package.json
```json
{
  "@tanstack/react-table": "^8.11.3",
  "react-helmet-async": "^2.0.3"
}
```

---

## Comparison: What You Have vs What You Need

### Current Backend Coverage
✅ Web API (FastAPI)  
✅ Database (SQLAlchemy)  
✅ Caching (Redis)  
✅ LLM Integration (Ollama)  
✅ Web Scraping (Playwright, Scrapy)  
✅ Report Generation (Jinja2, WeasyPrint, python-docx)  

### Missing Critical Features
❌ Email notifications  
❌ Enterprise authentication (SSO/LDAP)  
❌ Distributed logging & tracing  
❌ Rate limiting & API protection  
❌ Job scheduling/background tasks  
❌ Production database (using SQLite)  

---

## Files to Update

| File | What to Add | Why |
|------|-----------|-----|
| `requirements.txt` | 15+ new packages | Production features |
| `docker-compose.yml` | 5+ new services | Infrastructure |
| `.env.example` | 20+ env variables | Configuration |
| `backend/app/main.py` | Middleware for slowapi, tracing | Security & monitoring |
| `frontend/package.json` | 5+ new npm packages | UI & error tracking |

---

## Installation Steps

```bash
# 1. Add to requirements.txt
cat >> backend/requirements.txt << 'EOF'
aiosmtplib==2.1.1
email-validator==2.1.0
authlib==1.3.0
slowapi==0.1.9
# ... (add all from IMMEDIATE section)
EOF

# 2. Install new packages
cd backend
pip install -r requirements.txt

# 3. Update docker-compose.yml with new services

# 4. Update frontend
cd ../frontend
npm install @sentry/react @sentry/tracing react-toastify

# 5. Run docker-compose with new services
docker-compose up -d
```

---

## Expected Benefits After Adding These Dependencies

| Feature | Current | After |
|---------|---------|-------|
| **Email Alerts** | ❌ None | ✅ SMTP + async |
| **Authentication** | Basic JWT | ✅ OAuth2/OIDC/LDAP |
| **API Security** | Limited | ✅ Rate limiting + DDoS protection |
| **Monitoring** | Basic metrics | ✅ Distributed tracing + logs |
| **Logging** | Structured logs | ✅ Elasticsearch + Kibana |
| **Scheduling** | Manual only | ✅ Cron jobs + background tasks |
| **Error Tracking** | Server logs | ✅ Sentry integration |
| **Production DB** | SQLite | ✅ PostgreSQL |

---

## Cost Impact (if using cloud)

### AWS Example
- PostgreSQL RDS: ~$15-30/month
- Elasticsearch: ~$50-100/month
- Monitoring: ~$10-20/month

**Total**: ~$75-150/month for Production-Grade Infrastructure

---

## Timeline Estimate

| Phase | Task | Effort | Timeline |
|-------|------|--------|----------|
| 1 | Add core dependencies | 2-3 hours | Day 1 |
| 2 | Configure email & auth | 4-5 hours | Day 2 |
| 3 | Setup logging/tracing | 3-4 hours | Day 3 |
| 4 | Update frontend | 2-3 hours | Day 4 |
| 5 | Test & validate | 3-4 hours | Day 5 |
| **Total** | **All-In** | **14-19 hours** | **1 Week** |

---

## Next Steps

1. **Review** the full analysis in `EXTERNAL_DEPENDENCIES_ANALYSIS.md`
2. **Prioritize** based on your requirements
3. **Create** a requirements-production.txt file
4. **Update** docker-compose.yml
5. **Test** with new dependencies
6. **Deploy** to staging first

---

**Ready to proceed? Start with the IMMEDIATE section!**
