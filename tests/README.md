# mem0 Test Scripts

These scripts were used during initial development and validation.

## Test Files

- **test_integration.py** - Integration tests
- **test_llm_routing.py** - LLM routing validation
- **test_namespace_isolation.py** - Namespace isolation tests
- **test_ollama_enforcement.py** - Ollama-only enforcement tests

## Usage

These are historical validation scripts. The current deployment uses:

- `./deploy_prd.sh validate` - Production validation
- `./scripts/health_monitor.sh` - Health monitoring

## Note

These test scripts may reference old paths (intel-system) and may not work
with current deployment. They're kept for reference only.
