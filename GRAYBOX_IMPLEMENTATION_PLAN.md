# Gray-Box Testing Implementation Plan for NeuroPentWeb

**Version:** 1.0  
**Date:** June 1, 2026  
**Status:** Design Phase  
**Target:** Enable authenticated scanning with partial internal knowledge

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Difference: Black-Box vs Gray-Box in NeuroPentWeb](#difference-black-box-vs-gray-box-in-neuropentweb)
3. [Architecture Overview](#architecture-overview)
4. [Database Schema Changes](#database-schema-changes)
5. [Backend Implementation](#backend-implementation)
6. [Frontend Implementation](#frontend-implementation)
7. [API Changes](#api-changes)
8. [Data Collection Strategy](#data-collection-strategy)
9. [End-to-End Flow Diagrams](#end-to-end-flow-diagrams)
10. [Security Considerations](#security-considerations)
11. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

**Gray-box testing** adds authenticated/credentialed scanning capabilities to NeuroPentWeb, allowing testers to:
- Authenticate with target applications (login, OAuth, API keys, MFA)
- Access restricted endpoints and authenticated user workflows
- Discover admin panels, dashboards, and privilege escalation paths
- Test business logic and authorization checks
- Collect richer vulnerability data with user context

Current **black-box** flow:
```
Target URL → HTTP Probe → Crawl (public) → Nuclei Templates → Findings → Report
```

New **gray-box** flow:
```
Target URL + Credentials → Login → Session/Auth → HTTP Probe → Crawl (authenticated) 
→ Nuclei Templates (with auth context) → Advanced findings → Report
```

---

## Difference: Black-Box vs Gray-Box in NeuroPentWeb

| Aspect | Black-Box | Gray-Box |
|--------|-----------|----------|
| **Auth Required** | No | Yes (optional credentials) |
| **Tools Used** | httpx, katana, nuclei | + Browser auth, authenticated crawlers |
| **Endpoints Discovered** | Public only | Public + Authenticated restricted |
| **Vulnerabilities** | OWASP Top 10 (public) | + Authorization bypasses, logic flaws |
| **Session Handling** | None | Captures and reuses cookies/tokens |
| **Attack Surface** | ~30-40% | ~70-80%+ (with valid credentials) |
| **Data Collected** | URLs, tech stack, templates | + User roles, API endpoints, session tokens |
| **Time/Resources** | ~5-15 min | ~15-30 min (depends on app complexity) |

---

## Architecture Overview

### Current Architecture (Black-Box)
```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Vite)                         │
│                    ScanForm → Target URL                       │
└─────────────────────┬───────────────────────────────────────────┘
                      │ POST /api/v1/scans/
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI @ :8000)                      │
│                                                                 │
│  POST /scans/ → ScanCreate (target_url, scan_type, test_config) │
│                                                                 │
│    ┌──────────────────────────────────────────────────────┐    │
│    │       OrchestratorService                            │    │
│    │   Starts → ReconAgent → Parallel Tools              │    │
│    │   ├─ httpx (HTTP probing)                           │    │
│    │   ├─ katana (crawling)                              │    │
│    │   ├─ nuclei (template scanning)                     │    │
│    │   └─ Technology detection                           │    │
│    └──────────────────────────────────────────────────────┘    │
│                                                                 │
│    ┌──────────────────────────────────────────────────────┐    │
│    │  Storage Layer                                        │    │
│    │  ├─ PostgreSQL (Scan, Endpoints, Findings)          │    │
│    │  ├─ Neo4j (Graph: Targets, Endpoints, Vulns)        │    │
│    │  └─ MinIO (Raw scan outputs)                        │    │
│    └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                      │ WebSocket updates
                      ▼
         Real-time Dashboard + Report Generation
```

### Proposed Gray-Box Extension
```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (Vite - Enhanced)                   │
│              ScanForm + Auth Credentials Tab                     │
│  ├─ Target URL                                                   │
│  ├─ Scan Type (black-box, gray-box, white-box)                  │
│  ├─ Auth Method (form-login, api-key, oauth, mfa)               │
│  ├─ Credentials (username, password, secrets)                   │
│  └─ Auth Test (validate login before scan starts)               │
└──────────────────┬──────────────────────────────────────────────┘
                   │ POST /api/v1/scans/ with auth_config
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│           Backend API (FastAPI - Enhanced)                      │
│                                                                  │
│ ScanCreate:                                                      │
│  ├─ target_url (existing)                                        │
│  ├─ scan_type (existing)                                         │
│  ├─ test_config (existing)                                       │
│  ├─ auth_config (NEW)                                            │
│  │  ├─ auth_enabled: bool                                        │
│  │  ├─ auth_method: enum (form, api-key, oauth, etc.)           │
│  │  ├─ login_url: str (login endpoint)                           │
│  │  ├─ username: str (encrypted)                                 │
│  │  ├─ password: str (encrypted)                                 │
│  │  ├─ extra_headers: dict (API key, bearer token)               │
│  │  ├─ mfa_enabled: bool                                         │
│  │  ├─ mfa_method: str (TOTP, SMS, Email)                        │
│  │  └─ mfa_secret: str (encrypted, if TOTP)                      │
│  └─ scope_config (existing)                                      │
│                                                                  │
│    ┌───────────────────────────────────────────────────────┐   │
│    │  OrchestratorService (Enhanced)                       │   │
│    │                                                       │   │
│    │  Phase 0: Auth Validation (NEW)                       │   │
│    │    ├─ Decrypt credentials                            │   │
│    │    ├─ Attempt login (form/API)                        │   │
│    │    ├─ Extract session cookies/tokens                 │   │
│    │    └─ Store session in Redis (TTL: scan duration)     │   │
│    │                                                       │   │
│    │  Phase 1-7: (existing with auth context)             │   │
│    │    ├─ ReconAgent (+ auth headers/cookies)            │   │
│    │    ├─ httpx (authenticated requests)                 │   │
│    │    ├─ katana (authenticated crawling)                │   │
│    │    ├─ nuclei (authenticated templates)               │   │
│    │    ├─ Form Discovery (including restricted forms)    │   │
│    │    └─ Authorization Testing (NEW)                    │   │
│    └───────────────────────────────────────────────────────┘   │
│                                                                  │
│    ┌───────────────────────────────────────────────────────┐   │
│    │  Auth-Aware Tools                                      │   │
│    │  ├─ BrowserAuth (Playwright) - handle complex logins │   │
│    │  ├─ SessionManager - reuse auth across phases        │   │
│    │  ├─ AuthenticatedCrawler (Katana + cookies)          │   │
│    │  └─ AuthValidator - test privilege escalation        │   │
│    └───────────────────────────────────────────────────────┘   │
│                                                                  │
│    ┌───────────────────────────────────────────────────────┐   │
│    │  Enhanced Storage Layer                               │   │
│    │  ├─ PostgreSQL (Scan + AUTH_CONFIG table)             │   │
│    │  │  ├─ scan_id, auth_method, login_url, ...          │   │
│    │  │  └─ session_token (encrypted), session_valid_until │   │
│    │  ├─ Redis (Session Store - temporary)                │   │
│    │  │  ├─ session:{scan_id} → cookies/tokens            │   │
│    │  │  └─ TTL: scan duration + 5 min buffer             │   │
│    │  ├─ Neo4j (Graph queries now scoped by auth level)    │   │
│    │  │  ├─ Nodes tagged: @public, @authenticated, @admin  │   │
│    │  │  └─ Edges: privilege escalation paths             │   │
│    │  └─ MinIO (Raw outputs + auth telemetry)             │   │
│    └───────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                   │ WebSocket: auth_phase, session_active, etc.
                   ▼
      Enhanced Dashboard + Detailed Reports with Privilege Context
```

---

## Database Schema Changes

### 1. New `AUTH_CONFIG` Table (PostgreSQL)

```sql
-- Stores authentication configuration for scans
CREATE TABLE auth_config (
    id SERIAL PRIMARY KEY,
    scan_id VARCHAR(36) NOT NULL UNIQUE,
    auth_enabled BOOLEAN DEFAULT FALSE,
    auth_method VARCHAR(50) NOT NULL, -- form, api_key, oauth, mfa, custom
    login_url VARCHAR(500),
    username_encrypted VARCHAR(500),
    password_encrypted VARCHAR(500),
    extra_headers_encrypted TEXT, -- JSON blob, encrypted
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_method VARCHAR(50), -- totp, sms, email, hardware_key
    mfa_secret_encrypted VARCHAR(500), -- encrypted TOTP seed
    session_token_encrypted VARCHAR(1000), -- encrypted session/bearer token
    session_valid_until TIMESTAMP,
    auth_validation_status VARCHAR(50), -- pending, validating, success, failed
    auth_validation_error TEXT,
    auth_telemetry JSONB, -- login attempts, MFA attempts, session duration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scan_id) REFERENCES scans(scan_id) ON DELETE CASCADE
);

-- Index for faster lookups
CREATE INDEX idx_auth_config_scan_id ON auth_config(scan_id);
CREATE INDEX idx_auth_config_auth_enabled ON auth_config(auth_enabled);
```

### 2. Add Columns to `SCANS` Table (PostgreSQL)

```sql
-- Extend existing scans table to track auth context
ALTER TABLE scans ADD COLUMN auth_context_id INT;
ALTER TABLE scans ADD COLUMN authenticated_user VARCHAR(255);
ALTER TABLE scans ADD COLUMN privilege_level VARCHAR(50); -- public, user, admin
ALTER TABLE scans ADD COLUMN auth_findings_count INT DEFAULT 0;
ALTER TABLE scans ADD COLUMN privilege_escalation_vulns INT DEFAULT 0;

ALTER TABLE scans ADD CONSTRAINT fk_auth_context 
  FOREIGN KEY (auth_context_id) REFERENCES auth_config(id) ON DELETE SET NULL;
```

### 3. New `PRIVILEGE_ESCALATION` Finding Type

```sql
-- New column in vulnerabilities table to mark privilege escalation issues
ALTER TABLE vulnerabilities ADD COLUMN is_privilege_escalation BOOLEAN DEFAULT FALSE;
ALTER TABLE vulnerabilities ADD COLUMN required_privilege_level VARCHAR(50); -- public, user, admin
ALTER TABLE vulnerabilities ADD COLUMN escalates_to VARCHAR(50); -- what privilege level
ALTER TABLE vulnerabilities ADD COLUMN auth_context_required BOOLEAN DEFAULT FALSE;
```

### 4. Auth Session Storage (Redis)

```
Key: session:{scan_id}
Value: {
  "scan_id": "abc-123",
  "auth_method": "form",
  "session_cookie": "PHPSESSID=xyz...",
  "auth_headers": {
    "Authorization": "Bearer token...",
    "X-API-Key": "key..."
  },
  "authenticated_user": "testuser",
  "privilege_level": "user",
  "login_timestamp": 1717225200,
  "session_valid_until": 1717228800,
  "session_age_seconds": 3600
}

TTL: scan_duration + 5 minutes
Expires: automatically when scan completes
```

### 5. New Enum in Models

```python
class AuthMethod(str, Enum):
    FORM_LOGIN = "form_login"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    CUSTOM = "custom"

class MFAMethod(str, Enum):
    TOTP = "totp"  # Time-based OTP
    SMS = "sms"
    EMAIL = "email"
    HARDWARE_KEY = "hardware_key"

class PrivilegeLevel(str, Enum):
    PUBLIC = "public"
    AUTHENTICATED_USER = "authenticated_user"
    ADMIN = "admin"
    CUSTOM = "custom"  # for multi-role apps
```

---

## Backend Implementation

### 1. Enhanced `ScanCreate` Schema

```python
# backend/app/models/schemas.py

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum

class AuthMethod(str, Enum):
    FORM_LOGIN = "form_login"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    CUSTOM = "custom"

class MFAMethod(str, Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    NONE = "none"

class AuthConfig(BaseModel):
    """Authentication configuration for gray-box scans"""
    auth_enabled: bool = False
    auth_method: Optional[AuthMethod] = None
    login_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None  # For API keys, bearer tokens
    mfa_enabled: bool = False
    mfa_method: Optional[MFAMethod] = MFAMethod.NONE
    mfa_secret: Optional[str] = None  # TOTP seed, encrypted
    
    @validator('auth_method')
    def validate_auth_method(cls, v, values):
        if values.get('auth_enabled') and not v:
            raise ValueError("auth_method required when auth_enabled=True")
        return v

    @validator('login_url')
    def validate_login_url(cls, v, values):
        if values.get('auth_enabled') and not v:
            raise ValueError("login_url required for form-based auth")
        return v

class ScanCreate(BaseModel):
    target_url: HttpUrl
    scan_type: str = "full"
    scope_config: Optional[Dict[str, Any]] = None
    test_config: Optional[Dict[str, Any]] = None
    auth_config: Optional[AuthConfig] = None  # NEW: Gray-box config


class ScanResponse(BaseModel):
    # ... existing fields ...
    authenticated_user: Optional[str] = None
    privilege_level: Optional[str] = None
    auth_findings_count: Optional[int] = 0
    privilege_escalation_vulns: Optional[int] = 0
```

### 2. New `AuthenticationService` Class

```python
# backend/app/services/authentication_service.py

from typing import Dict, Any, Optional
import asyncio
import logging
import base64
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
import aiohttp
from playwright.async_api import async_playwright, Page

from app.core.config import get_settings
from app.core.redis_client import get_redis
from app.models.schemas import AuthConfig, AuthMethod, MFAMethod

logger = logging.getLogger(__name__)

class AuthenticationService:
    """Handles authentication setup and session management for gray-box scans"""
    
    def __init__(self):
        self.settings = get_settings()
        self.cipher = Fernet(self.settings.ENCRYPTION_KEY.encode())
        self.redis = get_redis()
    
    async def validate_and_authenticate(
        self,
        scan_id: str,
        auth_config: AuthConfig,
        db: Session
    ) -> Dict[str, Any]:
        """
        Validate auth config and establish authenticated session
        
        Returns:
            {
                "success": bool,
                "session_id": str,
                "auth_method": str,
                "privilege_level": str,
                "error": str (if failed)
            }
        """
        logger.info(f"[{scan_id}] Starting authentication validation")
        
        if not auth_config.auth_enabled:
            return {
                "success": True,
                "session_id": None,
                "auth_method": "none",
                "privilege_level": "public"
            }
        
        try:
            # Decrypt sensitive fields
            username = self._decrypt(auth_config.username)
            password = self._decrypt(auth_config.password)
            
            if auth_config.auth_method == AuthMethod.FORM_LOGIN:
                result = await self._authenticate_form_login(
                    scan_id, auth_config, username, password
                )
            elif auth_config.auth_method == AuthMethod.API_KEY:
                result = await self._authenticate_api_key(
                    scan_id, auth_config
                )
            elif auth_config.auth_method == AuthMethod.BEARER_TOKEN:
                result = await self._authenticate_bearer_token(
                    scan_id, auth_config
                )
            elif auth_config.auth_method == AuthMethod.BASIC_AUTH:
                result = await self._authenticate_basic_auth(
                    scan_id, auth_config, username, password
                )
            elif auth_config.auth_method == AuthMethod.OAUTH2:
                result = await self._authenticate_oauth2(
                    scan_id, auth_config
                )
            else:
                result = await self._authenticate_custom(
                    scan_id, auth_config
                )
            
            if result["success"]:
                # Store session in Redis
                await self._store_session(scan_id, result)
                logger.info(f"[{scan_id}] Authentication successful: {result['privilege_level']}")
            else:
                logger.error(f"[{scan_id}] Authentication failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"[{scan_id}] Auth error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "session_id": None,
                "error": str(e)
            }
    
    async def _authenticate_form_login(
        self,
        scan_id: str,
        auth_config: AuthConfig,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Authenticate via form submission using Playwright
        Handles MFA, JavaScript execution, redirects, etc.
        """
        logger.info(f"[{scan_id}] Starting form-based login to {auth_config.login_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to login page
                await page.goto(auth_config.login_url, wait_until="networkidle")
                
                # Find and fill username/password fields
                # (adjust selectors based on target app)
                username_selectors = ["input[name='username']", "input[name='user']", 
                                     "input[type='email']", "input[id*='user']"]
                password_selectors = ["input[name='password']", "input[name='pass']",
                                     "input[type='password']"]
                
                username_field = None
                for selector in username_selectors:
                    try:
                        username_field = await page.query_selector(selector)
                        if username_field:
                            break
                    except:
                        pass
                
                if not username_field:
                    return {
                        "success": False,
                        "error": "Could not locate username field on login page"
                    }
                
                password_field = None
                for selector in password_selectors:
                    try:
                        password_field = await page.query_selector(selector)
                        if password_field:
                            break
                    except:
                        pass
                
                if not password_field:
                    return {
                        "success": False,
                        "error": "Could not locate password field on login page"
                    }
                
                # Fill credentials
                await username_field.fill(username)
                await password_field.fill(password)
                
                # Find and click submit button
                submit_button = await page.query_selector(
                    "button[type='submit'], input[type='submit'], button:has-text('Login')"
                )
                
                if submit_button:
                    await submit_button.click()
                    await page.wait_for_nav_ignore_error(timeout=10000)
                
                # Handle MFA if enabled
                if auth_config.mfa_enabled:
                    await self._handle_mfa(page, auth_config, scan_id)
                
                # Extract session cookies
                cookies = await page.context.cookies()
                session_cookies = {c["name"]: c["value"] for c in cookies}
                
                # Determine privilege level by checking known admin URLs
                privilege_level = await self._determine_privilege_level(
                    page, auth_config.target_url
                )
                
                # Extract authenticated user if possible
                authenticated_user = await self._extract_username_from_page(page)
                
                return {
                    "success": True,
                    "session_id": scan_id,
                    "auth_method": "form_login",
                    "privilege_level": privilege_level,
                    "authenticated_user": authenticated_user,
                    "session_cookies": session_cookies,
                    "session_headers": {}
                }
                
            except Exception as e:
                logger.error(f"[{scan_id}] Form login failed: {str(e)}")
                return {
                    "success": False,
                    "error": f"Form login failed: {str(e)}"
                }
            finally:
                await browser.close()
    
    async def _authenticate_api_key(
        self,
        scan_id: str,
        auth_config: AuthConfig
    ) -> Dict[str, Any]:
        """Authenticate using API key header"""
        if not auth_config.extra_headers:
            return {"success": False, "error": "No API key provided"}
        
        headers = auth_config.extra_headers.copy()
        
        # Validate API key by making a test request
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    auth_config.login_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        return {
                            "success": True,
                            "session_id": scan_id,
                            "auth_method": "api_key",
                            "privilege_level": "authenticated_user",
                            "session_cookies": {},
                            "session_headers": headers
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"API key validation failed: {resp.status}"
                        }
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    async def _authenticate_bearer_token(
        self,
        scan_id: str,
        auth_config: AuthConfig
    ) -> Dict[str, Any]:
        """Authenticate using Bearer token"""
        if not auth_config.extra_headers or "Authorization" not in auth_config.extra_headers:
            return {"success": False, "error": "No Bearer token provided"}
        
        headers = {
            "Authorization": auth_config.extra_headers.get("Authorization")
        }
        
        # Validate token by making test request
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    auth_config.login_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        return {
                            "success": True,
                            "session_id": scan_id,
                            "auth_method": "bearer_token",
                            "privilege_level": "authenticated_user",
                            "session_cookies": {},
                            "session_headers": headers
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Bearer token validation failed: {resp.status}"
                        }
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    async def _authenticate_basic_auth(
        self,
        scan_id: str,
        auth_config: AuthConfig,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """Authenticate using HTTP Basic Auth"""
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers = {"Authorization": f"Basic {credentials}"}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    auth_config.login_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        return {
                            "success": True,
                            "session_id": scan_id,
                            "auth_method": "basic_auth",
                            "privilege_level": "authenticated_user",
                            "session_cookies": {},
                            "session_headers": headers
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Basic auth validation failed: {resp.status}"
                        }
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    async def _authenticate_oauth2(self, scan_id: str, auth_config: AuthConfig) -> Dict[str, Any]:
        """Placeholder for OAuth2 authentication"""
        # This would require more complex flow with authorization codes
        logger.warning(f"[{scan_id}] OAuth2 auth not fully implemented yet")
        return {"success": False, "error": "OAuth2 support coming soon"}
    
    async def _authenticate_custom(self, scan_id: str, auth_config: AuthConfig) -> Dict[str, Any]:
        """Placeholder for custom authentication methods"""
        logger.warning(f"[{scan_id}] Custom auth method specified")
        return {"success": False, "error": "Custom auth methods not yet implemented"}
    
    async def _handle_mfa(self, page: Page, auth_config: AuthConfig, scan_id: str):
        """Handle multi-factor authentication"""
        if auth_config.mfa_method == MFAMethod.TOTP:
            # Generate TOTP code
            import pyotp
            totp = pyotp.TOTP(self._decrypt(auth_config.mfa_secret))
            code = totp.now()
            
            # Find MFA input and fill it
            mfa_field = await page.query_selector(
                "input[name*='mfa'], input[name*='code'], input[name*='otp']"
            )
            if mfa_field:
                await mfa_field.fill(code)
                submit_button = await page.query_selector("button[type='submit']")
                if submit_button:
                    await submit_button.click()
        
        elif auth_config.mfa_method == MFAMethod.SMS:
            logger.warning(f"[{scan_id}] SMS MFA requires manual intervention")
            # Would require user input or saved verification codes
        
        elif auth_config.mfa_method == MFAMethod.EMAIL:
            logger.warning(f"[{scan_id}] Email MFA requires manual intervention")
            # Would require checking email for verification link
    
    async def _determine_privilege_level(self, page: Page, target_url: str) -> str:
        """Detect privilege level by testing access to known endpoints"""
        admin_indicators = [
            "/admin", "/dashboard", "/management", "/settings",
            "/api/admin", "/api/v1/admin", "/backend"
        ]
        
        for endpoint in admin_indicators:
            try:
                await page.goto(f"{target_url}{endpoint}", timeout=5000, wait_until="load")
                if page.url.find(endpoint) >= 0:
                    status = await page.evaluate("window.location.href")
                    # If we got here without redirect, likely admin access
                    if "admin" in endpoint.lower():
                        return "admin"
            except:
                pass
        
        return "authenticated_user"
    
    async def _extract_username_from_page(self, page: Page) -> Optional[str]:
        """Try to extract authenticated username from page content"""
        # Common patterns for displaying username
        username_indicators = [
            "text.user", "text.User", "text.username",
            "//span[contains(@class, 'username')]",
            "//div[contains(@class, 'profile-name')]",
            "//*[@id='user-name']"
        ]
        
        try:
            for indicator in username_indicators:
                element = await page.query_selector(indicator)
                if element:
                    username = await element.text_content()
                    if username:
                        return username.strip()
        except:
            pass
        
        return None
    
    async def _store_session(self, scan_id: str, session_data: Dict[str, Any]):
        """Store session in Redis for reuse across scan phases"""
        session_key = f"session:{scan_id}"
        
        session_payload = {
            "scan_id": scan_id,
            "auth_method": session_data.get("auth_method"),
            "session_cookies": session_data.get("session_cookies", {}),
            "session_headers": session_data.get("session_headers", {}),
            "authenticated_user": session_data.get("authenticated_user"),
            "privilege_level": session_data.get("privilege_level"),
            "login_timestamp": int(asyncio.get_event_loop().time()),
            "session_valid_until": int(asyncio.get_event_loop().time()) + 3600  # 1 hour
        }
        
        await self.redis.setex(
            session_key,
            3600 + 300,  # 1 hour + 5 min buffer
            json.dumps(session_payload)
        )
    
    async def get_session(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session from Redis"""
        session_key = f"session:{scan_id}"
        data = await self.redis.get(session_key)
        return json.loads(data) if data else None
    
    def _encrypt(self, plaintext: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def _decrypt(self, ciphertext: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

### 3. Update `ReconAgent` to Use Auth Session

```python
# backend/app/agents/recon.py (modifications)

from app.services.authentication_service import AuthenticationService

class ReconAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.auth_service = AuthenticationService()
    
    async def run(self, scan_id: str, auth_config: Optional[AuthConfig] = None, **kwargs) -> Dict[str, Any]:
        """Execute reconnaissance workflow with optional authentication"""
        
        try:
            await self.emit_progress(scan_id, "recon", "started", {
                "message": "Starting reconnaissance phase"
            })
            
            # Get scan details
            scan = await self._get_scan_details(scan_id)
            target_url = scan.get("target_url")
            
            # NEW: Phase 0 - Authentication (if configured)
            session = None
            if auth_config and auth_config.auth_enabled:
                await self.emit_progress(scan_id, "recon", "authenticating", {
                    "message": f"Authenticating via {auth_config.auth_method}"
                })
                
                auth_result = await self.auth_service.validate_and_authenticate(
                    scan_id, auth_config
                )
                
                if auth_result["success"]:
                    session = auth_result
                    await self.emit_progress(scan_id, "recon", "authenticated", {
                        "message": f"Authenticated as {session.get('authenticated_user')} ({session.get('privilege_level')})"
                    })
                else:
                    await self.emit_progress(scan_id, "recon", "auth_failed", {
                        "message": auth_result.get("error"),
                        "severity": "warning"
                    })
                    # Continue with unauthenticated scan
            
            # Phase 1: HTTP probing (with auth if available)
            await self.emit_progress(scan_id, "recon", "http_probing", {
                "message": "Probing HTTP endpoints"
            })
            http_results = await self._http_probe(target_url, session)
            
            # Phase 2: Web crawling (with auth)
            await self.emit_progress(scan_id, "recon", "crawling", {
                "message": "Crawling web application"
            })
            crawl_results = await self._web_crawl(target_url, session)
            
            # ... rest of phases with session context ...
            
            return result
    
    async def _http_probe(self, target_url: str, session: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute httpx with optional authentication headers"""
        try:
            headers = {}
            if session:
                # Add session headers/cookies
                if session.get("session_headers"):
                    headers.update(session["session_headers"])
                if session.get("session_cookies"):
                    headers["Cookie"] = "; ".join(
                        [f"{k}={v}" for k, v in session["session_cookies"].items()]
                    )
            
            result = await self.tool_sandbox.execute("httpx", {
                "target": target_url,
                "headers": headers if headers else None,
                "tech_detect": True,
                "status_code": True,
                "title": True,
                "web_server": True,
                "json": True,
                "timeout": 10
            })
            
            # ... rest of implementation ...
    
    async def _web_crawl(self, target_url: str, session: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute katana with optional authentication"""
        headers = {}
        if session:
            if session.get("session_headers"):
                headers.update(session["session_headers"])
            if session.get("session_cookies"):
                headers["Cookie"] = "; ".join(
                    [f"{k}={v}" for k, v in session["session_cookies"].items()]
                )
        
        result = await self.tool_sandbox.execute("katana", {
            "url": target_url,
            "headers": headers if headers else None,
            "depth": 3,
            "delay": 100,
            # ... rest of katana config ...
        })
        # ...
```

### 4. Update `OrchestratorService` to Call Auth Phase

```python
# backend/app/services/orchestrator.py (modifications)

async def start_scan(
    self,
    scan_id: str,
    target_url: str,
    scan_type: str,
    user_id: str,
    policy: Dict[str, Any],
    auth_config: Optional[AuthConfig] = None  # NEW parameter
) -> Dict[str, Any]:
    """Start enterprise scan with optional authentication"""
    
    # ... existing validation ...
    
    # NEW: Store auth config in database
    if auth_config and auth_config.auth_enabled:
        auth_service = AuthenticationService()
        auth_result = await auth_service.validate_and_authenticate(
            scan_id, auth_config, db
        )
        
        if auth_result["success"]:
            # Update scan with auth context
            scan.authenticated_user = auth_result.get("authenticated_user")
            scan.privilege_level = auth_result.get("privilege_level")
            db.commit()
    
    # Pass auth_config to CoordinatorAgent
    coordinator = CoordinatorAgent(agent_id=f"coordinator-{scan_id}")
    result = await coordinator.orchestrate(
        scan_id=scan_id,
        target_url=target_url,
        scan_type=scan_type,
        policy=policy,
        auth_config=auth_config  # NEW
    )
    
    return result
```

---

## Frontend Implementation

### 1. Enhanced `ScanForm` Component

```typescript
// frontend/src/components/ScanForm.tsx

import React, { useState } from 'react';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';

interface AuthConfig {
  authEnabled: boolean;
  authMethod: 'form_login' | 'api_key' | 'bearer_token' | 'basic_auth' | 'oauth2' | 'custom';
  loginUrl: string;
  username: string;
  password: string;
  extraHeaders: Record<string, string>;
  mfaEnabled: boolean;
  mfaMethod: 'totp' | 'sms' | 'email' | 'none';
  mfaSecret: string;
}

export function ScanForm() {
  const [targetUrl, setTargetUrl] = useState('');
  const [scanType, setScanType] = useState('full');
  const [authConfig, setAuthConfig] = useState<AuthConfig>({
    authEnabled: false,
    authMethod: 'form_login',
    loginUrl: '',
    username: '',
    password: '',
    extraHeaders: {},
    mfaEnabled: false,
    mfaMethod: 'none',
    mfaSecret: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const payload = {
      target_url: targetUrl,
      scan_type: scanType,
      auth_config: authConfig.authEnabled ? authConfig : null
    };
    
    const response = await fetch('/api/v1/scans/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    // ... handle response ...
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <TabGroup>
        <TabList className="flex space-x-1 rounded-xl bg-blue-900/20 p-1">
          <Tab className="px-4 py-2 rounded text-sm font-medium">Basic</Tab>
          <Tab className="px-4 py-2 rounded text-sm font-medium">Authentication</Tab>
          <Tab className="px-4 py-2 rounded text-sm font-medium">Advanced</Tab>
        </TabList>
        
        <TabPanels>
          {/* Basic Tab */}
          <TabPanel className="space-y-4">
            <div>
              <label htmlFor="target-url" className="block text-sm font-medium">
                Target URL *
              </label>
              <input
                id="target-url"
                type="url"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="https://example.com"
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
              />
            </div>

            <div>
              <label htmlFor="scan-type" className="block text-sm font-medium">
                Scan Type
              </label>
              <select
                id="scan-type"
                value={scanType}
                onChange={(e) => setScanType(e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
              >
                <option value="quick">Quick Scan (5-10 min)</option>
                <option value="full">Full Scan (15-30 min)</option>
                <option value="targeted">Targeted Scan (custom scope)</option>
              </select>
            </div>
          </TabPanel>

          {/* Authentication Tab */}
          <TabPanel className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="auth-enabled"
                checked={authConfig.authEnabled}
                onChange={(e) =>
                  setAuthConfig({ ...authConfig, authEnabled: e.target.checked })
                }
                className="h-4 w-4 rounded border-gray-300"
              />
              <label htmlFor="auth-enabled" className="ml-2 text-sm font-medium">
                Enable Gray-Box Testing (Authenticated Scan)
              </label>
            </div>

            {authConfig.authEnabled && (
              <>
                <div>
                  <label htmlFor="auth-method" className="block text-sm font-medium">
                    Authentication Method
                  </label>
                  <select
                    id="auth-method"
                    value={authConfig.authMethod}
                    onChange={(e) =>
                      setAuthConfig({
                        ...authConfig,
                        authMethod: e.target.value as any
                      })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  >
                    <option value="form_login">Form Login</option>
                    <option value="api_key">API Key</option>
                    <option value="bearer_token">Bearer Token</option>
                    <option value="basic_auth">Basic Authentication</option>
                    <option value="oauth2">OAuth2</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>

                {authConfig.authMethod === 'form_login' && (
                  <>
                    <div>
                      <label htmlFor="login-url" className="block text-sm font-medium">
                        Login URL *
                      </label>
                      <input
                        id="login-url"
                        type="url"
                        value={authConfig.loginUrl}
                        onChange={(e) =>
                          setAuthConfig({ ...authConfig, loginUrl: e.target.value })
                        }
                        placeholder="https://example.com/login"
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                      />
                    </div>

                    <div>
                      <label htmlFor="username" className="block text-sm font-medium">
                        Username
                      </label>
                      <input
                        id="username"
                        type="text"
                        value={authConfig.username}
                        onChange={(e) =>
                          setAuthConfig({ ...authConfig, username: e.target.value })
                        }
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                      />
                    </div>

                    <div>
                      <label htmlFor="password" className="block text-sm font-medium">
                        Password
                      </label>
                      <input
                        id="password"
                        type="password"
                        value={authConfig.password}
                        onChange={(e) =>
                          setAuthConfig({ ...authConfig, password: e.target.value })
                        }
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                      />
                    </div>

                    {/* MFA Section */}
                    <div className="pt-4 border-t border-gray-300">
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          id="mfa-enabled"
                          checked={authConfig.mfaEnabled}
                          onChange={(e) =>
                            setAuthConfig({
                              ...authConfig,
                              mfaEnabled: e.target.checked
                            })
                          }
                          className="h-4 w-4 rounded border-gray-300"
                        />
                        <label htmlFor="mfa-enabled" className="ml-2 text-sm font-medium">
                          Enable Multi-Factor Authentication
                        </label>
                      </div>

                      {authConfig.mfaEnabled && (
                        <div className="mt-3">
                          <label htmlFor="mfa-method" className="block text-sm font-medium">
                            MFA Method
                          </label>
                          <select
                            id="mfa-method"
                            value={authConfig.mfaMethod}
                            onChange={(e) =>
                              setAuthConfig({
                                ...authConfig,
                                mfaMethod: e.target.value as any
                              })
                            }
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                          >
                            <option value="totp">TOTP (Authenticator App)</option>
                            <option value="sms">SMS</option>
                            <option value="email">Email</option>
                          </select>

                          {authConfig.mfaMethod === 'totp' && (
                            <div className="mt-3">
                              <label htmlFor="mfa-secret" className="block text-sm font-medium">
                                TOTP Secret (Base32)
                              </label>
                              <input
                                id="mfa-secret"
                                type="password"
                                value={authConfig.mfaSecret}
                                onChange={(e) =>
                                  setAuthConfig({
                                    ...authConfig,
                                    mfaSecret: e.target.value
                                  })
                                }
                                placeholder="JBSWY3DPEBLW64TMMQ======"
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                              />
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </>
                )}

                {authConfig.authMethod === 'api_key' && (
                  <div>
                    <label htmlFor="api-key" className="block text-sm font-medium">
                      API Key
                    </label>
                    <input
                      id="api-key"
                      type="password"
                      value={authConfig.extraHeaders['X-API-Key'] || ''}
                      onChange={(e) =>
                        setAuthConfig({
                          ...authConfig,
                          extraHeaders: { 'X-API-Key': e.target.value }
                        })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    />
                  </div>
                )}

                {authConfig.authMethod === 'bearer_token' && (
                  <div>
                    <label htmlFor="bearer-token" className="block text-sm font-medium">
                      Bearer Token
                    </label>
                    <input
                      id="bearer-token"
                      type="password"
                      value={authConfig.extraHeaders['Authorization'] || ''}
                      onChange={(e) =>
                        setAuthConfig({
                          ...authConfig,
                          extraHeaders: { Authorization: `Bearer ${e.target.value}` }
                        })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    />
                  </div>
                )}
              </>
            )}
          </TabPanel>

          {/* Advanced Tab */}
          <TabPanel className="space-y-4">
            {/* Advanced options here */}
          </TabPanel>
        </TabPanels>
      </TabGroup>

      <button
        type="submit"
        className="w-full bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700"
      >
        Start Scan
      </button>
    </form>
  );
}
```

### 2. Enhanced Scan Dashboard with Auth Context

```typescript
// frontend/src/components/ScanDashboard.tsx

export function ScanDashboard({ scanId }: { scanId: string }) {
  const [scan, setScan] = useState<any>(null);
  const [authPhaseStatus, setAuthPhaseStatus] = useState<'pending' | 'validating' | 'success' | 'failed'>('pending');

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/scans/${scanId}/ws`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.phase === 'authenticating' || data.phase === 'authenticated') {
        setAuthPhaseStatus(data.phase === 'authenticated' ? 'success' : 'validating');
      }
      
      setScan(data.scan_data);
    };

    return () => ws.close();
  }, [scanId]);

  return (
    <div className="space-y-6">
      {/* Auth Context Display */}
      {scan?.authenticated_user && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900">Gray-Box Context</h3>
          <p className="text-sm text-blue-700 mt-2">
            Authenticated as: <span className="font-mono">{scan.authenticated_user}</span>
          </p>
          <p className="text-sm text-blue-700">
            Privilege Level: <span className="font-mono">{scan.privilege_level}</span>
          </p>
          <p className="text-sm text-blue-700">
            Auth Findings: <span className="font-mono">{scan.auth_findings_count}</span>
          </p>
          <p className="text-sm text-blue-700">
            Privilege Escalation Vulns: <span className="font-mono">{scan.privilege_escalation_vulns}</span>
          </p>
        </div>
      )}

      {/* Regular scan progress */}
      {/* ... existing dashboard code ... */}
    </div>
  );
}
```

---

## API Changes

### 1. Updated `POST /api/v1/scans/` Endpoint

```python
# backend/app/api/v1/endpoints/scans.py (updated)

@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,  # Now includes optional auth_config
    db: Session = Depends(get_db)
):
    """
    Create and start a new security scan
    
    Request Body:
    {
      "target_url": "https://example.com",
      "scan_type": "full",
      "auth_config": {
        "auth_enabled": true,
        "auth_method": "form_login",
        "login_url": "https://example.com/login",
        "username": "testuser",
        "password": "password123",
        "mfa_enabled": false
      }
    }
    """
    try:
        new_scan_id = str(uuid.uuid4())

        scan = Scan(
            scan_id=new_scan_id,
            target_url=str(scan_data.target_url),
            scan_type=scan_data.scan_type or "full",
            status=ScanStatus.PENDING,
            progress_percentage=0,
            current_phase="initializing",
            created_at=datetime.utcnow(),
        )
        db.add(scan)
        db.commit()

        orchestrator = OrchestratorService()
        result = await orchestrator.start_scan(
            scan_id=new_scan_id,
            target_url=str(scan_data.target_url),
            scan_type=scan_data.scan_type or "full",
            user_id="local-user",
            policy=scan_data.test_config or {},
            auth_config=scan_data.auth_config  # NEW parameter
        )

        if not result.get("success"):
            scan.status = ScanStatus.FAILED
            scan.error_message = result.get("message")
            db.commit()
            raise HTTPException(status_code=400, detail=scan.error_message)

        scan.status = ScanStatus.RUNNING
        db.commit()

        return scan

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. New `GET /api/v1/scans/{scan_id}/auth-status` Endpoint

```python
@router.get("/{scan_id}/auth-status")
async def get_auth_status(scan_id: str, db: Session = Depends(get_db)):
    """Get authentication status for a scan"""
    from app.models.models import AuthConfig as AuthConfigModel
    
    auth_config = db.query(AuthConfigModel).filter(
        AuthConfigModel.scan_id == scan_id
    ).first()
    
    if not auth_config:
        return {"auth_enabled": False}
    
    return {
        "auth_enabled": auth_config.auth_enabled,
        "auth_method": auth_config.auth_method,
        "auth_validation_status": auth_config.auth_validation_status,
        "authenticated_user": auth_config.authenticated_user,
        "privilege_level": auth_config.privilege_level,
        "error": auth_config.auth_validation_error
    }
```

### 3. New `POST /api/v1/scans/validate-auth` Endpoint

```python
@router.post("/validate-auth")
async def validate_auth(
    target_url: str,
    auth_config: AuthConfig
):
    """
    Validate authentication without starting a full scan
    Useful for testing credentials before committing to a scan
    """
    auth_service = AuthenticationService()
    result = await auth_service.validate_and_authenticate(
        scan_id="test-" + str(uuid.uuid4()),
        auth_config=auth_config,
        db=None
    )
    
    return {
        "success": result.get("success"),
        "auth_method": result.get("auth_method"),
        "privilege_level": result.get("privilege_level"),
        "error": result.get("error")
    }
```

---

## Data Collection Strategy

### Additional Data to Collect in Gray-Box Scans

#### 1. **Session & Authentication Data**
- Session cookies (with HTTPOnly, Secure, SameSite flags)
- JWT tokens / OAuth tokens (expiration, scopes, claims)
- Session lifetime and idle timeout behavior
- Session fixation vulnerabilities
- Session management bypass techniques

#### 2. **User Context & Privilege Data**
- Authenticated user identifier and roles
- Permission/capability set for the user
- Account enumeration data
- Multi-user workflows and collaboration features
- Cross-user authorization checks

#### 3. **Restricted Endpoints & Workflows**
- Admin panels and dashboards (URLs, features, data)
- User management endpoints (CRUD, bulk operations)
- Privilege escalation attack surface
- Business logic flows (workflows, state transitions)
- Finance/billing endpoints (if applicable)

#### 4. **API Authorization Data**
- API endpoints requiring specific roles
- API key / token scopes
- Rate limiting per privilege level
- Resource-level authorization checks
- Cross-account/org access boundaries

#### 5. **Data Access Patterns**
- Data visibility by privilege level
- Personal data access (own data vs. others)
- Aggregation/export capabilities restricted by role
- Logging/audit data visibility
- Configuration access by privilege level

#### 6. **Advanced Vulnerability Classes**
- Broken access control (horizontal + vertical escalation)
- Sensitive business logic flaws
- IDOR (Insecure Direct Object References) with auth context
- Parameter pollution in authenticated context
- API abuse scenarios (bulk operations, export attacks)

---

## End-to-End Flow Diagrams

### Gray-Box Scan Flow

```
User Interface (Frontend)
        │
        │ 1. Submit scan form
        │    ├─ target_url
        │    ├─ scan_type
        │    ├─ auth_config (if enabled)
        │    │  ├─ auth_method
        │    │  ├─ username/password (encrypted)
        │    │  └─ mfa_secret (if needed)
        │    └─ scope_config
        │
        ▼
POST /api/v1/scans/
        │
        │ 2. Create Scan record (PostgreSQL)
        │    └─ status: PENDING
        │
        ▼
OrchestratorService.start_scan()
        │
        │ 3. AUTH PHASE (NEW - Phase 0)
        │    ├─ Call AuthenticationService
        │    ├─ Decrypt credentials
        │    ├─ Attempt login via Playwright/aiohttp
        │    ├─ Extract session cookies/tokens
        │    ├─ Determine privilege level
        │    ├─ Store session in Redis: session:{scan_id}
        │    └─ Update scan: authenticated_user, privilege_level
        │
        ├─ Auth success? ─Yes─→ Continue with phases 1-7 (with auth context)
        │                       │
        │                       ├─ Phase 1: HTTP Probing
        │                       │  └─ Include session in headers/cookies
        │                       │
        │                       ├─ Phase 2: Crawling (Katana)
        │                       │  └─ Discover authenticated endpoints
        │                       │
        │                       ├─ Phase 3: Tech Detection
        │                       │
        │                       ├─ Phase 4: Nuclei Templates
        │                       │  └─ Use authenticated templates
        │                       │
        │                       ├─ Phase 5: Form Discovery
        │                       │  └─ Include restricted forms
        │                       │
        │                       ├─ Phase 6: Privilege Escalation Testing
        │                       │  └─ Test IDOR, horizontal escalation
        │                       │
        │                       └─ Phase 7: Report Generation
        │                          └─ Include auth context findings
        │
        └─ Auth failed? ─No──→ Continue unauthenticated (downgrade to black-box)
                               │
                               └─ Phases 1-7 (public surface only)
        │
        ▼
Dashboard Updates (WebSocket)
        │
        ├─ Real-time progress
        ├─ Auth status: authenticating → authenticated/failed
        ├─ Current phase: http_probing, crawling, etc.
        ├─ Findings count
        │  ├─ General findings
        │  ├─ Auth findings
        │  └─ Privilege escalation vulns
        │
        ▼
Report Generation
        │
        ├─ Include "Gray-Box Context" section
        │  ├─ Authenticated as: username
        │  ├─ Privilege Level: user/admin
        │  └─ Attack surface increase: X% additional
        │
        ├─ Tag findings with auth requirements
        │  ├─ Requires: public/authenticated/admin
        │  └─ Can escalate to: admin/system
        │
        └─ Generate actionable recommendations
           ├─ Privilege escalation remediation
           ├─ Authorization bypass fixes
           └─ Enhanced mitigations
```

---

## Security Considerations

### 1. **Credential Storage & Encryption**
- **Requirement:** All credentials must be encrypted at rest
- **Implementation:**
  ```python
  from cryptography.fernet import Fernet
  
  # .env
  ENCRYPTION_KEY = "your-key-base64-encoded"
  
  # Usage
  cipher = Fernet(ENCRYPTION_KEY.encode())
  encrypted = cipher.encrypt(password.encode()).decode()
  decrypted = cipher.decrypt(encrypted.encode()).decode()
  ```
- **Key Rotation:** Implement periodic key rotation for long-running systems

### 2. **Session Isolation**
- Sessions stored in Redis with TTL (scan duration + buffer)
- Session data scoped to scan_id (no cross-scan leakage)
- Automatic cleanup on scan completion

### 3. **Audit Logging**
- Log all auth attempts (success/failure)
- Log privilege levels detected
- Log findings discovered in authenticated context
- No logging of plaintext credentials

### 4. **Rate Limiting During Auth**
- Rate limit login attempts (3-5 per scan)
- Backoff on repeated failures
- Alert on suspicious patterns

### 5. **Credential Sanitization**
- Remove credentials from logs and reports
- Never return plaintext credentials in API responses
- Sanitize WebSocket updates

### 6. **MFA Support Limitations**
- TOTP: Fully supported (secrets provided in config)
- SMS/Email: Requires manual intervention or saved codes
- Hardware keys: Out of scope for now

### 7. **SSL/TLS Certificate Validation**
- Default: validate certificates (prevent MITM)
- Option: disable validation for testing (with warning)

---

## Implementation Roadmap

### **Phase 1: Foundation (Week 1-2)**
- [ ] Add `AuthConfig` schema + database tables
- [ ] Create `AuthenticationService` (form login + API key methods)
- [ ] Implement credential encryption/decryption
- [ ] Add session storage (Redis)
- [ ] Update `ScanCreate` to include `auth_config`
- [ ] Update API `/scans/` endpoint

### **Phase 2: Authentication Methods (Week 2-3)**
- [ ] Form-based login (Playwright)
- [ ] API key authentication
- [ ] Bearer token authentication
- [ ] Basic auth
- [ ] TOTP/MFA support

### **Phase 3: Integration (Week 3-4)**
- [ ] Integrate auth service into `ReconAgent`
- [ ] Update tools (httpx, katana, nuclei) to use auth session
- [ ] Implement privilege level detection
- [ ] Add auth telemetry tracking

### **Phase 4: Frontend (Week 4-5)**
- [ ] Enhance ScanForm with auth tabs
- [ ] Add credential input fields
- [ ] MFA UI components
- [ ] Auth validation/testing button

### **Phase 5: Advanced Features (Week 5-6)**
- [ ] Privilege escalation testing module
- [ ] Authorization bypass detection
- [ ] IDOR testing with multiple users (if available)
- [ ] API scope/permission testing

### **Phase 6: Reporting & Analytics (Week 6-7)**
- [ ] Add "Gray-Box Context" section to reports
- [ ] Tag findings by privilege requirement
- [ ] Generate escalation paths in report
- [ ] Dashboard enhancements

### **Phase 7: Testing & Documentation (Week 7-8)**
- [ ] End-to-end testing with sample apps
- [ ] Security audit of auth implementation
- [ ] Documentation & user guide
- [ ] Runbook for common auth types

---

## Success Criteria

✅ **Authentication Phase**
- Successfully authenticate to target app (form, API, OAuth)
- Extract and reuse session cookies/tokens
- Detect privilege level automatically
- Store sessions securely in Redis

✅ **Scan Execution**
- All scan phases work with authenticated context
- Tools (httpx, katana, nuclei) receive session data
- Additional endpoints discovered in authenticated context
- Privilege escalation vulnerabilities detected

✅ **Reporting**
- Reports include gray-box context (user, privilege level)
- Findings tagged with auth requirements
- Actionable recommendations for auth issues
- Clear before/after comparison (black-box vs gray-box findings)

✅ **Security**
- No plaintext credentials in logs/storage
- Credentials encrypted using Fernet
- Sessions isolated per scan
- Audit trail for all auth attempts

---

## Example: Running a Gray-Box Scan

### 1. **Request:**
```bash
curl -X POST http://localhost:8000/api/v1/scans/ \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://juice-shop.herokuapp.com",
    "scan_type": "full",
    "auth_config": {
      "auth_enabled": true,
      "auth_method": "form_login",
      "login_url": "https://juice-shop.herokuapp.com/#/login",
      "username": "demo@juice-shop.com",
      "password": "demo123",
      "mfa_enabled": false
    }
  }'
```

### 2. **Response:**
```json
{
  "scan_id": "abc-123-xyz",
  "target_url": "https://juice-shop.herokuapp.com",
  "scan_type": "full",
  "status": "running",
  "authenticated_user": "demo@juice-shop.com",
  "privilege_level": "authenticated_user",
  "progress_percentage": 5,
  "current_phase": "authenticating"
}
```

### 3. **WebSocket Updates:**
```json
{
  "phase": "authenticating",
  "message": "Attempting login to https://juice-shop.herokuapp.com/#/login",
  "timestamp": "2026-06-01T10:30:00Z"
}

{
  "phase": "authenticated",
  "message": "Successfully authenticated as demo@juice-shop.com (authenticated_user)",
  "authenticated_user": "demo@juice-shop.com",
  "privilege_level": "authenticated_user",
  "timestamp": "2026-06-01T10:30:05Z"
}

{
  "phase": "http_probing",
  "message": "Probing HTTP endpoints (with auth context)",
  "progress": 10,
  "timestamp": "2026-06-01T10:30:10Z"
}

{
  "phase": "crawling",
  "message": "Discovered 42 authenticated endpoints (+ 18 new vs black-box)",
  "progress": 25,
  "timestamp": "2026-06-01T10:31:00Z"
}

{
  "phase": "privilege_escalation_testing",
  "message": "Testing privilege escalation vectors...",
  "progress": 60,
  "timestamp": "2026-06-01T10:33:00Z"
}

{
  "phase": "completed",
  "total_findings": 34,
  "auth_findings": 12,
  "privilege_escalation_vulns": 3,
  "timestamp": "2026-06-01T10:35:00Z"
}
```

### 4. **Report Section (Excerpt):**
```
## Gray-Box Testing Context

**Authentication Status:** ✓ Success

- **Authenticated As:** demo@juice-shop.com
- **Privilege Level:** User (Authenticated)
- **Attack Surface Increase:** +45% (18 additional endpoints discovered)

**Key Findings:**

1. **Horizontal Privilege Escalation (High)**
   - **Finding:** User can access other users' profiles via IDOR
   - **Requires:** Authenticated context
   - **Impact:** Sensitive data disclosure
   - **Recommendation:** Implement per-user authorization checks

2. **Privilege Escalation to Admin (Critical)**
   - **Finding:** Role attribute injectable via API
   - **Requires:** Authenticated context
   - **Impact:** Full admin access
   - **Recommendation:** Implement server-side role validation

3. **Sensitive Data Exposure (Medium)**
   - **Finding:** User dashboard exposes sensitive metrics not in public API
   - **Requires:** Authenticated context
   - **Impact:** Information disclosure
   - **Recommendation:** Add data masking per role
```

---

## Conclusion

This gray-box implementation plan transforms NeuroPentWeb from a public-surface-only scanner into a comprehensive authenticated vulnerability assessment tool. By supporting multiple authentication methods, MFA, session management, and privilege escalation testing, the system can now discover and validate a significantly larger portion of the attack surface.

**Next Steps:**
1. Review and approve this plan
2. Begin Phase 1 implementation (database schema + auth service)
3. Set up development environment with test application
4. Iterate through phases with continuous testing

