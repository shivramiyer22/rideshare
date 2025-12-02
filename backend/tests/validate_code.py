"""
Code validation script - checks code structure and imports without requiring dependencies.
Run this to validate the code before installing dependencies.
"""
import ast
import sys
from pathlib import Path


def check_file_imports(file_path):
    """Check if a file can be parsed and has valid Python syntax."""
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def check_config_values():
    """Check if config.py has the expected structure."""
    config_path = Path(__file__).parent.parent / "app" / "config.py"
    
    if not config_path.exists():
        return False, "config.py not found"
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    checks = {
        "MONGO_URI": "MONGO_URI" in content,
        "MONGO_DB_NAME": "MONGO_DB_NAME" in content,
        "redis_url property": "def redis_url" in content or "@property" in content and "redis_url" in content,
        "Docker override": "redis://redis" in content or "localhost" in content,
        "env_file": "env_file" in content,
        "extra = ignore": "extra = \"ignore\"" in content or "extra='ignore'" in content,
    }
    
    failed = [k for k, v in checks.items() if not v]
    if failed:
        return False, f"Missing: {', '.join(failed)}"
    
    return True, "All config checks passed"


def check_priority_queue_structure():
    """Check if priority_queue.py has Redis implementation."""
    pq_path = Path(__file__).parent.parent / "app" / "priority_queue.py"
    
    if not pq_path.exists():
        return False, "priority_queue.py not found"
    
    with open(pq_path, 'r') as f:
        content = f.read()
    
    checks = {
        "Redis import": "get_redis" in content or "redis" in content.lower(),
        "P0 LIST": "P0_KEY" in content and "lpush" in content.lower() and "rpop" in content.lower(),
        "P1 SORTED SET": "P1_KEY" in content and "zadd" in content.lower() and "zrevrange" in content.lower(),
        "P2 SORTED SET": "P2_KEY" in content and "zadd" in content.lower() and "zrevrange" in content.lower(),
        "add_order method": "def add_order" in content or "async def add_order" in content,
        "get_next_p0_order": "get_next_p0_order" in content,
        "get_next_p1_order": "get_next_p1_order" in content,
        "get_next_p2_order": "get_next_p2_order" in content,
        "No in-memory list": "self.queue: List" not in content and "self.queue = []" not in content,
    }
    
    failed = [k for k, v in checks.items() if not v]
    if failed:
        return False, f"Missing: {', '.join(failed)}"
    
    return True, "All priority queue checks passed"


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("CODE VALIDATION CHECKS")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Check Python syntax
    print("1. Checking Python syntax...")
    files_to_check = [
        "app/config.py",
        "app/database.py",
        "app/redis_client.py",
        "app/priority_queue.py",
        "app/main.py",
    ]
    
    syntax_ok = True
    for file_rel in files_to_check:
        file_path = Path(__file__).parent.parent / file_rel
        if file_path.exists():
            ok, error = check_file_imports(file_path)
            if ok:
                print(f"   ✓ {file_rel}")
            else:
                print(f"   ✗ {file_rel}: {error}")
                syntax_ok = False
        else:
            print(f"   ✗ {file_rel}: File not found")
            syntax_ok = False
    
    results["syntax"] = syntax_ok
    print()
    
    # Check config structure
    print("2. Checking config.py structure...")
    ok, msg = check_config_values()
    if ok:
        print(f"   ✓ {msg}")
    else:
        print(f"   ✗ {msg}")
    results["config"] = ok
    print()
    
    # Check priority queue structure
    print("3. Checking priority_queue.py structure...")
    ok, msg = check_priority_queue_structure()
    if ok:
        print(f"   ✓ {msg}")
    else:
        print(f"   ✗ {msg}")
    results["priority_queue"] = ok
    print()
    
    # Check requirements.txt
    print("4. Checking requirements.txt...")
    req_path = Path(__file__).parent.parent / "requirements.txt"
    if req_path.exists():
        with open(req_path, 'r') as f:
            req_content = f.read()
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "motor",
            "redis",
            "prophet",
            "langchain",
            "openai",
            "chromadb",
        ]
        
        missing = [pkg for pkg in required_packages if pkg not in req_content.lower()]
        if not missing:
            print(f"   ✓ All required packages in requirements.txt")
            results["requirements"] = True
        else:
            print(f"   ✗ Missing packages: {', '.join(missing)}")
            results["requirements"] = False
    else:
        print("   ✗ requirements.txt not found")
        results["requirements"] = False
    print()
    
    # Summary
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Python Syntax:      {'✓ PASS' if results['syntax'] else '✗ FAIL'}")
    print(f"Config Structure:   {'✓ PASS' if results['config'] else '✗ FAIL'}")
    print(f"Priority Queue:     {'✓ PASS' if results['priority_queue'] else '✗ FAIL'}")
    print(f"Requirements:       {'✓ PASS' if results['requirements'] else '✗ FAIL'}")
    print("=" * 60)
    
    if all(results.values()):
        print("\n✓ ALL CODE VALIDATION CHECKS PASSED!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Ensure MongoDB is accessible at the MONGO_URI from .env")
        print("3. Ensure Redis is running on localhost:6379")
        print("4. Run: python3 tests/test_connections.py")
        return 0
    else:
        print("\n✗ SOME VALIDATION CHECKS FAILED. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

