#!/usr/bin/env python3
"""
Force mem0 to use Ollama-only configuration
Patches mem0 Memory initialization to NEVER use OpenAI

Created: 2025-11-03
Purpose: Enforce local-only Ollama embeddings and LLM
"""

import os
import sys

def force_ollama_config():
    """
    Monkey-patch mem0 to force Ollama configuration
    This runs BEFORE mem0 server starts
    """

    # Set environment variables as fallback
    os.environ['MEM0_EMBEDDER_PROVIDER'] = 'ollama'
    os.environ['MEM0_EMBEDDER_MODEL'] = 'nomic-embed-text:latest'
    os.environ['MEM0_LLM_PROVIDER'] = 'ollama'
    os.environ['MEM0_LLM_MODEL'] = 'mistral:7b-instruct-q5_K_M'
    os.environ['OLLAMA_URL'] = os.getenv('OLLAMA_URL', 'http://host.docker.internal:11434')

    # Import mem0 after setting env vars
    from mem0 import Memory

    # Monkey-patch Memory.__init__ to force Ollama config
    original_init = Memory.__init__

    def patched_init(self, config=None):
        """Force Ollama configuration"""

        # Build Ollama-only config
        ollama_config = {
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": os.getenv('MEM0_LLM_MODEL', 'mistral:7b-instruct-q5_K_M'),
                    "ollama_base_url": os.getenv('OLLAMA_URL', 'http://host.docker.internal:11434'),
                    "temperature": 0.3,
                    "max_tokens": 1500,
                }
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": os.getenv('MEM0_EMBEDDER_MODEL', 'nomic-embed-text:latest'),
                    "ollama_base_url": os.getenv('OLLAMA_URL', 'http://host.docker.internal:11434'),
                }
            },
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "host": os.getenv('POSTGRES_HOST', 'postgres'),
                    "port": int(os.getenv('POSTGRES_PORT', 5432)),
                    "user": os.getenv('POSTGRES_USER', 'mem0_user'),
                    "password": os.getenv('POSTGRES_PASSWORD'),
                    "dbname": os.getenv('POSTGRES_DB', 'mem0'),
                }
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": os.getenv('NEO4J_URI', 'bolt://neo4j:7687'),
                    "username": os.getenv('NEO4J_USERNAME', 'neo4j'),
                    "password": os.getenv('NEO4J_PASSWORD'),
                }
            },
            "history_db_path": os.getenv('HISTORY_DB_PATH', '/app/data/history.db'),
        }

        print("=" * 70)
        print("🔒 OLLAMA-ONLY CONFIGURATION ENFORCED")
        print("=" * 70)
        print(f"LLM Provider: ollama")
        print(f"LLM Model: {ollama_config['llm']['config']['model']}")
        print(f"Embedder Provider: ollama")
        print(f"Embedder Model: {ollama_config['embedder']['config']['model']}")
        print(f"Ollama URL: {ollama_config['llm']['config']['ollama_base_url']}")
        print(f"Vector Store: pgvector")
        print(f"Graph Store: neo4j")
        print("=" * 70)

        # Call original init with forced config
        original_init(self, config=ollama_config)

    # Apply monkey patch
    Memory.__init__ = patched_init

    print("✅ Ollama-only configuration patch applied")
    return True

if __name__ == "__main__":
    force_ollama_config()
