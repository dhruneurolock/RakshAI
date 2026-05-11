#!/usr/bin/env python3
"""
NeuroPentWeb Local Development Setup Verification Script

Verifies that the local development environment is properly configured:
- Python virtual environment
- Package dependencies
- Node.js and npm
- Frontend dependencies
- Database configuration
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")


def check_python_venv():
    """Check if Python virtual environment is set up"""
    print_header("Checking Python Virtual Environment")
    
    venv_path = Path("backend/.venv")
    if venv_path.exists():
        print_success(f"Virtual environment found at {venv_path}")
        return True
    else:
        print_error(f"Virtual environment not found at {venv_path}")
        print_info("To create it, run:")
        print("  cd backend")
        print("  python -m venv .venv")
        return False


def check_python_packages():
    """Check if required Python packages are installed"""
    print_header("Checking Python Packages")
    
    venv_python = Path("backend/.venv/Scripts/python.exe")
    if not venv_python.exists():
        print_error("Virtual environment Python executable not found")
        return False
    
    try:
        # Check key packages
        packages = ["fastapi", "uvicorn", "sqlalchemy", "alembic"]
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            installed = json.loads(result.stdout)
            installed_names = {pkg["name"].lower() for pkg in installed}
            
            all_found = True
            for pkg in packages:
                if pkg.lower() in installed_names:
                    print_success(f"{pkg} is installed")
                else:
                    print_warning(f"{pkg} is NOT installed")
                    all_found = False
            
            if not all_found:
                print_info("To install missing packages, run:")
                print("  cd backend")
                print("  .venv\\Scripts\\activate.bat")
                print("  pip install -r requirements.txt")
            
            return all_found
        else:
            print_error(f"Failed to check packages: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Error checking packages: {e}")
        return False


def check_nodejs():
    """Check if Node.js and npm are installed"""
    print_header("Checking Node.js & npm")
    
    try:
        node_result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        npm_result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if node_result.returncode == 0:
            print_success(f"Node.js {node_result.stdout.strip()} found")
        else:
            print_error("Node.js not found")
            return False
        
        if npm_result.returncode == 0:
            print_success(f"npm {npm_result.stdout.strip()} found")
        else:
            print_error("npm not found")
            return False
        
        return True
    except FileNotFoundError:
        print_error("Node.js or npm not found in PATH")
        print_info("Visit https://nodejs.org/ to install")
        return False
    except Exception as e:
        print_error(f"Error checking Node.js: {e}")
        return False


def check_frontend_dependencies():
    """Check if frontend dependencies are installed"""
    print_header("Checking Frontend Dependencies")
    
    node_modules = Path("frontend/node_modules")
    package_lock = Path("frontend/package-lock.json")
    
    if node_modules.exists():
        print_success("node_modules directory found")
        return True
    else:
        print_warning("node_modules directory not found")
        if package_lock.exists():
            print_info("To install dependencies, run:")
            print("  cd frontend")
            print("  npm install")
        else:
            print_info("To initialize dependencies, run:")
            print("  cd frontend")
            print("  npm install")
        return False


def check_env_files():
    """Check if .env files are configured"""
    print_header("Checking Environment Configuration Files")
    
    backend_env = Path("backend/.env")
    backend_example = Path("backend/.env.local.example")
    frontend_env = Path("frontend/.env.local")
    frontend_example = Path("frontend/.env.local.example")
    
    backend_ok = backend_env.exists()
    if backend_ok:
        print_success("backend/.env found")
    elif backend_example.exists():
        print_warning("backend/.env not found (using example template)")
    else:
        print_error("backend/.env and .env.local.example not found")
    
    frontend_ok = frontend_env.exists()
    if frontend_ok:
        print_success("frontend/.env.local found")
    elif frontend_example.exists():
        print_warning("frontend/.env.local not found")
        print_info("To create it:")
        print("  copy frontend\\.env.local.example frontend\\.env.local")
    else:
        print_error("frontend/.env.local and .env.local.example not found")
    
    return backend_ok and frontend_ok


def check_database():
    """Check database configuration"""
    print_header("Checking Database Configuration")
    
    backend_env = Path("backend/.env")
    if backend_env.exists():
        with open(backend_env, 'r') as f:
            content = f.read()
            if "sqlite:///" in content:
                print_success("SQLite database configured (local development)")
            elif "postgresql://" in content:
                print_warning("PostgreSQL configured (remote database)")
            else:
                print_warning("Database type unclear from .env")
    else:
        print_info("backend/.env not found - using defaults")
    
    return True


def main():
    """Run all checks"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  NeuroPentWeb Local Development Setup Verification".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    checks = [
        ("Python Virtual Environment", check_python_venv),
        ("Python Packages", check_python_packages),
        ("Node.js & npm", check_nodejs),
        ("Frontend Dependencies", check_frontend_dependencies),
        ("Environment Files", check_env_files),
        ("Database Configuration", check_database),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_error(f"Unexpected error in {name}: {e}")
            results[name] = False
    
    # Summary
    print_header("Setup Verification Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print_success("Your local development environment is ready!")
        print("\nTo start the servers, run:")
        print("  powershell -ExecutionPolicy Bypass -File start-local-dev.ps1")
        print("  OR")
        print("  start-local-dev.bat")
        return 0
    else:
        print_warning("Please fix the issues above before starting development")
        return 1


if __name__ == "__main__":
    sys.exit(main())
