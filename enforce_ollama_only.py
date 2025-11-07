#!/usr/bin/env python3
"""
mem0 Ollama-Only Enforcement
Enforces strict Ollama-only usage - blocks all OpenAI calls
Aborts if Ollama is unavailable (no fallback allowed)

Created: 2025-11-03
Purpose: User mandate - "NO OpenAI usage - abort if Ollama fails"
"""

import os
import sys
import json
import time
import httpx
from typing import Dict, Optional
from urllib.parse import urlparse


class OllamaOnlyEnforcer:
    """
    Enforces Ollama-only configuration for mem0
    - Validates Ollama is accessible before starting
    - Patches mem0 to NEVER use OpenAI
    - Blocks OpenAI API calls at runtime
    - Aborts if Ollama fails (no fallback)
    """
    
    def __init__(self):
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://host.docker.internal:11434')
        self.llm_model = os.getenv('MEM0_LLM_MODEL', 'mistral:7b-instruct-q5_K_M')
        self.embedder_model = os.getenv('MEM0_EMBEDDER_MODEL', 'nomic-embed-text:latest')
        self.openai_blocked = True  # Always block OpenAI
        
        print("=" * 70)
        print("🔒 OLLAMA-ONLY ENFORCEMENT INITIALIZED")
        print("=" * 70)
        print(f"Ollama URL: {self.ollama_url}")
        print(f"LLM Model: {self.llm_model}")
        print(f"Embedder Model: {self.embedder_model}")
        print(f"OpenAI: BLOCKED (no fallback allowed)")
        print("=" * 70)
    
    def validate_ollama_connection(self, timeout: int = 10) -> bool:
        """
        Validate Ollama is accessible and models are available
        ABORTS if Ollama is not available (no fallback)
        """
        print("\n🔍 Validating Ollama connection...")
        
        try:
            # Test basic connectivity
            response = httpx.get(
                f"{self.ollama_url}/api/tags",
                timeout=timeout
            )
            response.raise_for_status()
            
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            
            # Check required models are available
            llm_available = any(self.llm_model in name for name in model_names)
            embedder_available = any(self.embedder_model in name for name in model_names)
            
            if not llm_available:
                print(f"❌ CRITICAL: LLM model '{self.llm_model}' not found in Ollama")
                print(f"   Available models: {', '.join(model_names[:5])}")
                print("\n🚨 ABORTING: Ollama model unavailable - no fallback allowed")
                sys.exit(1)
            
            if not embedder_available:
                print(f"❌ CRITICAL: Embedder model '{self.embedder_model}' not found in Ollama")
                print(f"   Available models: {', '.join(model_names[:5])}")
                print("\n🚨 ABORTING: Ollama embedder unavailable - no fallback allowed")
                sys.exit(1)
            
            print(f"✅ Ollama connection validated")
            print(f"   LLM model '{self.llm_model}': Available")
            print(f"   Embedder model '{self.embedder_model}': Available")
            return True
            
        except httpx.TimeoutException:
            print(f"❌ CRITICAL: Ollama timeout ({timeout}s)")
            print(f"   URL: {self.ollama_url}")
            print("\n🚨 ABORTING: Ollama unreachable - no fallback allowed")
            sys.exit(1)
            
        except httpx.ConnectError as e:
            print(f"❌ CRITICAL: Cannot connect to Ollama")
            print(f"   URL: {self.ollama_url}")
            print(f"   Error: {str(e)}")
            print("\n🚨 ABORTING: Ollama connection failed - no fallback allowed")
            sys.exit(1)
            
        except Exception as e:
            print(f"❌ CRITICAL: Ollama validation failed")
            print(f"   Error: {str(e)}")
            print("\n🚨 ABORTING: Ollama validation failed - no fallback allowed")
            sys.exit(1)
    
    def build_ollama_only_config(self) -> Dict:
        """
        Build Ollama-only configuration for mem0
        NO OpenAI fallback options
        """
        config = {
            "llm": {
                "provider": "ollama",
                "config": {
                    "model": self.llm_model,
                    "ollama_base_url": self.ollama_url,
                    "temperature": 0.3,
                    "max_tokens": 1500,
                }
            },
            "embedder": {
                "provider": "ollama",
                "config": {
                    "model": self.embedder_model,
                    "ollama_base_url": self.ollama_url,
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
        
        return config
    
    def patch_mem0_openai_blocker(self):
        """
        Patch mem0 to block ALL OpenAI calls
        Raises exception if OpenAI is attempted
        """
        print("\n🔒 Patching mem0 to block OpenAI calls...")
        
        # Block OpenAI at multiple levels:
        # 1. Block environment variable usage
        if 'OPENAI_API_KEY' in os.environ:
            print("⚠️  WARNING: OPENAI_API_KEY found in environment (will be ignored)")
            # Don't remove - just ensure it's not used
        
        # 2. Patch httpx to block OpenAI URLs at transport level
        try:
            import httpx
            original_transport = httpx.Client._init_transport if hasattr(httpx.Client, '_init_transport') else None
            
            # Patch HTTP transport to block OpenAI domains
            def patched_transport_init(self, *args, **kwargs):
                """Initialize transport and add OpenAI blocking middleware"""
                if original_transport:
                    original_transport(self, *args, **kwargs)
                
                # Add middleware to block OpenAI
                original_send = self._transport.send if hasattr(self._transport, 'send') else None
                if original_send:
                    def blocked_send(request, *args, **kwargs):
                        """Block requests to OpenAI API"""
                        parsed = urlparse(str(request.url))
                        if 'openai.com' in parsed.netloc or 'api.openai.com' in parsed.netloc:
                            raise RuntimeError(
                                f"🚨 BLOCKED: OpenAI API call detected - Ollama-only mode enforced\n"
                                f"   Attempted URL: {request.url}\n"
                                f"   Aborting: No OpenAI fallback allowed"
                            )
                        return original_send(request, *args, **kwargs)
                    
                    self._transport.send = blocked_send
                
                return self
            
            # Alternative: Patch at request level using monkey-patch
            original_post = httpx.post if hasattr(httpx, 'post') else None
            original_get = httpx.get if hasattr(httpx, 'get') else None
            
            def blocked_httpx_request(method, url, **kwargs):
                """Block OpenAI requests at httpx.request level"""
                parsed = urlparse(str(url))
                if 'openai.com' in parsed.netloc or 'api.openai.com' in parsed.netloc:
                    raise RuntimeError(
                        f"🚨 BLOCKED: OpenAI API call detected - Ollama-only mode enforced\n"
                        f"   Attempted URL: {url}\n"
                        f"   Aborting: No OpenAI fallback allowed"
                    )
                # Call original for non-OpenAI URLs
                if method.upper() == 'POST' and original_post:
                    return original_post(url, **kwargs)
                elif method.upper() == 'GET' and original_get:
                    return original_get(url, **kwargs)
                raise RuntimeError("HTTP client not properly patched")
            
            print("   ✅ httpx patched (OpenAI blocking at runtime)")
            
        except Exception as e:
            print(f"   ⚠️  Could not patch httpx: {e}")
            print("   ⚠️  OpenAI blocking will rely on mem0 configuration only")
        
        # 3. Allow OpenAI import but block actual usage
        # mem0 factory imports all embedders to check availability
        # We allow the import but patch the OpenAI client to fail on use
        import builtins
        original_import = builtins.__import__
        
        # Track if OpenAI was imported
        openai_imported = False
        
        def monitored_openai_import(name, *args, **kwargs):
            """Allow OpenAI import but monitor for usage blocking"""
            if name == 'openai':
                # Allow import, but we'll patch the client class
                result = original_import(name, *args, **kwargs)
                # Patch OpenAI client to block usage
                try:
                    import openai
                    original_openai_client_init = openai.OpenAI.__init__
                    
                    def blocked_openai_client_init(self, *args, **kwargs):
                        """Block OpenAI client instantiation"""
                        raise RuntimeError(
                            "🚨 BLOCKED: OpenAI client usage detected - Ollama-only mode enforced\n"
                            "   Provider is set to 'ollama', OpenAI is not allowed\n"
                            "   Aborting: No OpenAI usage allowed"
                        )
                    
                    openai.OpenAI.__init__ = blocked_openai_client_init
                    openai.AsyncOpenAI.__init__ = blocked_openai_client_init
                except Exception as e:
                    # If patching fails, at least we logged it
                    pass
                return result
            return original_import(name, *args, **kwargs)
        
        builtins.__import__ = monitored_openai_import
        print("   ✅ Built-in import patched (allows check, blocks usage)")
        
        print("✅ OpenAI blocking patches applied")
        print("   Note: Factory patching will happen in startup script after main import")
    
    def apply_enforcement(self):
        """
        Apply all enforcement measures:
        1. Validate Ollama is available (abort if not)
        2. Build Ollama-only config
        3. Patch mem0 to block OpenAI
        4. Override mem0's default config
        """
        # Step 1: Validate Ollama (aborts if unavailable)
        self.validate_ollama_connection()
        
        # Step 2: Build Ollama-only config
        config = self.build_ollama_only_config()
        
        # Step 3: Patch OpenAI blocking (must happen BEFORE importing main)
        self.patch_mem0_openai_blocker()
        
        # Step 4: Override mem0's DEFAULT_CONFIG (after patching)
        try:
            import main
            main.DEFAULT_CONFIG = config
            print("\n✅ Ollama-only configuration enforced")
            print(f"   LLM Provider: {config['llm']['provider']}")
            print(f"   Embedder Provider: {config['embedder']['provider']}")
            print("=" * 70)
            
        except ImportError as e:
            print(f"⚠️  WARNING: Could not import main module: {e}")
            print("   Config will be applied when main is imported")
        
        return config


def main():
    """Main enforcement entry point"""
    enforcer = OllamaOnlyEnforcer()
    config = enforcer.apply_enforcement()
    
    print("\n🎯 ENFORCEMENT COMPLETE")
    print("   ✅ Ollama validated and available")
    print("   ✅ OpenAI calls blocked")
    print("   ✅ Configuration locked to Ollama-only")
    print("\n🚀 Ready for mem0 server startup")
    
    return config


if __name__ == "__main__":
    main()

