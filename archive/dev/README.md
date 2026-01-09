# Development Files Archive

**Date Archived:** 2026-01-09
**Reason:** Production repo cleanup

## Archived Files

### docker-compose.dev.yml
- **Issue:** Uses upstream `mem0ai/mem0:latest` instead of custom `mem0-fixed:local`
- **Issue:** Has security problems (anonymous admin, sign-up enabled)
- **Issue:** References MacBook Pro (non-existent hardware)
- **Status:** Archived, not suitable for production use

### docker-compose.generic.yml (was docker-compose.yml)
- **Issue:** Generic template, unclear which environment
- **Issue:** References intel-llm-router (removed dependency)
- **Issue:** Has external path references (../../scripts/)
- **Status:** Archived, use docker-compose.prd.yml or test.yml instead

## Production Setup

This repo now contains ONLY production-ready files:

- **docker-compose.prd.yml** - Production deployment (Mac Studio)
- **docker-compose.test.yml** - Test environment (Mac Studio)

Both use:
- Custom image: `mem0-fixed:local`
- Self-contained paths
- Proper security (no anonymous access)
- Environment-specific configs

## Note

If you need a dev environment, create a separate dev repo or fork.
This repo is for **Mac Studio production/test deployments only**.
