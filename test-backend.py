#!/usr/bin/env python3
"""Quick test of backend API status"""

import requests
import json
import sys

endpoints = [
    ("Health Check", "http://localhost:8000/health"),
    ("API Docs", "http://localhost:8000/api/v1/docs"),
    ("API OpenAPI", "http://localhost:8000/openapi.json"),
]

print("\n" + "="*60)
print("  NeuroPentWeb Backend - Service Status Check")
print("="*60 + "\n")

all_ok = True
for name, url in endpoints:
    try:
        response = requests.get(url, timeout=2)
        status = f"✅ {response.status_code}" if response.status_code == 200 else f"⚠️  {response.status_code}"
        print(f"{name:.<40} {status}")
        if response.status_code != 200:
            all_ok = False
    except requests.exceptions.ConnectionError:
        print(f"{name:.<40} ❌ Connection refused")
        all_ok = False
    except requests.exceptions.Timeout:
        print(f"{name:.<40} ⏱️  Timeout")
        all_ok = False
    except Exception as e:
        print(f"{name:.<40} ❌ {str(e)}")
        all_ok = False

print("\n" + "="*60)

if all_ok:
    print("✅ Backend is running and responding!")
    print("\nAccess points:")
    print("  - API Documentation: http://localhost:8000/api/v1/docs")
    print("  - Frontend: http://localhost:5173 (if running)")
    print("  - PostgreSQL: localhost:5432")
    print("  - Redis: localhost:6379")
    print("\nMissing services (will use graceful degradation):")
    print("  - Neo4j: bolt://localhost:7687")
    print("  - Ollama: http://localhost:11434")
    print("  - MinIO: http://localhost:9000")
else:
    print("⚠️  Backend may not be responding correctly")
    print("\nMake sure:")
    print("  1. Backend process is running")
    print("  2. PostgreSQL and Redis are accessible")
    print("  3. Port 8000 is not blocked by firewall")
    sys.exit(1)

print("\n")
