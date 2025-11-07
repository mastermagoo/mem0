#!/usr/bin/env python3
"""
Test script for mem0 Telegram bot
Validates bot functionality without requiring Telegram interaction
"""
import sys
import os
import time
from mem0_client import Mem0Client
from config import config

def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    try:
        assert config.telegram_token is not None, "TELEGRAM_BOT_TOKEN not set"
        assert config.mem0_url is not None, "MEM0_URL not set"
        assert len(config.namespaces) > 0, "No namespaces configured"
        print("✅ Configuration loaded successfully")
        print(f"   mem0 URL: {config.mem0_url}")
        print(f"   Default namespace: {config.default_namespace}")
        print(f"   User prefix: {config.user_prefix}")
        print(f"   Namespaces: {', '.join(config.namespaces)}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_mem0_connection():
    """Test connection to mem0 server"""
    print("\nTesting mem0 server connection...")
    try:
        client = Mem0Client(config.mem0_url, config.mem0_api_key)
        health = client.health_check()

        if health['status'] == 'healthy':
            print("✅ mem0 server is healthy")
            print(f"   Response: {health.get('details', {})}")
            return True
        else:
            print(f"❌ mem0 server unhealthy: {health.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to mem0: {e}")
        return False

def test_memory_operations():
    """Test basic memory operations"""
    print("\nTesting memory operations...")
    client = Mem0Client(config.mem0_url, config.mem0_api_key)
    test_namespace = "personal"
    user_id = config.get_full_user_id(test_namespace)

    # Test 1: Store memory
    print("  Testing memory storage...")
    try:
        test_content = f"Test memory from bot test script - {int(time.time())}"
        result = client.store_memory(
            user_id=user_id,
            content=test_content,
            metadata={'source': 'test_script'}
        )
        memory_id = result.get('id')
        print(f"  ✅ Stored memory: {memory_id}")
    except Exception as e:
        print(f"  ❌ Failed to store memory: {e}")
        return False

    # Wait a moment for indexing
    time.sleep(1)

    # Test 2: Search memory
    print("  Testing memory search...")
    try:
        memories = client.search_memories(
            user_id=user_id,
            query="test memory bot test script",
            limit=5
        )
        if len(memories) > 0:
            print(f"  ✅ Found {len(memories)} memories")
            for i, mem in enumerate(memories[:3], 1):
                if isinstance(mem, dict):
                    content = mem.get('memory', mem.get('content', str(mem)))
                    print(f"     {i}. {content[:80]}")
        else:
            print("  ⚠️ No memories found (may be indexing delay)")
    except Exception as e:
        print(f"  ❌ Failed to search memories: {e}")
        return False

    # Test 3: Get all memories
    print("  Testing get all memories...")
    try:
        all_memories = client.get_all_memories(user_id)
        print(f"  ✅ Retrieved {len(all_memories)} total memories in '{test_namespace}'")
    except Exception as e:
        print(f"  ❌ Failed to get all memories: {e}")
        return False

    return True

def test_namespace_isolation():
    """Test that namespaces are properly isolated"""
    print("\nTesting namespace isolation...")
    client = Mem0Client(config.mem0_url, config.mem0_api_key)

    namespace1 = "personal"
    namespace2 = "progressief"

    user_id_1 = config.get_full_user_id(namespace1)
    user_id_2 = config.get_full_user_id(namespace2)

    # Store unique memory in each namespace
    timestamp = int(time.time())
    content1 = f"Unique memory for {namespace1} - {timestamp}"
    content2 = f"Unique memory for {namespace2} - {timestamp}"

    try:
        print(f"  Storing memory in '{namespace1}'...")
        client.store_memory(user_id=user_id_1, content=content1)

        print(f"  Storing memory in '{namespace2}'...")
        client.store_memory(user_id=user_id_2, content=content2)

        time.sleep(1)  # Wait for indexing

        # Search in namespace1 for namespace2 content
        print(f"  Searching '{namespace1}' for '{namespace2}' content...")
        memories1 = client.search_memories(
            user_id=user_id_1,
            query=content2,
            limit=10
        )

        # Should not find namespace2 memory in namespace1
        found_in_wrong_namespace = any(
            content2 in str(mem) for mem in memories1
        )

        if not found_in_wrong_namespace:
            print("  ✅ Namespace isolation working correctly")
            return True
        else:
            print("  ❌ Namespace isolation failed - memories leaked between namespaces")
            return False

    except Exception as e:
        print(f"  ❌ Namespace isolation test failed: {e}")
        return False

def test_stats():
    """Test stats retrieval for all namespaces"""
    print("\nTesting statistics retrieval...")
    client = Mem0Client(config.mem0_url, config.mem0_api_key)

    try:
        total = 0
        for namespace in config.namespaces:
            user_id = config.get_full_user_id(namespace)
            stats = client.get_stats(user_id)
            count = stats.get('total_memories', 0)
            total += count
            print(f"  {namespace}: {count} memories")

        print(f"  ✅ Total: {total} memories across all namespaces")
        return True
    except Exception as e:
        print(f"  ❌ Failed to get stats: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("mem0 Telegram Bot - Test Suite")
    print("=" * 60)

    tests = [
        ("Configuration", test_config),
        ("mem0 Connection", test_mem0_connection),
        ("Memory Operations", test_memory_operations),
        ("Namespace Isolation", test_namespace_isolation),
        ("Statistics", test_stats),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed! Bot is ready to use.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Review errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
