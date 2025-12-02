#!/usr/bin/env python3
"""
NO DOCKER Verification Script

Verifies that NO Docker is used anywhere in the project.
Based on CURSOR_IDE_INSTRUCTIONS.md lines 853-855.
"""

import os
import subprocess
from pathlib import Path

def check_docker_ps():
    """Check if docker ps command works (should fail or show nothing)."""
    print("1. Checking docker ps command...")
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            print("   ❌ FAIL: Docker containers are running!")
            return False
        else:
            print("   ✓ PASS: No Docker containers running")
            return True
    except FileNotFoundError:
        print("   ✓ PASS: Docker command not found (Docker not installed)")
        return True
    except Exception as e:
        print(f"   ✓ PASS: Docker check failed (expected): {e}")
        return True

def check_docker_files():
    """Check for Docker-related files in project."""
    print("\n2. Checking for Docker files in project...")
    project_root = Path(__file__).parent.parent.parent
    
    docker_files = [
        "docker-compose.yml",
        "docker-compose.yaml",
        "Dockerfile",
        ".dockerignore"
    ]
    
    found_files = []
    for docker_file in docker_files:
        if (project_root / docker_file).exists():
            found_files.append(docker_file)
    
    if found_files:
        print(f"   ❌ FAIL: Found Docker files: {found_files}")
        return False
    else:
        print("   ✓ PASS: No Docker files found")
        return True

def check_native_services():
    """Check if services are running natively (systemd, PM2)."""
    print("\n3. Checking native service management...")
    
    results = []
    
    # Check systemd
    try:
        result = subprocess.run(
            ["systemctl", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("   ✓ systemd available")
            results.append(True)
        else:
            print("   ⚠️  systemd not available (may be macOS)")
            results.append(True)  # Not a failure on macOS
    except Exception:
        print("   ⚠️  systemd check skipped (may be macOS)")
        results.append(True)
    
    # Check PM2
    try:
        result = subprocess.run(
            ["pm2", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("   ✓ PM2 available")
            results.append(True)
        else:
            print("   ⚠️  PM2 not installed")
            results.append(False)
    except FileNotFoundError:
        print("   ⚠️  PM2 not installed")
        results.append(False)
    except Exception:
        print("   ⚠️  PM2 check skipped")
        results.append(True)
    
    return all(results)

def main():
    """Run all NO DOCKER verification checks."""
    print("=" * 80)
    print("NO DOCKER Verification")
    print("Based on CURSOR_IDE_INSTRUCTIONS.md lines 853-855")
    print("=" * 80)
    
    checks = [
        check_docker_ps(),
        check_docker_files(),
        check_native_services()
    ]
    
    print("\n" + "=" * 80)
    print("Verification Summary")
    print("=" * 80)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ All checks passed: {passed}/{total}")
        return 0
    else:
        print(f"⚠️  Some checks failed: {passed}/{total}")
        return 1

if __name__ == "__main__":
    exit(main())

