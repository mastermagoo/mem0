# CLAUDE.md — Mem0 Core Rules

**Repository:** mem0-system
**Purpose:** Production mem0 deployment for Mac Studio
**Last Updated:** 2026-02-16 (refactored to modular structure)

---

## 🚨 HARD RULES (non-negotiable)

1. **CLEAN ROOT DIRECTORY** — repository root MUST contain ≤ 15 files; NO loose `.py` or `.sh` files (see [file-organization.md](.claude/rules/file-organization.md))
2. **NO HARDCODED CREDENTIALS** — ALL credentials in `.env` files only; use environment variables everywhere (see [security.md](.claude/rules/security.md))
3. **ZERO EXTERNAL DEPENDENCIES** — 100% self-contained; NO references to intel-system or wingman-system (see [isolation.md](.claude/rules/isolation.md))
4. **PROPER FILE ORGANIZATION** — Python in `lib/`, scripts in `scripts/`, docs in `docs/` (see [file-organization.md](.claude/rules/file-organization.md))
5. **DOCKER LABELS & NAMING** — use `com.mem0-system.*` labels and `mem0_*` container names (see [docker-conventions.md](.claude/rules/docker-conventions.md))
6. **DOCUMENTATION REQUIREMENTS** — NEVER create files in root; ALL docs in `docs/` subdirectories (see [documentation.md](.claude/rules/documentation.md))
7. **GIT COMMIT RULES** — verify root clean, no credentials, no external deps before EVERY commit (see [git-workflow.md](.claude/rules/git-workflow.md))
8. **DEPLOYMENT SAFETY** — PRD uses `./deploy_prd.sh` only; TEST uses isolated ports/networks (see [deployment.md](.claude/rules/deployment.md))
9. **MONITORING & ALERTING** — health checks, backups, auto-start, Telegram alerts required (see [monitoring.md](.claude/rules/monitoring.md))
10. **PATH CONVENTIONS** — absolute paths in scripts, relative in configs, environment-driven (see [path-conventions.md](.claude/rules/path-conventions.md))

## Project

- **Repository:** `mem0-system`
- **Root:** `/Volumes/Data/ai_projects/mem0-system`
- **Purpose:** Shared memory service for wingman, intel-system, cv-automation
- **Environments:** TEST (ports 15432, 18888) + PRD (ports 5433, 8889)

## Repo Layout

- `lib/` — Python application code
- `scripts/` — Operational scripts (backup, monitoring)
- `docs/` — All documentation
- `telegram_bot/` — Telegram bot implementation
- `monitoring/` — Prometheus, Grafana configs
- `tests/` — Test scripts
- `tools/` — Utilities
- `deployment/` — Deployment artifacts
- `archive/` — Archived files

## Key Rules (see `.claude/rules/` for details)

- **Security**: [.claude/rules/security.md](.claude/rules/security.md) — never commit secrets, single source of truth (.env)
- **Isolation**: [.claude/rules/isolation.md](.claude/rules/isolation.md) — zero external dependencies, 100% self-contained
- **File Organization**: [.claude/rules/file-organization.md](.claude/rules/file-organization.md) — clean root directory (≤ 15 files)
- **Docker Conventions**: [.claude/rules/docker-conventions.md](.claude/rules/docker-conventions.md) — labels, naming, networks
- **Deployment**: [.claude/rules/deployment.md](.claude/rules/deployment.md) — TEST/PRD isolation, health checks
- **Monitoring**: [.claude/rules/monitoring.md](.claude/rules/monitoring.md) — data-aware monitoring, backups, alerts
- **Git Workflow**: [.claude/rules/git-workflow.md](.claude/rules/git-workflow.md) — commit rules, enforcement checklist
- **Documentation**: [.claude/rules/documentation.md](.claude/rules/documentation.md) — proper directory structure
- **Path Conventions**: [.claude/rules/path-conventions.md](.claude/rules/path-conventions.md) — absolute vs relative paths
- **Incidents**: [.claude/rules/incidents.md](.claude/rules/incidents.md) — incident history & key learnings

## Namespaces (Logical Isolation)

Each client system has its own namespace (`user_id`):
- `wingman` — Wingman system
- `intel-system` — Intel system
- `cv-automation` — CV automation system

## Environments

**TEST**: `http://localhost:18888` (API), port 15432 (Postgres)
**PRD**: `http://localhost:8889` (API), port 5433 (Postgres)

## Quick Verification

```bash
# Check root is clean (should be ≤ 15 files)
ls -la | grep -v "^d" | wc -l

# Check no credentials
grep -r "password\|secret\|key" --include="*.yml" --include="*.py" | grep -v "REPLACE_ME\|your_\|:?"

# Check no external deps
grep -r "intel-system\|wingman-system\|../../" --include="*.yml" --include="*.sh"

# Verify structure
tree -L 1 -d
```

## Philosophy

This repository is:
- **Production-focused** (PRD + TEST only)
- **Self-contained** (zero external dependencies)
- **Clean and organized** (proper file structure)
- **Secure** (no hardcoded credentials)
- **Resilient** (auto-recovery, data-aware monitoring)

**Keep it that way.**
