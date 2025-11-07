# mem0 Ollama-Only Enforcement

**Status**: ✅ IMPLEMENTED  
**Date**: 2025-11-03  
**Purpose**: Enforce strict Ollama-only usage - NO OpenAI fallback allowed

## Problem Statement

mem0 production service was using OpenAI API despite environment variables configured for Ollama:

- **Environment variables SET**: `OLLAMA_URL`, `MEM0_LLM_PROVIDER=ollama`, `MEM0_EMBEDDER_PROVIDER=ollama`
- **Container logs showed**: `HTTP Request: POST https://api.openai.com/v1/chat/completions`
- **User mandate**: "NO OpenAI usage - abort if Ollama fails"

## Solution

Comprehensive enforcement system that:

1. **Validates Ollama before startup** - Aborts if Ollama unavailable (no fallback)
2. **Blocks OpenAI calls at runtime** - Patches HTTP clients to block OpenAI URLs
3. **Forces Ollama-only configuration** - Overrides mem0's default config
4. **Removes OpenAI dependency** - OPENAI_API_KEY no longer required

## Implementation

### Files Created/Modified

1. **`enforce_ollama_only.py`** (NEW) - Core enforcement engine
   - Validates Ollama connection and model availability
   - Patches mem0 to block OpenAI calls
   - Generates Ollama-only configuration
   - Aborts if Ollama unavailable (no fallback)

2. **`start_mem0_with_patch.sh`** (UPDATED) - Startup script
   - Now includes Ollama-only enforcement step
   - Applies enforcement before mem0 server starts
   - Aborts if Ollama validation fails

3. **`docker-compose.prd.yml`** (UPDATED) - Production compose file
   - Removed OPENAI_API_KEY requirement (commented out)
   - Added `enforce_ollama_only.py` volume mount
   - Removed `force_ollama_config.py` (replaced)

4. **`deploy_prd.sh`** (UPDATED) - Deployment script
   - Removed OPENAI_API_KEY from required variables check

5. **`test_ollama_enforcement.py`** (NEW) - Validation test suite
   - Tests Ollama validation
   - Tests OpenAI blocking
   - Tests config generation

## Enforcement Mechanisms

### 1. Pre-Startup Validation

Before mem0 server starts:
- Validates Ollama connection (HTTP check)
- Verifies required models are available (LLM + embedder)
- **ABORTS if Ollama unavailable** (exit code 1)

```python
def validate_ollama_connection(self, timeout: int = 10) -> bool:
    # Tests: /api/tags endpoint
    # Checks: LLM model exists, embedder model exists
    # Action: sys.exit(1) if unavailable
```

### 2. Runtime OpenAI Blocking

Patches HTTP clients to block OpenAI URLs:
- Blocks `httpx` requests to `api.openai.com`
- Blocks `openai` library imports
- Raises `RuntimeError` if OpenAI call attempted

```python
def patch_mem0_openai_blocker(self):
    # Patches httpx.Client to block OpenAI domains
    # Patches builtins.__import__ to block openai library
    # Raises RuntimeError if OpenAI call detected
```

### 3. Configuration Override

Forces Ollama-only configuration:
- Overrides `main.DEFAULT_CONFIG` with Ollama-only config
- Removes all OpenAI fallback options
- Sets provider to `ollama` for both LLM and embedder

```python
config = {
    "llm": {"provider": "ollama", ...},
    "embedder": {"provider": "ollama", ...},
    # NO OpenAI options
}
```

## Environment Variables

### Required

- `OLLAMA_URL` - Ollama service URL (default: `http://host.docker.internal:11434`)
- `MEM0_LLM_MODEL` - LLM model name (default: `mistral:7b-instruct-q5_K_M`)
- `MEM0_EMBEDDER_MODEL` - Embedder model name (default: `nomic-embed-text:latest`)
- `POSTGRES_PASSWORD` - PostgreSQL password
- `MEM0_API_KEY` - mem0 API key
- `GRAFANA_PASSWORD` - Grafana admin password

### Optional (No longer required)

- `OPENAI_API_KEY` - **IGNORED** (will not be used even if set)

## Deployment

### Production Deployment

```bash
cd /Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale
./deploy_prd.sh up
```

**What happens**:

1. Validates environment variables (OPENAI_API_KEY no longer required)
2. Starts containers
3. **Enforcement runs during startup**:
   - Validates Ollama connection
   - Blocks OpenAI calls
   - Forces Ollama-only config
   - **Aborts if Ollama unavailable** (container fails)

### Startup Sequence

```
1. Apply GDS patch (Neo4j compatibility)
2. Initialize Ollama-only enforcer
3. Validate Ollama connection (ABORT if fails)
4. Patch mem0 to block OpenAI
5. Override mem0 DEFAULT_CONFIG
6. Start uvicorn server
```

## Validation

### Run Test Suite

```bash
# Inside mem0 container
docker exec -it mem0_server_prd python3 /app/test_ollama_enforcement.py
```

**Tests**:

1. ✅ **Ollama Validation** - Verifies Ollama is accessible
2. ✅ **OpenAI Blocking** - Verifies OpenAI calls are blocked
3. ✅ **Config Generation** - Verifies Ollama-only config

### Manual Validation

```bash
# Check Ollama is accessible
curl http://host.docker.internal:11434/api/tags

# Check mem0 logs (should show Ollama-only enforcement)
docker logs mem0_server_prd | grep -i "ollama-only"

# Verify no OpenAI calls in logs
docker logs mem0_server_prd | grep -i "openai"  # Should be empty or show "BLOCKED"
```

## Troubleshooting

### Issue: "Ollama connection failed"

**Cause**: Ollama service not running or unreachable

**Solution**:
1. Verify Ollama is running on host:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. Check OLLAMA_URL in .env:
   ```bash
   grep OLLAMA_URL .env
   # Should be: http://host.docker.internal:11434 (from Docker)
   ```

3. Test from container:
   ```bash
   docker exec -it mem0_server_prd curl http://host.docker.internal:11434/api/tags
   ```

### Issue: "LLM model not found"

**Cause**: Required Ollama model not pulled

**Solution**:
1. Pull required models:
   ```bash
   ollama pull mistral:7b-instruct-q5_K_M
   ollama pull nomic-embed-text:latest
   ```

2. Verify models are available:
   ```bash
   ollama list
   ```

### Issue: OpenAI calls still happening

**Cause**: Enforcement not applied correctly

**Solution**:
1. Check enforcement script is mounted:
   ```bash
   docker exec -it mem0_server_prd ls -la /app/enforce_ollama_only.py
   ```

2. Check startup logs for enforcement:
   ```bash
   docker logs mem0_server_prd | grep -i "ollama-only enforcement"
   ```

3. Run test suite to verify:
   ```bash
   docker exec -it mem0_server_prd python3 /app/test_ollama_enforcement.py
   ```

## Expected Behavior

### Successful Startup

```
==================================================================
🔒 OLLAMA-ONLY ENFORCEMENT INITIALIZING
==================================================================
✅ GDS patch applied
==================================================================
🔒 OLLAMA-ONLY ENFORCEMENT INITIALIZED
==================================================================
Ollama URL: http://host.docker.internal:11434
LLM Model: mistral:7b-instruct-q5_K_M
Embedder Model: nomic-embed-text:latest
OpenAI: BLOCKED (no fallback allowed)
==================================================================

🔍 Validating Ollama connection...
✅ Ollama connection validated
   LLM model 'mistral:7b-instruct-q5_K_M': Available
   Embedder model 'nomic-embed-text:latest': Available

🔒 Patching mem0 to block OpenAI calls...
   ✅ httpx patched (OpenAI blocking at runtime)
   ✅ Built-in import patched

✅ Ollama-only configuration enforced
==================================================================

✅ mem0 configured for Ollama-only operation
==================================================================

🚀 Starting mem0 server on port 8888...
```

### Failed Startup (Ollama Unavailable)

```
==================================================================
🔒 OLLAMA-ONLY ENFORCEMENT INITIALIZING
==================================================================
✅ GDS patch applied
==================================================================
🔒 OLLAMA-ONLY ENFORCEMENT INITIALIZED
==================================================================

🔍 Validating Ollama connection...
❌ CRITICAL: Cannot connect to Ollama
   URL: http://host.docker.internal:11434
   Error: Connection refused

🚨 ABORTING: Ollama connection failed - no fallback allowed
```

**Container exits with code 1** - mem0 does not start.

## Cost Impact

**Before**: OpenAI fallback allowed → $0-45/month (depending on usage)

**After**: Ollama-only → **$0/month** (100% local)

**Savings**: Up to $45/month + elimination of OpenAI dependency

## Compliance

- ✅ **User mandate met**: "NO OpenAI usage - abort if Ollama fails"
- ✅ **Zero OpenAI calls**: Blocked at multiple levels
- ✅ **Fail-safe**: Aborts if Ollama unavailable (no silent fallback)
- ✅ **Transparent**: All enforcement actions logged

## Future Enhancements

1. **Ollama health monitoring** - Periodic checks during runtime
2. **Automatic retry** - Retry Ollama connection before aborting
3. **Model pre-warming** - Pull models if missing during validation
4. **Metrics dashboard** - Track Ollama usage vs blocked OpenAI attempts

