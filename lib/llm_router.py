#!/usr/bin/env python3
"""
LLM Router for mem0 - Local-First Strategy
Location: /Volumes/Data/ai_projects/mem0-system/lib/llm_router.py
Purpose: Route mem0 LLM queries to local Ollama models (95%) with OpenAI fallback (5%)
Scope: Cost optimization - Target $0/month baseline by using local LLMs

Architecture:
- Primary: Local Ollama models (mistral:7b, deepseek-coder:6.7b, codellama:13b)
- Fallback: OpenAI API for complex reasoning or when local models fail
- Goal: 95% local routing, 5% external API usage
- Cost: $0 for local queries vs $0.10-0.50 per 1000 queries for OpenAI
"""

import os
import time
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import httpx
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Query type classification for routing decisions"""
    EMBEDDING = "embedding"          # Text embeddings (ALWAYS local)
    SUMMARIZATION = "summarization"   # Memory summarization (local preferred)
    EXTRACTION = "extraction"         # Entity/fact extraction (local preferred)
    REASONING = "reasoning"           # Complex reasoning (may need external)
    CODE = "code"                     # Code-related queries (use deepseek-coder)
    SIMPLE = "simple"                 # Simple Q&A (ALWAYS local)


class ModelProvider(str, Enum):
    """LLM provider types"""
    OLLAMA_LOCAL = "ollama_local"     # Local Ollama models ($0 cost)
    OPENAI = "openai"                  # OpenAI API (fallback, has cost)


@dataclass
class RoutingDecision:
    """Routing decision with reasoning"""
    provider: ModelProvider
    model: str
    reason: str
    estimated_cost: float  # In dollars
    max_tokens: int
    temperature: float


@dataclass
class QueryMetrics:
    """Track query routing metrics"""
    total_queries: int = 0
    local_queries: int = 0
    external_queries: int = 0
    total_cost: float = 0.0
    avg_local_latency: float = 0.0
    avg_external_latency: float = 0.0


class Mem0LLMRouter:
    """
    Intelligent LLM router for mem0 with local-first strategy.

    Routing Strategy:
    1. Embeddings: ALWAYS use Ollama nomic-embed-text (free, fast)
    2. Code queries: Use deepseek-coder:6.7b (specialized, local)
    3. Simple queries (<2k tokens): Use mistral:7b (fast, local)
    4. Medium queries (2k-4k tokens): Use codellama:13b (balanced, local)
    5. Complex reasoning (>4k tokens OR high complexity): OpenAI fallback

    Cost Analysis:
    - Local: $0.00 per query (unlimited)
    - OpenAI: ~$0.002-0.03 per query (depends on model)
    - Target: 95% local = $0-5/month even with 10k queries
    """

    def __init__(self):
        # Ollama connection (local on host machine)
        # Use localhost when running locally, host.docker.internal from Docker
        default_url = "http://localhost:11434" if not os.path.exists("/.dockerenv") else "http://host.docker.internal:11434"
        self.ollama_url = os.getenv("OLLAMA_URL", default_url)

        # OpenAI fallback
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Routing thresholds
        self.local_threshold = int(os.getenv("LLM_LOCAL_THRESHOLD", "95"))  # 95% target
        self.simple_query_max_tokens = 2000
        self.medium_query_max_tokens = 4000

        # Model configurations
        self.models = {
            "mistral:7b": {
                "type": "general",
                "max_context": 8192,
                "cost": 0.0,
                "latency": 1.5,  # seconds
                "best_for": ["simple", "summarization", "extraction"]
            },
            "deepseek-coder:6.7b": {
                "type": "code",
                "max_context": 16384,
                "cost": 0.0,
                "latency": 2.0,
                "best_for": ["code", "technical"]
            },
            "codellama:13b": {
                "type": "general",
                "max_context": 16384,
                "cost": 0.0,
                "latency": 3.0,
                "best_for": ["medium", "balanced"]
            },
            "nomic-embed-text:latest": {
                "type": "embedding",
                "max_context": 8192,
                "cost": 0.0,
                "latency": 0.5,
                "best_for": ["embedding"]
            }
        }

        # Metrics tracking
        self.metrics = QueryMetrics()

        # HTTP client for async requests
        self.http_client = httpx.AsyncClient(timeout=120.0)

        logger.info(f"Mem0LLMRouter initialized - Ollama: {self.ollama_url}")
        logger.info(f"Target: {self.local_threshold}% local routing")

    def classify_query(self, text: str, context_length: int = 0) -> Tuple[QueryType, int]:
        """
        Classify query type and estimate complexity.

        Returns:
            Tuple[QueryType, complexity_score]
            complexity_score: 1-10 (1=simple, 10=very complex)
        """
        text_lower = text.lower()

        # Estimate context length if not provided
        if context_length == 0:
            context_length = len(text.split())

        # Embedding queries (ALWAYS local)
        if "embedding" in text_lower or "encode" in text_lower:
            return QueryType.EMBEDDING, 1

        # Code queries (use specialized model)
        if any(kw in text_lower for kw in ["code", "function", "class", "python", "javascript", "debug", "error"]):
            return QueryType.CODE, 3

        # Simple queries (short, straightforward)
        if context_length < 500 and not any(kw in text_lower for kw in ["analyze", "complex", "reasoning", "explain why"]):
            return QueryType.SIMPLE, 1

        # Summarization
        if any(kw in text_lower for kw in ["summarize", "summary", "tldr", "brief"]):
            return QueryType.SUMMARIZATION, 2

        # Extraction
        if any(kw in text_lower for kw in ["extract", "find", "list", "identify"]):
            return QueryType.EXTRACTION, 2

        # Complex reasoning (may need external)
        if any(kw in text_lower for kw in ["analyze", "reasoning", "complex", "explain why", "compare"]):
            complexity = 7 if context_length > 2000 else 5
            return QueryType.REASONING, complexity

        # Default: simple if short, medium if longer
        if context_length < 1000:
            return QueryType.SIMPLE, 2
        else:
            return QueryType.SUMMARIZATION, 4

    def route_query(
        self,
        query_text: str,
        query_type: Optional[QueryType] = None,
        context_length: Optional[int] = None,
        force_local: bool = False
    ) -> RoutingDecision:
        """
        Route query to appropriate model based on type and complexity.

        Args:
            query_text: The query to route
            query_type: Optional pre-classified query type
            context_length: Optional context length in tokens
            force_local: Force local routing even for complex queries

        Returns:
            RoutingDecision with provider, model, and reasoning
        """
        # Classify query if not provided
        if query_type is None or context_length is None:
            query_type, complexity = self.classify_query(
                query_text,
                context_length or len(query_text.split())
            )
        else:
            complexity = 5  # Default medium complexity

        ctx_len = context_length or len(query_text.split())

        # ALWAYS use local for embeddings
        if query_type == QueryType.EMBEDDING:
            return RoutingDecision(
                provider=ModelProvider.OLLAMA_LOCAL,
                model="nomic-embed-text:latest",
                reason="Embedding queries ALWAYS use local Ollama (free, fast)",
                estimated_cost=0.0,
                max_tokens=512,
                temperature=0.0
            )

        # Use specialized code model
        if query_type == QueryType.CODE:
            return RoutingDecision(
                provider=ModelProvider.OLLAMA_LOCAL,
                model="deepseek-coder:6.7b",
                reason="Code query - using specialized deepseek-coder local model",
                estimated_cost=0.0,
                max_tokens=min(ctx_len * 2, 4000),
                temperature=0.1
            )

        # Simple queries - use fast local model
        if query_type == QueryType.SIMPLE or complexity <= 3:
            return RoutingDecision(
                provider=ModelProvider.OLLAMA_LOCAL,
                model="mistral:7b",
                reason="Simple query - using fast mistral:7b local model",
                estimated_cost=0.0,
                max_tokens=min(ctx_len * 2, 2000),
                temperature=0.3
            )

        # Medium complexity - use codellama for better quality
        if complexity <= 6 or ctx_len < self.medium_query_max_tokens:
            return RoutingDecision(
                provider=ModelProvider.OLLAMA_LOCAL,
                model="codellama:13b",
                reason="Medium complexity - using codellama:13b local model",
                estimated_cost=0.0,
                max_tokens=min(ctx_len * 2, 4000),
                temperature=0.3
            )

        # Complex reasoning - check if we should use external API
        if not force_local and complexity >= 7:
            # Check if we're below local threshold
            local_percentage = (self.metrics.local_queries / max(self.metrics.total_queries, 1)) * 100

            if local_percentage < self.local_threshold:
                # We're below target, use local anyway
                return RoutingDecision(
                    provider=ModelProvider.OLLAMA_LOCAL,
                    model="codellama:13b",
                    reason=f"Complex query but staying under {self.local_threshold}% local target",
                    estimated_cost=0.0,
                    max_tokens=4000,
                    temperature=0.5
                )
            else:
                # Use external for best quality on complex queries
                return RoutingDecision(
                    provider=ModelProvider.OPENAI,
                    model="gpt-4o-mini",  # Cost-effective OpenAI model
                    reason="Complex reasoning query - using OpenAI for quality",
                    estimated_cost=0.015,  # ~$0.015 per query
                    max_tokens=min(ctx_len * 3, 8000),
                    temperature=0.7
                )

        # Default: use local codellama
        return RoutingDecision(
            provider=ModelProvider.OLLAMA_LOCAL,
            model="codellama:13b",
            reason="Default routing - codellama:13b local model",
            estimated_cost=0.0,
            max_tokens=2000,
            temperature=0.3
        )

    async def call_local_llm(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """Call local Ollama model"""
        start_time = time.time()

        try:
            # Build full prompt with system message if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            response = await self.http_client.post(
                f"{self.ollama_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            latency = time.time() - start_time

            # Update metrics
            self.metrics.local_queries += 1
            self.metrics.total_queries += 1

            # Update average latency
            if self.metrics.avg_local_latency == 0:
                self.metrics.avg_local_latency = latency
            else:
                self.metrics.avg_local_latency = (
                    self.metrics.avg_local_latency * 0.9 + latency * 0.1
                )

            logger.info(f"Local LLM ({model}) - {latency:.2f}s - Cost: $0.00")

            return {
                "response": result.get("response", ""),
                "model": model,
                "provider": "ollama_local",
                "tokens": result.get("eval_count", 0),
                "cost": 0.0,
                "latency": latency
            }

        except Exception as e:
            logger.error(f"Local LLM error ({model}): {str(e)}")
            raise

    async def call_external_api(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """Call external OpenAI API (fallback)"""
        start_time = time.time()

        try:
            import openai

            client = openai.AsyncOpenAI(api_key=self.openai_api_key)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            latency = time.time() - start_time
            tokens = response.usage.total_tokens

            # Estimate cost (gpt-4o-mini: ~$0.15/$0.60 per 1M tokens)
            cost = (tokens / 1_000_000) * 0.375  # Average of input/output

            # Update metrics
            self.metrics.external_queries += 1
            self.metrics.total_queries += 1
            self.metrics.total_cost += cost

            # Update average latency
            if self.metrics.avg_external_latency == 0:
                self.metrics.avg_external_latency = latency
            else:
                self.metrics.avg_external_latency = (
                    self.metrics.avg_external_latency * 0.9 + latency * 0.1
                )

            logger.info(f"External API ({model}) - {latency:.2f}s - Cost: ${cost:.4f}")

            return {
                "response": response.choices[0].message.content,
                "model": model,
                "provider": "openai",
                "tokens": tokens,
                "cost": cost,
                "latency": latency
            }

        except Exception as e:
            logger.error(f"External API error ({model}): {str(e)}")
            raise

    async def execute_query(
        self,
        query_text: str,
        query_type: Optional[QueryType] = None,
        context_length: Optional[int] = None,
        system_prompt: Optional[str] = None,
        force_local: bool = False
    ) -> Dict:
        """
        Execute a query with automatic routing.

        Args:
            query_text: The query/prompt
            query_type: Optional pre-classified type
            context_length: Optional context length
            system_prompt: Optional system message
            force_local: Force local execution

        Returns:
            Dict with response, model, cost, latency, etc.
        """
        # Get routing decision
        decision = self.route_query(query_text, query_type, context_length, force_local)

        logger.info(f"Routing: {decision.provider.value} / {decision.model}")
        logger.info(f"Reason: {decision.reason}")

        # Execute based on provider
        if decision.provider == ModelProvider.OLLAMA_LOCAL:
            return await self.call_local_llm(
                model=decision.model,
                prompt=query_text,
                max_tokens=decision.max_tokens,
                temperature=decision.temperature,
                system_prompt=system_prompt
            )
        else:
            return await self.call_external_api(
                model=decision.model,
                prompt=query_text,
                max_tokens=decision.max_tokens,
                temperature=decision.temperature,
                system_prompt=system_prompt
            )

    def get_metrics(self) -> Dict:
        """Get current routing metrics"""
        total = max(self.metrics.total_queries, 1)
        local_pct = (self.metrics.local_queries / total) * 100
        external_pct = (self.metrics.external_queries / total) * 100

        return {
            "total_queries": self.metrics.total_queries,
            "local_queries": self.metrics.local_queries,
            "external_queries": self.metrics.external_queries,
            "local_percentage": round(local_pct, 2),
            "external_percentage": round(external_pct, 2),
            "total_cost": round(self.metrics.total_cost, 4),
            "avg_cost_per_query": round(self.metrics.total_cost / total, 4),
            "avg_local_latency": round(self.metrics.avg_local_latency, 2),
            "avg_external_latency": round(self.metrics.avg_external_latency, 2),
            "target_local_pct": self.local_threshold,
            "on_target": local_pct >= self.local_threshold
        }

    async def health_check(self) -> Dict:
        """Check health of all LLM providers"""
        health = {
            "ollama": False,
            "openai": False,
            "ollama_models": []
        }

        # Check Ollama
        try:
            response = await self.http_client.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                health["ollama"] = True
                health["ollama_models"] = [m["name"] for m in data.get("models", [])]
        except:
            pass

        # Check OpenAI
        health["openai"] = bool(self.openai_api_key)

        return health


# Singleton instance
_router_instance = None

def get_router() -> Mem0LLMRouter:
    """Get or create router singleton"""
    global _router_instance
    if _router_instance is None:
        _router_instance = Mem0LLMRouter()
    return _router_instance


# Configuration for mem0 to use Ollama directly
def get_mem0_config() -> Dict:
    """
    Get mem0 configuration for Ollama local LLMs.

    This configuration can be used to initialize mem0 with local-first routing.
    """
    return {
        "llm": {
            "provider": "ollama",
            "config": {
                "model": "mistral:7b",  # Default model
                "temperature": 0.3,
                "max_tokens": 2000,
                "ollama_base_url": "http://host.docker.internal:11434"
            }
        },
        "embedder": {
            "provider": "ollama",
            "config": {
                "model": "nomic-embed-text:latest",
                "ollama_base_url": "http://host.docker.internal:11434"
            }
        }
    }
