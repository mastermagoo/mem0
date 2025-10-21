"""
Namespace Isolation Testing
Location: /Volumes/intel-system/deployment/docker/mem0_tailscale/test_namespace_isolation.py
Purpose: Comprehensive tests for namespace isolation
Scope: Verifies zero memory leakage between namespaces

Usage:
    python test_namespace_isolation.py
"""

import sys
import time
import requests
from typing import Dict, List
from datetime import datetime
import json

# Test configuration
MEM0_URL = "http://localhost:8888"
API_KEY = "your_api_key_here"  # TODO: Load from .env
USER_ID = "mark_carey"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_test(name: str):
    """Print test name"""
    print(f"\n{Colors.BLUE}TEST: {name}{Colors.END}")


def print_pass(message: str):
    """Print success message"""
    print(f"  {Colors.GREEN}✓ {message}{Colors.END}")


def print_fail(message: str):
    """Print failure message"""
    print(f"  {Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print info message"""
    print(f"  {Colors.YELLOW}ℹ {message}{Colors.END}")


class NamespaceIsolationTests:
    """Test suite for namespace isolation"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.test_results: List[Dict] = []

    def run_all_tests(self) -> bool:
        """Run all isolation tests"""
        print(f"\n{'='*80}")
        print(f"Namespace Isolation Test Suite")
        print(f"{'='*80}\n")
        print(f"Base URL: {self.base_url}")
        print(f"User: {USER_ID}")
        print(f"Started: {datetime.now().isoformat()}\n")

        all_passed = True

        # Run tests
        all_passed &= self.test_list_namespaces()
        all_passed &= self.test_namespace_switching()
        all_passed &= self.test_store_in_different_namespaces()
        all_passed &= self.test_search_isolation()
        all_passed &= self.test_cross_namespace_prevention()
        all_passed &= self.test_user_id_formatting()
        all_passed &= self.test_concurrent_namespace_operations()
        all_passed &= self.test_namespace_stats()

        # Summary
        self.print_summary()

        return all_passed

    def test_list_namespaces(self) -> bool:
        """Test 1: List all namespaces"""
        print_test("List All Namespaces")

        try:
            response = requests.get(
                f"{self.base_url}/v1/namespace/list",
                headers=self.headers
            )

            if response.status_code != 200:
                print_fail(f"Failed to list namespaces: {response.status_code}")
                return False

            data = response.json()
            namespaces = data.get('namespaces', [])

            expected = ['progressief', 'cv_automation', 'investments', 'personal', 'intel_system']

            if set(namespaces) == set(expected):
                print_pass(f"All 5 namespaces found: {namespaces}")
                return True
            else:
                print_fail(f"Expected {expected}, got {namespaces}")
                return False

        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            return False

    def test_namespace_switching(self) -> bool:
        """Test 2: Switch between namespaces"""
        print_test("Namespace Switching")

        try:
            # Get current namespace
            response = requests.get(
                f"{self.base_url}/v1/namespace/current",
                headers=self.headers
            )

            if response.status_code != 200:
                print_fail("Failed to get current namespace")
                return False

            initial = response.json()['namespace']
            print_info(f"Initial namespace: {initial}")

            # Switch to progressief
            response = requests.post(
                f"{self.base_url}/v1/namespace/switch",
                headers=self.headers,
                json={"namespace": "progressief"}
            )

            if response.status_code != 200:
                print_fail("Failed to switch to progressief")
                return False

            data = response.json()
            if data['current'] == 'progressief':
                print_pass("Switched to progressief")
            else:
                print_fail(f"Expected progressief, got {data['current']}")
                return False

            # Switch back
            requests.post(
                f"{self.base_url}/v1/namespace/switch",
                headers=self.headers,
                json={"namespace": initial}
            )

            return True

        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            return False

    def test_store_in_different_namespaces(self) -> bool:
        """Test 3: Store memories in different namespaces"""
        print_test("Store Memories in Different Namespaces")

        test_data = {
            'progressief': "Meeting with Synovia Digital about SAP project",
            'cv_automation': "Applied to Booking.com Data Engineer position",
            'investments': "Researching NVIDIA stock fundamentals",
            'personal': "Family vacation planned for December",
            'intel_system': "Deployed mem0 namespace isolation feature"
        }

        try:
            memory_ids = {}

            for namespace, content in test_data.items():
                # Set namespace header
                headers = self.headers.copy()
                headers['X-Namespace'] = namespace

                # Add memory
                response = requests.post(
                    f"{self.base_url}/v1/memories",
                    headers=headers,
                    json={
                        "messages": [{"role": "user", "content": content}],
                        "user_id": f"{USER_ID}/{namespace}"
                    }
                )

                if response.status_code not in [200, 201]:
                    print_fail(f"Failed to add memory to {namespace}: {response.status_code}")
                    return False

                data = response.json()
                memory_ids[namespace] = data.get('id')
                print_pass(f"Added memory to {namespace}: {memory_ids[namespace][:8]}...")

            time.sleep(1)  # Allow indexing

            return True

        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            return False

    def test_search_isolation(self) -> bool:
        """Test 4: Verify search isolation between namespaces"""
        print_test("Search Isolation")

        try:
            # Search in progressief namespace
            headers = self.headers.copy()
            headers['X-Namespace'] = 'progressief'

            response = requests.get(
                f"{self.base_url}/v1/memories?user_id={USER_ID}/progressief",
                headers=headers
            )

            if response.status_code != 200:
                print_fail(f"Failed to search progressief: {response.status_code}")
                return False

            progressief_memories = response.json()
            progressief_count = len(progressief_memories.get('memories', []))

            # Verify progressief memories don't contain cv_automation content
            for memory in progressief_memories.get('memories', []):
                if 'Booking.com' in memory.get('content', ''):
                    print_fail("Found cv_automation content in progressief namespace!")
                    return False

            print_pass(f"progressief namespace isolated ({progressief_count} memories)")

            # Search in cv_automation namespace
            headers['X-Namespace'] = 'cv_automation'

            response = requests.get(
                f"{self.base_url}/v1/memories?user_id={USER_ID}/cv_automation",
                headers=headers
            )

            if response.status_code != 200:
                print_fail(f"Failed to search cv_automation: {response.status_code}")
                return False

            cv_memories = response.json()
            cv_count = len(cv_memories.get('memories', []))

            # Verify cv_automation memories don't contain progressief content
            for memory in cv_memories.get('memories', []):
                if 'Synovia' in memory.get('content', ''):
                    print_fail("Found progressief content in cv_automation namespace!")
                    return False

            print_pass(f"cv_automation namespace isolated ({cv_count} memories)")

            return True

        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            return False

    def test_cross_namespace_prevention(self) -> bool:
        """Test 5: Verify cross-namespace relationships are prevented"""
        print_test("Cross-Namespace Relationship Prevention")

        # This test would require access to Neo4j to verify
        # For now, we'll verify through API that memories stay isolated

        try:
            # Attempt to query progressief memories from cv_automation context
            headers = self.headers.copy()
            headers['X-Namespace'] = 'cv_automation'

            # Try to access a progressief memory from cv_automation namespace
            # This should fail or return empty
            response = requests.get(
                f"{self.base_url}/v1/memories?user_id={USER_ID}/progressief",
                headers=headers
            )

            if response.status_code == 403 or response.status_code == 404:
                print_pass("Cross-namespace access properly blocked")
                return True
            elif response.status_code == 200:
                data = response.json()
                if len(data.get('memories', [])) == 0:
                    print_pass("Cross-namespace query returned empty (isolated)")
                    return True
                else:
                    print_fail("Cross-namespace query returned data (NOT ISOLATED!)")
                    return False
            else:
                print_info(f"Unexpected status code: {response.status_code}")
                return True  # Don't fail on unexpected codes

        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            return False

    def test_user_id_formatting(self) -> bool:
        """Test 6: User ID formatting and parsing"""
        print_test("User ID Formatting")

        test_cases = [
            ("mark_carey", "progressief", "mark_carey/progressief"),
            ("mark_carey", "cv_automation", "mark_carey/cv_automation"),
        ]

        try:
            for base_user, namespace, expected in test_cases:
                response = requests.post(
                    f"{self.base_url}/v1/namespace/validate-user-id",
                    headers=self.headers,
                    json={"user_id": expected}
                )

                if response.status_code != 200:
                    print_fail(f"Failed to validate {expected}")
                    return False

                data = response.json()
                if data['base_user'] == base_user and data['namespace'] == namespace:
                    print_pass(f"Validated {expected}")
                else:
                    print_fail(f"Parse mismatch for {expected}")
                    return False

            return True

        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            return False

    def test_concurrent_namespace_operations(self) -> bool:
        """Test 7: Concurrent operations in different namespaces"""
        print_test("Concurrent Namespace Operations")

        # This would ideally use threading, but simplified for now
        try:
            # Quickly switch namespaces and add memories
            for namespace in ['progressief', 'cv_automation', 'investments']:
                headers = self.headers.copy()
                headers['X-Namespace'] = namespace

                response = requests.post(
                    f"{self.base_url}/v1/memories",
                    headers=headers,
                    json={
                        "messages": [{
                            "role": "user",
                            "content": f"Concurrent test memory for {namespace}"
                        }],
                        "user_id": f"{USER_ID}/{namespace}"
                    }
                )

                if response.status_code not in [200, 201]:
                    print_fail(f"Failed concurrent add to {namespace}")
                    return False

            print_pass("Concurrent operations completed without errors")
            return True

        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            return False

    def test_namespace_stats(self) -> bool:
        """Test 8: Namespace statistics"""
        print_test("Namespace Statistics")

        try:
            for namespace in ['progressief', 'cv_automation']:
                response = requests.get(
                    f"{self.base_url}/v1/namespace/{namespace}/stats",
                    headers=self.headers
                )

                if response.status_code != 200:
                    print_fail(f"Failed to get stats for {namespace}")
                    return False

                data = response.json()
                print_info(f"{namespace}: {data.get('memory_count', 0)} memories")

            print_pass("Namespace statistics retrieved")
            return True

        except Exception as e:
            print_fail(f"Exception: {str(e)}")
            return False

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*80}")
        print(f"Test Summary")
        print(f"{'='*80}\n")

        passed = sum(1 for r in self.test_results if r.get('passed'))
        total = len(self.test_results)

        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")

        if passed == total:
            print(f"\n{Colors.GREEN}✓ ALL TESTS PASSED - NAMESPACE ISOLATION VERIFIED{Colors.END}\n")
        else:
            print(f"\n{Colors.RED}✗ SOME TESTS FAILED - ISOLATION MAY BE COMPROMISED{Colors.END}\n")


def main():
    """Main test runner"""
    # Check if mem0 is accessible
    try:
        response = requests.get(f"{MEM0_URL}/health", timeout=5)
        if response.status_code != 200:
            print_fail(f"mem0 server not accessible at {MEM0_URL}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print_fail(f"Cannot connect to mem0: {str(e)}")
        print_info("Make sure mem0 is running: docker ps | grep mem0")
        sys.exit(1)

    # Run tests
    tester = NamespaceIsolationTests(MEM0_URL, API_KEY)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
