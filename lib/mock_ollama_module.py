#!/usr/bin/env python3
"""
Mock ollama module for mem0 - Uses HTTP API calls instead of ollama package
This allows mem0 to use host-metal Ollama via HTTP without duplicating Python code

Created: 2025-11-04
Purpose: Fix mem0 restart loop by replacing ollama package dependency with httpx HTTP calls
"""

import sys
import os
import httpx
from typing import List, Dict, Any, Optional, Iterator
import json


class MockOllamaClient:
    """
    HTTP-based Ollama client using httpx
    Replaces ollama Python package with direct HTTP API calls to host-metal Ollama
    """
    
    def __init__(self, host: str = None, **kwargs):
        """Initialize with Ollama HTTP URL"""
        self.host = host or os.getenv('OLLAMA_URL', 'http://host.docker.internal:11434')
        if not self.host.startswith('http'):
            self.host = f"http://{self.host}"
        # Remove trailing slash
        self.host = self.host.rstrip('/')
        self.client = httpx.Client(timeout=httpx.Timeout(300.0, connect=10.0))
        print(f"   ✅ HTTP Ollama client initialized: {self.host}")
    
    def embeddings(self, model: str, prompt: str) -> List[float]:
        """Generate embeddings via HTTP API"""
        try:
            response = self.client.post(
                f"{self.host}/api/embeddings",
                json={"model": model, "prompt": prompt},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding", [])
            if not embedding:
                raise ValueError(f"No embedding returned from Ollama API: {data}")
            return embedding
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama HTTP API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Ollama HTTP API error: {e}")
    
    def generate(self, model: str, prompt: str, stream: bool = False, **kwargs) -> Any:
        """Generate text via HTTP API (for LLM)"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                **kwargs
            }
            
            if stream:
                # Streaming response
                with self.client.stream(
                    "POST",
                    f"{self.host}/api/generate",
                    json=payload,
                    timeout=httpx.Timeout(300.0, connect=10.0)
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            try:
                                yield json.loads(line)
                            except json.JSONDecodeError:
                                continue
            else:
                # Non-streaming response
                response = self.client.post(
                    f"{self.host}/api/generate",
                    json=payload,
                    timeout=httpx.Timeout(300.0, connect=10.0)
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama HTTP API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Ollama HTTP API error: {e}")
    
    def chat(self, model: str, messages: List[Dict], **kwargs) -> Any:
        """Chat completion via HTTP API"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                **kwargs
            }
            response = self.client.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=httpx.Timeout(300.0, connect=10.0)
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama HTTP API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Ollama HTTP API error: {e}")
    
    def pull(self, model: str, **kwargs) -> Dict[str, Any]:
        """Pull/download a model via HTTP API (streaming response)"""
        try:
            # Pull endpoint returns streaming JSON (one JSON object per line)
            with self.client.stream(
                "POST",
                f"{self.host}/api/pull",
                json={"name": model, **kwargs},
                timeout=httpx.Timeout(600.0, connect=10.0)  # Long timeout for model downloads
            ) as response:
                response.raise_for_status()
                # Read streaming response - last line contains final status
                last_status = None
                for line in response.iter_lines():
                    if line:
                        try:
                            last_status = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                # Return last status if available, otherwise success
                return last_status if last_status else {"status": "success"}
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama HTTP API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Ollama HTTP API error: {e}")
    
    def list(self) -> Dict[str, Any]:
        """List available models via HTTP API"""
        try:
            response = self.client.get(
                f"{self.host}/api/tags",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama HTTP API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Ollama HTTP API error: {e}")
    
    def close(self):
        """Close HTTP client"""
        if self.client:
            self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# Create mock ollama module
class MockOllamaModule:
    """Mock ollama module that provides Client class using HTTP API"""
    
    def __init__(self):
        self.Client = MockOllamaClient
        # For compatibility with different import styles
        self.OllamaClient = MockOllamaClient
    
    def Client(self, host: str = None, **kwargs):
        """Factory function for creating Client instances"""
        return MockOllamaClient(host, **kwargs)


def install_mock_ollama_module():
    """
    Install mock ollama module BEFORE mem0 tries to import it
    This must be called BEFORE any mem0 imports happen
    """
    print("=" * 70)
    print("🔧 INSTALLING MOCK OLLAMA MODULE (HTTP API)")
    print("=" * 70)
    
    # Create mock module
    mock_module = MockOllamaModule()
    
    # Install it in sys.modules BEFORE mem0 imports it
    sys.modules['ollama'] = mock_module
    
    # Also install as ollama.Client for compatibility
    import types
    ollama_module = types.ModuleType('ollama')
    ollama_module.Client = MockOllamaClient
    ollama_module.OllamaClient = MockOllamaClient
    sys.modules['ollama'] = ollama_module
    
    print("✅ Mock ollama module installed")
    print(f"   📡 Uses HTTP API: {os.getenv('OLLAMA_URL', 'http://host.docker.internal:11434')}")
    print("   🚫 No ollama Python package required")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = install_mock_ollama_module()
    sys.exit(0 if success else 1)


    def Client(self, host: str = None, **kwargs):
        """Factory function for creating Client instances"""
        return MockOllamaClient(host, **kwargs)


def install_mock_ollama_module():
    """
    Install mock ollama module BEFORE mem0 tries to import it
    This must be called BEFORE any mem0 imports happen
    """
    print("=" * 70)
    print("🔧 INSTALLING MOCK OLLAMA MODULE (HTTP API)")
    print("=" * 70)
    
    # Create mock module
    mock_module = MockOllamaModule()
    
    # Install it in sys.modules BEFORE mem0 imports it
    sys.modules['ollama'] = mock_module
    
    # Also install as ollama.Client for compatibility
    import types
    ollama_module = types.ModuleType('ollama')
    ollama_module.Client = MockOllamaClient
    ollama_module.OllamaClient = MockOllamaClient
    sys.modules['ollama'] = ollama_module
    
    print("✅ Mock ollama module installed")
    print(f"   📡 Uses HTTP API: {os.getenv('OLLAMA_URL', 'http://host.docker.internal:11434')}")
    print("   🚫 No ollama Python package required")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = install_mock_ollama_module()
    sys.exit(0 if success else 1)

