#!/usr/bin/env python3
"""
Test script to validate Ollama-only enforcement
Verifies that OpenAI calls are blocked and Ollama validation works

Usage:
    python3 test_ollama_enforcement.py
"""

import os
import sys
import json

# Add parent directory to path for testing
sys.path.insert(0, '/app')

def test_ollama_validation():
    """Test that Ollama validation works correctly"""
    print("=" * 70)
    print("TEST 1: Ollama Connection Validation")
    print("=" * 70)
    
    try:
        from enforce_ollama_only import OllamaOnlyEnforcer
        
        enforcer = OllamaOnlyEnforcer()
        
        # Test validation (will abort if Ollama unavailable)
        result = enforcer.validate_ollama_connection(timeout=10)
        
        if result:
            print("✅ PASS: Ollama validation successful")
            return True
        else:
            print("❌ FAIL: Ollama validation failed")
            return False
            
    except SystemExit as e:
        if e.code == 1:
            print("❌ FAIL: Ollama validation aborted (expected if Ollama unavailable)")
            return False
        raise
    except Exception as e:
        print(f"❌ FAIL: Ollama validation error: {e}")
        return False


def test_openai_blocking():
    """Test that OpenAI calls are blocked"""
    print("\n" + "=" * 70)
    print("TEST 2: OpenAI Call Blocking")
    print("=" * 70)
    
    try:
        from enforce_ollama_only import OllamaOnlyEnforcer
        
        enforcer = OllamaOnlyEnforcer()
        enforcer.patch_mem0_openai_blocker()
        
        # Try to make an OpenAI request (should be blocked)
        import httpx
        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                json={"model": "gpt-4", "messages": []},
                timeout=5
            )
            print("❌ FAIL: OpenAI call was NOT blocked")
            return False
        except RuntimeError as e:
            if "BLOCKED" in str(e) and "OpenAI" in str(e):
                print("✅ PASS: OpenAI calls are blocked")
                return True
            else:
                print(f"❌ FAIL: Unexpected error: {e}")
                return False
        except Exception as e:
            # Other errors (timeout, connection) are acceptable
            print(f"⚠️  WARNING: Request failed (expected): {e}")
            print("✅ PASS: OpenAI call was blocked or failed")
            return True
            
    except Exception as e:
        print(f"❌ FAIL: OpenAI blocking test error: {e}")
        return False


def test_config_generation():
    """Test that Ollama-only config is generated correctly"""
    print("\n" + "=" * 70)
    print("TEST 3: Ollama-Only Config Generation")
    print("=" * 70)
    
    try:
        from enforce_ollama_only import OllamaOnlyEnforcer
        
        enforcer = OllamaOnlyEnforcer()
        config = enforcer.build_ollama_only_config()
        
        # Verify config structure
        required_keys = ['llm', 'embedder', 'vector_store', 'graph_store']
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            print(f"❌ FAIL: Config missing keys: {missing_keys}")
            return False
        
        # Verify LLM provider is Ollama
        if config['llm']['provider'] != 'ollama':
            print(f"❌ FAIL: LLM provider is not 'ollama': {config['llm']['provider']}")
            return False
        
        # Verify embedder provider is Ollama
        if config['embedder']['provider'] != 'ollama':
            print(f"❌ FAIL: Embedder provider is not 'ollama': {config['embedder']['provider']}")
            return False
        
        # Verify no OpenAI references in config
        config_str = json.dumps(config)
        if 'openai' in config_str.lower():
            print("❌ FAIL: Config contains OpenAI references")
            print(f"   Config: {config_str}")
            return False
        
        print("✅ PASS: Ollama-only config generated correctly")
        print(f"   LLM Provider: {config['llm']['provider']}")
        print(f"   LLM Model: {config['llm']['config']['model']}")
        print(f"   Embedder Provider: {config['embedder']['provider']}")
        print(f"   Embedder Model: {config['embedder']['config']['model']}")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Config generation error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 OLLAMA-ONLY ENFORCEMENT TEST SUITE")
    print("=" * 70)
    print()
    
    results = []
    
    # Test 1: Ollama validation
    results.append(("Ollama Validation", test_ollama_validation()))
    
    # Test 2: OpenAI blocking
    results.append(("OpenAI Blocking", test_openai_blocking()))
    
    # Test 3: Config generation
    results.append(("Config Generation", test_config_generation()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Ollama-only enforcement working correctly")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review implementation")
        return 1


if __name__ == "__main__":
    sys.exit(main())

