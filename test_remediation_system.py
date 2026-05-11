#!/usr/bin/env python3
"""
Test script for LLM-Based Remediation System

This script tests the remediation endpoint and generates sample remediation solutions.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
REMEDIATION_ENDPOINT = "/vulnerabilities/{vuln_id}/generate-remediation"

# Test vulnerability IDs (modify based on your database)
TEST_VULN_IDS = [621, 1, 2, 3]  # Add IDs from your scans


def check_api_health():
    """Check if backend API is running"""
    print("🔍 Checking API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/vulnerabilities/?limit=1", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
            return True
        else:
            print(f"❌ API returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API not responding: {e}")
        return False


def get_vulnerabilities():
    """Get list of vulnerabilities from database"""
    print("\n📋 Fetching vulnerabilities...")
    try:
        response = requests.get(f"{API_BASE_URL}/vulnerabilities/?limit=10", timeout=10)
        if response.status_code == 200:
            vulns = response.json()
            print(f"✅ Found {len(vulns)} vulnerabilities")
            return vulns
        else:
            print(f"❌ Failed to fetch: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def test_remediation(vuln_id):
    """Test remediation generation for a vulnerability"""
    print(f"\n🔄 Generating remediation for vulnerability {vuln_id}...")
    
    try:
        url = f"{API_BASE_URL}{REMEDIATION_ENDPOINT.format(vuln_id=vuln_id)}"
        
        start_time = datetime.now()
        response = requests.post(url, timeout=30)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"⏱️  Response time: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Remediation generated successfully!\n")
            
            # Display summary
            print(f"📌 Vulnerability: {data.get('vulnerability_type')}")
            print(f"🎯 Severity: {data.get('severity')}")
            print(f"💻 Technology: {data.get('technology_detected')}")
            
            remediation = data.get('remediation_solution', {})
            
            if remediation.get('executive_summary'):
                print(f"\n📝 Executive Summary:")
                print(f"   {remediation['executive_summary'][:200]}...")
            
            if remediation.get('root_cause'):
                print(f"\n🔍 Root Cause:")
                print(f"   {remediation['root_cause'][:200]}...")
            
            if remediation.get('remediation_steps'):
                print(f"\n✅ Remediation Steps: {len(remediation['remediation_steps'])} steps")
                for i, step in enumerate(remediation['remediation_steps'][:3], 1):
                    print(f"   {i}. {step}")
                if len(remediation['remediation_steps']) > 3:
                    print(f"   ... and {len(remediation['remediation_steps']) - 3} more steps")
            
            if remediation.get('code_example'):
                print(f"\n💻 Code Example:")
                lines = remediation['code_example'].split('\n')[:5]
                for line in lines:
                    print(f"   {line}")
                if len(remediation['code_example'].split('\n')) > 5:
                    print(f"   ...")
            
            if remediation.get('timeline'):
                print(f"\n⏱️  Timeline: {remediation['timeline']}")
            
            if remediation.get('urgency'):
                print(f"🚨 Urgency: {remediation['urgency']}")
            
            if remediation.get('references'):
                print(f"\n📚 References: {len(remediation['references'])} links")
                for ref in remediation['references'][:2]:
                    print(f"   {ref}")
            
            return True
            
        elif response.status_code == 404:
            print(f"❌ Vulnerability {vuln_id} not found")
            return False
        else:
            print(f"❌ Error ({response.status_code}): {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out (check if Ollama is running)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def save_full_response(vuln_id, response_data):
    """Save full remediation response to file"""
    filename = f"remediation_{vuln_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, 'w') as f:
            json.dump(response_data, f, indent=2)
        print(f"💾 Full response saved to: {filename}")
    except Exception as e:
        print(f"⚠️  Could not save response: {e}")


def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 LLM-Based Remediation System Test Suite")
    print("="*60)
    
    # Check health
    if not check_api_health():
        print("\n❌ Backend is not running. Start it with:")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    
    # Get vulnerabilities
    vulns = get_vulnerabilities()
    if not vulns:
        print("\n⚠️  No vulnerabilities found in database")
        print("    Run a scan first to generate vulnerabilities")
        return False
    
    # Test remediation on first vulnerability
    print("\n" + "-"*60)
    print("🚀 Testing Remediation Generation")
    print("-"*60)
    
    first_vuln = vulns[0]
    vuln_id = first_vuln.get('id')
    
    if test_remediation(vuln_id):
        print("\n✅ TEST PASSED - Remediation system is working!")
        
        # Offer to test more
        print("\n💡 Tips:")
        print(f"   • Test with other vulnerabilities: {[v.get('id') for v in vulns[:3]]}")
        print(f"   • API endpoint: POST {API_BASE_URL}/vulnerabilities/{{id}}/generate-remediation")
        print(f"   • View API docs: http://localhost:8000/api/v1/docs")
        
        return True
    else:
        print("\n❌ TEST FAILED")
        print("\nTroubleshooting:")
        print("   1. Check if Ollama is running:")
        print("      curl http://localhost:11434/api/tags")
        print("   2. Verify backend is running:")
        print("      curl http://localhost:8000/api/v1/docs")
        print("   3. Check for errors in backend logs")
        return False


def interactive_test():
    """Interactive testing mode"""
    print("\n" + "="*60)
    print("📋 Interactive Remediation Testing")
    print("="*60)
    
    if not check_api_health():
        print("❌ Backend is not running")
        return
    
    print("\nAvailable vulnerabilities:")
    vulns = get_vulnerabilities()
    
    if not vulns:
        print("No vulnerabilities found")
        return
    
    for v in vulns[:5]:
        print(f"  [{v.get('id')}] {v.get('title')} ({v.get('severity')})")
    
    try:
        vuln_id = int(input("\nEnter vulnerability ID to remediate: "))
        if test_remediation(vuln_id):
            save_file = input("\nSave full response to JSON file? (y/n): ")
            if save_file.lower() == 'y':
                response = requests.post(f"{API_BASE_URL}{REMEDIATION_ENDPOINT.format(vuln_id=vuln_id)}")
                if response.status_code == 200:
                    save_full_response(vuln_id, response.json())
    except ValueError:
        print("Invalid vulnerability ID")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_test()
    else:
        success = run_tests()
        sys.exit(0 if success else 1)
