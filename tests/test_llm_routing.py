#!/usr/bin/env python3
"""
Test LLM Routing - Local-First Strategy
Location: /Volumes/intel-system/deployment/docker/mem0_tailscale/test_llm_routing.py
Purpose: Test and benchmark the LLM router with various query types
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from llm_router import Mem0LLMRouter, QueryType


async def test_routing_decisions():
    """Test routing decision logic"""
    router = Mem0LLMRouter()

    print("=" * 80)
    print("LLM ROUTING DECISION TEST")
    print("=" * 80)

    test_queries = [
        {
            "text": "What is 2+2?",
            "description": "Simple math query",
            "expected": "mistral:7b (local)"
        },
        {
            "text": "def calculate_fibonacci(n):\n    # Write a Python function",
            "description": "Code generation",
            "expected": "deepseek-coder:6.7b (local)"
        },
        {
            "text": "Summarize this: " + ("word " * 500),
            "description": "Medium summarization (500 words)",
            "expected": "codellama:13b (local)"
        },
        {
            "text": "Analyze the complex philosophical implications of quantum mechanics on determinism and free will, considering both Copenhagen and Many-Worlds interpretations",
            "description": "Complex reasoning",
            "expected": "Could route to OpenAI if needed"
        },
        {
            "text": "Extract key entities from this text: John works at Google in California",
            "description": "Entity extraction",
            "expected": "mistral:7b (local)"
        }
    ]

    for i, test in enumerate(test_queries, 1):
        print(f"\n[Test {i}] {test['description']}")
        print(f"Query: {test['text'][:100]}...")
        print(f"Expected: {test['expected']}")

        decision = router.route_query(test['text'])

        print(f"✅ Decision: {decision.provider.value} / {decision.model}")
        print(f"   Reason: {decision.reason}")
        print(f"   Cost: ${decision.estimated_cost:.4f}")
        print(f"   Max tokens: {decision.max_tokens}")
        print(f"   Temperature: {decision.temperature}")


async def test_actual_execution():
    """Test actual LLM execution"""
    router = Mem0LLMRouter()

    print("\n" + "=" * 80)
    print("LLM EXECUTION TEST")
    print("=" * 80)

    # Test simple query (should use mistral:7b)
    print("\n[Test 1] Simple query to local Ollama")
    result = await router.execute_query(
        query_text="What is the capital of France? Answer in 3 words or less.",
        force_local=True
    )

    print(f"Response: {result['response'][:200]}")
    print(f"Model: {result['model']}")
    print(f"Provider: {result['provider']}")
    print(f"Latency: {result['latency']:.2f}s")
    print(f"Cost: ${result['cost']:.4f}")

    # Test code query (should use deepseek-coder)
    print("\n[Test 2] Code query to deepseek-coder")
    result = await router.execute_query(
        query_text="Write a Python function to check if a number is prime. Just the code, no explanation.",
        query_type=QueryType.CODE,
        force_local=True
    )

    print(f"Response: {result['response'][:200]}")
    print(f"Model: {result['model']}")
    print(f"Provider: {result['provider']}")
    print(f"Latency: {result['latency']:.2f}s")
    print(f"Cost: ${result['cost']:.4f}")


async def test_metrics():
    """Test metrics tracking"""
    router = Mem0LLMRouter()

    print("\n" + "=" * 80)
    print("ROUTING METRICS TEST")
    print("=" * 80)

    # Execute several queries
    queries = [
        "What is Python?",
        "Explain machine learning",
        "def add(a, b): return a + b  # What does this do?",
        "Summarize: AI is transforming the world",
        "What's 5 * 7?"
    ]

    for query in queries:
        await router.execute_query(query, force_local=True)

    metrics = router.get_metrics()

    print(f"\nTotal Queries: {metrics['total_queries']}")
    print(f"Local Queries: {metrics['local_queries']} ({metrics['local_percentage']}%)")
    print(f"External Queries: {metrics['external_queries']} ({metrics['external_percentage']}%)")
    print(f"Total Cost: ${metrics['total_cost']:.4f}")
    print(f"Avg Cost/Query: ${metrics['avg_cost_per_query']:.4f}")
    print(f"Avg Local Latency: {metrics['avg_local_latency']:.2f}s")
    print(f"Target: {metrics['target_local_pct']}% local")
    print(f"On Target: {'✅ YES' if metrics['on_target'] else '❌ NO'}")


async def test_health():
    """Test health check"""
    router = Mem0LLMRouter()

    print("\n" + "=" * 80)
    print("HEALTH CHECK TEST")
    print("=" * 80)

    health = await router.health_check()

    print(f"\nOllama: {'✅ Available' if health['ollama'] else '❌ Unavailable'}")
    print(f"OpenAI: {'✅ Configured' if health['openai'] else '❌ Not configured'}")

    if health['ollama_models']:
        print(f"\nAvailable Ollama Models ({len(health['ollama_models'])}):")
        for model in health['ollama_models']:
            print(f"  - {model}")


async def benchmark_performance():
    """Benchmark local vs external performance"""
    router = Mem0LLMRouter()

    print("\n" + "=" * 80)
    print("PERFORMANCE BENCHMARK")
    print("=" * 80)

    # Benchmark local models
    local_models = ["mistral:7b", "deepseek-coder:6.7b", "codellama:13b"]

    for model in local_models:
        print(f"\n[Benchmarking {model}]")

        start = asyncio.get_event_loop().time()

        try:
            result = await router.call_local_llm(
                model=model,
                prompt="What is AI? Explain in one sentence.",
                max_tokens=100,
                temperature=0.1
            )

            elapsed = asyncio.get_event_loop().time() - start

            print(f"  Response: {result['response'][:100]}...")
            print(f"  Latency: {elapsed:.2f}s")
            print(f"  Tokens: {result.get('tokens', 'N/A')}")
            print(f"  Cost: ${result['cost']:.4f}")

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

    # Cost projection
    print("\n" + "=" * 80)
    print("COST PROJECTION")
    print("=" * 80)

    queries_per_day = 100
    queries_per_month = queries_per_day * 30

    # 95% local, 5% external
    local_queries = queries_per_month * 0.95
    external_queries = queries_per_month * 0.05

    local_cost = local_queries * 0.0  # Free
    external_cost = external_queries * 0.015  # ~$0.015 per query

    total_cost = local_cost + external_cost

    print(f"\nProjected Monthly Usage:")
    print(f"  Total Queries: {queries_per_month}")
    print(f"  Local Queries (95%): {int(local_queries)} @ $0.00 = ${local_cost:.2f}")
    print(f"  External Queries (5%): {int(external_queries)} @ $0.015 = ${external_cost:.2f}")
    print(f"  Total Monthly Cost: ${total_cost:.2f}")
    print(f"\n  vs 100% OpenAI: ${queries_per_month * 0.015:.2f}")
    print(f"  Monthly Savings: ${(queries_per_month * 0.015) - total_cost:.2f}")


async def main():
    """Run all tests"""
    print("Starting LLM Router Tests...")

    # Test 1: Routing decisions
    await test_routing_decisions()

    # Test 2: Health check
    await test_health()

    # Test 3: Actual execution
    await test_actual_execution()

    # Test 4: Metrics tracking
    await test_metrics()

    # Test 5: Performance benchmark
    await benchmark_performance()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
