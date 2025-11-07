#lso !/bin/bash
# mem0 Startup Script with GDS Patch + Ollama-Only Enforcement
# Created: 2025-10-16
# Updated: 2025-11-03 - Added Ollama-only enforcement
# Purpose: Apply GDS compatibility patch + enforce Ollama-only (NO OpenAI fallback)

set -e

echo "================================================"
echo "🚀 Starting mem0 with Neo4j GDS Patch"
echo "🔒 Ollama-Only Enforcement (NO OpenAI fallback)"
echo "================================================"
echo ""

# Apply GDS patch before starting server
echo "🔧 Applying GDS patch..."
python3 /app/mem0_gds_patch_v2.py

# Start mem0 server with uvicorn + Ollama-only enforcement
echo "🚀 Starting mem0 server with Ollama-only enforcement..."
cd /app

# Run uvicorn with patches applied
python3 <<'PYTHON'
import sys
import os
sys.path.insert(0, '/app')

print("=" * 70)
print("🔒 OLLAMA-ONLY ENFORCEMENT INITIALIZING")
print("=" * 70)

# Step 0: CRITICAL ROOT CAUSE FIX - Remove OPENAI_API_KEY
# mem0 defaults to OpenAI if OPENAI_API_KEY is set, regardless of config
print("🔧 Step 0a: Removing OPENAI_API_KEY (root cause of OpenAI fallback)...")
if 'OPENAI_API_KEY' in os.environ:
    original_openai_key = os.environ.get('OPENAI_API_KEY')
    del os.environ['OPENAI_API_KEY']
    print(f"   ✅ OPENAI_API_KEY removed from environment (was set)")
    print("   📋 This prevents mem0 from defaulting to OpenAI")
else:
    print("   ✅ OPENAI_API_KEY not set (good)")
print("=" * 70)

# Step 0b: CRITICAL - Install mock ollama module BEFORE any imports
# This replaces 'from ollama import Client' with HTTP API-based client
print("🔧 Step 0b: Installing mock ollama module (HTTP API)...")
import importlib.util
mock_spec = importlib.util.spec_from_file_location("mock_ollama_module", "/app/mock_ollama_module.py")
mock_module = importlib.util.module_from_spec(mock_spec)
mock_spec.loader.exec_module(mock_module)
mock_module.install_mock_ollama_module()
print("✅ Mock ollama module installed (HTTP API, no package required)")

# Step 1: Apply GDS patch
from mem0_gds_patch_v2 import patch_neo4j_graph
patch_neo4j_graph()
print("✅ GDS patch applied")

# Step 2: CRITICAL FIX - Patch factories BEFORE importing main
# Strategy: Block OpenAI embedder/LLM instantiation at the class level
# This prevents OpenAI from being created even if factory tries to select it
print("🔒 Step 2a: Patching factories BEFORE importing main...")
try:
    import sys
    import importlib
    
    # Import mem0.utils.factory directly
    mem0_factory = importlib.import_module('mem0.utils.factory')
    
    # CRITICAL: Patch EmbedderFactory.create to check config provider, not just parameter
    if hasattr(mem0_factory, 'EmbedderFactory'):
        original_embedder_create = mem0_factory.EmbedderFactory.create
        
        if hasattr(original_embedder_create, '__func__'):
            original_func = original_embedder_create.__func__
        else:
            original_func = original_embedder_create
        
        def patched_embedder_create(cls, provider=None, config=None, *args, **kwargs):
            """Block OpenAI embedder - enforce Ollama-only"""
            # CRITICAL: Force provider to 'ollama' regardless of input
            # Extract provider from config if present, then remove it
            if config is None:
                config = {}
            elif isinstance(config, str):
                # If config is a string, treat it as provider
                provider = config
                config = {}
            elif isinstance(config, dict):
                # Extract provider from config dict if present
                if 'provider' in config:
                    provider = config.get('provider')
                    # Remove provider from config - it's passed separately
                    config = {k: v for k, v in config.items() if k != 'provider'}
            elif not isinstance(config, dict):
                # Ensure config is a dict
                config = {}
            
            # FORCE ollama provider
            provider = 'ollama'
            
            # Block OpenAI attempts
            if provider == 'openai':
                raise RuntimeError(
                    "🚨 BLOCKED: OpenAI embedder requested - Ollama-only mode enforced\n"
                    "   Provider must be 'ollama', OpenAI is not allowed"
                )
            
            # Call original with FORCED ollama provider (provider separate, config without provider key)
            return original_func(cls, 'ollama', config, *args, **kwargs)
        
        if hasattr(original_embedder_create, '__func__'):
            mem0_factory.EmbedderFactory.create = classmethod(patched_embedder_create)
        else:
            mem0_factory.EmbedderFactory.create = staticmethod(patched_embedder_create)
        print("   ✅ EmbedderFactory patched (blocks OpenAI, enforces Ollama)")
    
    # Patch LLMFactory.create similarly
    if hasattr(mem0_factory, 'LLMFactory'):
        original_llm_create = mem0_factory.LLMFactory.create
        
        if hasattr(original_llm_create, '__func__'):
            original_func = original_llm_create.__func__
        else:
            original_func = original_llm_create
        
        def patched_llm_create(cls, provider=None, config=None, *args, **kwargs):
            """Block OpenAI LLM - enforce Ollama-only"""
            # DEBUG: Log what we received
            print(f"🔍 DEBUG: patched_llm_create called with provider={provider}, config={config}")
            
            # CRITICAL: Force provider to 'ollama' regardless of input
            # Extract provider from config if present, then remove it
            original_provider = provider
            if config is None:
                config = {}
            elif isinstance(config, str):
                # If config is a string, treat it as provider
                provider = config
                config = {}
            elif isinstance(config, dict):
                # Extract provider from config dict if present
                if 'provider' in config:
                    provider = config.get('provider')
                    # Remove provider from config - it's passed separately
                    config = {k: v for k, v in config.items() if k != 'provider'}
            elif not isinstance(config, dict):
                # Ensure config is a dict
                config = {}
            
            # FORCE ollama provider
            print(f"🔍 DEBUG: Forcing provider from '{original_provider}' to 'ollama'")
            provider = 'ollama'
            
            # Block OpenAI attempts
            if provider == 'openai':
                raise RuntimeError(
                    "🚨 BLOCKED: OpenAI LLM requested - Ollama-only mode enforced\n"
                    "   Provider must be 'ollama', OpenAI is not allowed"
                )
            
            # Call original with FORCED ollama provider (provider separate, config without provider key)
            print(f"🔍 DEBUG: Calling original_func with provider='ollama'")
            return original_func(cls, 'ollama', config, *args, **kwargs)
        
        if hasattr(original_llm_create, '__func__'):
            mem0_factory.LLMFactory.create = classmethod(patched_llm_create)
        else:
            mem0_factory.LLMFactory.create = staticmethod(patched_llm_create)
        print("   ✅ LLMFactory patched (blocks OpenAI, enforces Ollama)")
    
    print("✅ Factories patched successfully (OpenAI blocked, Ollama enforced)")
        
except Exception as e:
    import traceback
    print(f"❌ CRITICAL: Factory patching failed: {e}")
    print(f"   Traceback: {traceback.format_exc()}")
    sys.exit(1)

# Step 2b: Apply Ollama-only enforcement (but DON'T import main yet)
print("\n🔒 Step 2b: Applying Ollama-only enforcement (without importing main)...")
import importlib.util
spec = importlib.util.spec_from_file_location("enforce_ollama_only", "/app/enforce_ollama_only.py")
enforce_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(enforce_module)

enforcer = enforce_module.OllamaOnlyEnforcer()

# CRITICAL: Only validate Ollama and build config - DON'T import main
# We'll import main after factories are patched
print("🔍 Validating Ollama connection...")
enforcer.validate_ollama_connection()
print("🔧 Building Ollama-only configuration...")
ollama_config = enforcer.build_ollama_only_config()
print("🔒 Applying OpenAI blocking patches (without importing main)...")
enforcer.patch_mem0_openai_blocker()
print("✅ Ollama enforcement initialized (main not imported yet)")

# Step 3: CRITICAL FIX - Patch Memory.from_config BEFORE importing main
# BUT: Don't import Memory yet - it might trigger ollama imports
# Instead, patch it after importing main but before MEMORY_INSTANCE is created
print("\n🔒 Step 3: Preparing to patch Memory.from_config...")
# We'll patch it after main imports Memory, but before MEMORY_INSTANCE is created

# Step 4: CRITICAL - Replace DEFAULT_CONFIG in main.py BEFORE it executes line 59
# Root cause: main.py line 59 executes MEMORY_INSTANCE = Memory.from_config(DEFAULT_CONFIG) at import time
# Solution: Use importlib to load main.py, modify DEFAULT_CONFIG in the module dict BEFORE executing
print("\n🔒 Step 4: Loading main.py and replacing DEFAULT_CONFIG before MEMORY_INSTANCE creation...")
import sys
import importlib.util
import types

# Use importlib to load main.py WITHOUT executing it yet
main_path = "/app/main.py"
spec = importlib.util.spec_from_file_location("main", main_path)
main_module = types.ModuleType('main')
main_module.__file__ = main_path

# Read source and modify DEFAULT_CONFIG before executing
with open(main_path, 'r') as f:
    main_source = f.read()

# Replace DEFAULT_CONFIG assignment: find line 36-58 and replace with our config
lines = main_source.split('\n')
default_config_start = None
default_config_end = None

for i, line in enumerate(lines):
    if 'DEFAULT_CONFIG = {' in line:
        default_config_start = i
    elif default_config_start is not None and 'MEMORY_INSTANCE = Memory.from_config(DEFAULT_CONFIG)' in line:
        default_config_end = i
        break

if default_config_start is not None and default_config_end is not None:
    # Replace DEFAULT_CONFIG lines with our Ollama config
    import json
    config_str = json.dumps(ollama_config, indent=4)
    # Format as Python dict
    config_str = config_str.replace('"', "'").replace("'", '"')  # Keep double quotes
    config_str = 'DEFAULT_CONFIG = ' + config_str.replace('\n', '\n    ')  # Indent
    
    modified_lines = lines[:default_config_start] + [config_str] + lines[default_config_end:]
    main_source_modified = '\n'.join(modified_lines)
    
    print("   ✅ DEFAULT_CONFIG replaced in source")
else:
    print("   ⚠️  Could not find DEFAULT_CONFIG boundaries, using original source")
    main_source_modified = main_source

# Execute modified source
exec(compile(main_source_modified, main_path, 'exec'), main_module.__dict__)
sys.modules['main'] = main_module

# Import main (now it's already loaded)
import main

# Verify
if hasattr(main, 'DEFAULT_CONFIG'):
    llm_provider = main.DEFAULT_CONFIG.get('llm', {}).get('provider', 'unknown')
    embedder_provider = main.DEFAULT_CONFIG.get('embedder', {}).get('provider', 'unknown')
    print(f"   ✅ DEFAULT_CONFIG verified: LLM={llm_provider}, Embedder={embedder_provider}")
    if llm_provider != 'ollama' or embedder_provider != 'ollama':
        print(f"   ⚠️  Still wrong providers, forcing override...")
        main.DEFAULT_CONFIG = ollama_config
        if hasattr(main, 'MEMORY_INSTANCE'):
            from mem0 import Memory
            main.MEMORY_INSTANCE = Memory.from_config(ollama_config)

print("✅ main module configured for Ollama-only operation")

# Step 5: Start uvicorn
import uvicorn
port = int(os.getenv('MEM0_PORT', '8888'))
print(f"\n🚀 Starting mem0 server on port {port}...")
print("=" * 70)
uvicorn.run('main:app', host='0.0.0.0', port=port, reload=False)
PYTHON


if default_config_start is not None and default_config_end is not None:
    # Replace DEFAULT_CONFIG lines with our Ollama config
    import json
    config_str = json.dumps(ollama_config, indent=4)
    # Format as Python dict
    config_str = config_str.replace('"', "'").replace("'", '"')  # Keep double quotes
    config_str = 'DEFAULT_CONFIG = ' + config_str.replace('\n', '\n    ')  # Indent
    
    modified_lines = lines[:default_config_start] + [config_str] + lines[default_config_end:]
    main_source_modified = '\n'.join(modified_lines)
    
    print("   ✅ DEFAULT_CONFIG replaced in source")
else:
    print("   ⚠️  Could not find DEFAULT_CONFIG boundaries, using original source")
    main_source_modified = main_source

# Execute modified source
exec(compile(main_source_modified, main_path, 'exec'), main_module.__dict__)
sys.modules['main'] = main_module

# Import main (now it's already loaded)
import main

# Verify
if hasattr(main, 'DEFAULT_CONFIG'):
    llm_provider = main.DEFAULT_CONFIG.get('llm', {}).get('provider', 'unknown')
    embedder_provider = main.DEFAULT_CONFIG.get('embedder', {}).get('provider', 'unknown')
    print(f"   ✅ DEFAULT_CONFIG verified: LLM={llm_provider}, Embedder={embedder_provider}")
    if llm_provider != 'ollama' or embedder_provider != 'ollama':
        print(f"   ⚠️  Still wrong providers, forcing override...")
        main.DEFAULT_CONFIG = ollama_config
        if hasattr(main, 'MEMORY_INSTANCE'):
            from mem0 import Memory
            main.MEMORY_INSTANCE = Memory.from_config(ollama_config)

print("✅ main module configured for Ollama-only operation")

# Step 5: Start uvicorn
import uvicorn
port = int(os.getenv('MEM0_PORT', '8888'))
print(f"\n🚀 Starting mem0 server on port {port}...")
print("=" * 70)
uvicorn.run('main:app', host='0.0.0.0', port=port, reload=False)
PYTHON
