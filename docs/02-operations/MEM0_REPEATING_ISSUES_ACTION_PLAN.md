# mem0 Repeating Issues - Root Cause & Permanent Fix Action Plan

**Date:** 2025-11-22 19:30  
**Status:** ✅ EXECUTING (Wingman oversight) - No Git push  
**Oversight:** Wingman 10-Point Framework + Three-Layer Protection  
**Problem:** mem0 OpenAI→Ollama issue repeated; persistence path not writing despite 200 responses

---

## 🔎 CURRENT STATUS SNAPSHOT

- ✅ Containers: 5/5 healthy (`mem0_server_prd` healthy)
- ✅ Config: LLM+Embedder moved to Ollama only
  - LLM: `provider=ollama`, `model=mistral:7b-instruct-q5_K_M`, `ollama_base_url=http://host.docker.internal:11434`
  - Embedder: `provider=ollama`, `model=nomic-embed-text:latest`, `embedding_dims=768`, `ollama_base_url` set
- ✅ Compose image assertion: `mem0-fixed:local` enforced (auto-patch in plan)
- ✅ OpenAI signals: 0 (sentinel running; embeddings detector included)
- ⚠ Telemetry: `mem0migrations.vector` set to `vector(1536)` to clear startup insert errors (embedder path emits 1536 for telemetry)
- ❌ Persistence: POST /memories returns 200 but no new rows (DB count remains 147)
- ⏱ Performance (5 runs): avg 16.07s, max 18.46s; target p95 ≤ 5s not met (yet)

---

## 🚨 REPEATING ISSUE ANALYSIS

### Issue Statement
mem0 continued to call OpenAI API and/or ignore env overrides; recent builds hardcoded OpenAI defaults in main.py.

### Confirmed Root Cause
Hardcoded defaults in main.py (`provider="openai"`) for `llm` and `embedder`. Env overrides not applied at import time.

### Fix Path Implemented
- Rebuild local image by layering on existing `mem0-fixed:local` and patching `/app/main.py` at build time:
  - `llm.provider=openai → ollama`, `embedder.provider=openai → ollama`
  - Add `ollama_base_url` under both `llm.config` and `embedder.config`
  - LLM model set to local `mistral:7b-instruct-q5_K_M`
  - Embedder model `nomic-embed-text:latest`, `embedding_dims=768`
- Unified compose commands; compose auto-patch ensures `image: mem0-fixed:local`
- Wingman sentinels running (OpenAI domain + embeddings patterns)

---

## ✅ PERMANENT FIX - OPTIONS (RETAINED)
- Option A: Rebuild mem0 Image with Ollama Config (RECOMMENDED) — implemented locally via layered patch image
- Option B: Runtime Config Patch (EMERGENCY ONLY) — not used
- Option C: Use Correct Branch/Image (FASTEST) — not found; proceeded with A

---

## 📋 WINGMAN 10-POINT FRAMEWORK - STATUS

### 1. DELIVERABLES
- [x] Located/created Dockerfile for mem0 layer build
- [x] Patched `main.py` (LLM+embedder → Ollama; base URLs; models; dims)
- [x] Rebuilt and retagged `mem0-fixed:local`
- [x] All mem0 PRD containers healthy per compose
- [x] Verified zero OpenAI calls (sentinel + logs)
- [x] Plan updated with PRD strategy & resource impact
- [ ] Local git commit ready; push pending conflict resolution

### 2. SUCCESS_CRITERIA
- [x] Server healthy
- [x] Logs show Ollama usage; no OpenAI calls
- [ ] Persistence: new memories committed (currently failing)
- [ ] Performance: writes avg < 10s (currently ~16.1s)
- [ ] Zero errors after 5 test memories (business-level write failure still present)

### 3. BOUNDARIES
In scope: mem0 PRD image + config; compose assertion; sentinel/monitoring  
Out of scope: broader infra; TEST env; non-mem0 services

### 4. DEPENDENCIES
- Ollama reachable at host:11434 ✅
- Local models present ✅
- Backups taken (compose/env; DB dumps previously captured) ✅

### 5. MITIGATION
- Three-layer rollback documented (data/image/orchestration)
- Image tags preserved for quick restore
- Telemetry isolation planned (make non-blocking next)

### 6. TEST_PROCESS (Executed)
1) Preflight compose image assertion with auto-patch  
2) Build layered image; verify `DEFAULT_CONFIG` shows Ollama for both LLM and embedder  
3) Redeploy; container health check  
4) Canary + 4 tests; log scrapes for OpenAI and errors  
5) DB counts before/after  

### 7. TEST_RESULTS (Key Evidence)
```json
{
  "containers": { "expected": 5, "healthy": 5 },
  "openai_signals_last_10m": 0,
  "write_tests": {
    "requests": 5,
    "http_200": 5,
    "persisted": 0
  },
  "performance": {
    "avg_seconds": 16.07,
    "max_seconds": 18.46
  },
  "db_counts": {
    "before": 147,
    "after": 147
  },
  "telemetry": {
    "mem0migrations_vector_dims": 1536,
    "reason": "embedder telemetry path emits 1536; set to unblock startup inserts"
  }
}
```

### 8. TASK_CLASSIFICATION
CREATIVE: locate/modify build path; ensure deterministic config; validate runtime

### 9. RETROSPECTIVE (Interim)
- What failed previously: env-only overrides and removing OPENAI_API_KEY — import-time defaults won
- What worked: image-level config patch; compose assertion; sentinels; resource guardrails
- What remains: persistence path fix; performance target ≤ 5s p95; telemetry isolation

### 10. PERFORMANCE_REQUIREMENTS
Target post-fix: write p95 ≤ 5s; read p95 ≤ 1s; zero OpenAI calls  
Current: write avg ~16.1s; needs optimization and cache/warm-up activation

---

## 🧭 PRD-Grade Strategy & Resource Impact (Wingman Oversight)

### North-Star SLOs
- Writes: p95 ≤ 5s; success ≥ 99.9%
- Reads: p95 ≤ 1s; success ≥ 99.99%
- External calls: 0 OpenAI/API calls (enforced; sentinel-monitored; evidenced)

### Architecture Guardrails
- Dimensional invariant: 768 across embedder, memories.vector, and telemetry (with controlled migration rules)
- Env-driven config only; reject conflicting env at startup
- Telemetry isolation: non-blocking; circuit-break if degraded

### Reliability Plan
- Deterministic add path: support `infer=false` and minimal extraction; both persist or fail visibly
- Idempotency keys to avoid duplicates and enable safe retries
- Canary gate per deploy: 1 → 1RPS/1m → 5RPS/1m before full traffic

### Performance Plan
- Models: LLM `mistral:7b-instruct-q5_K_M` (local, warmed); embedder `nomic-embed-text:latest` (768)
- Warm-up & caching: session cache; boot warm-up hits; keep-alives
- Prompt/token discipline: trim; cap generation; timeouts with retries
- Target: current ~16.1s → ≤ 8s (M1) → ≤ 5s (M2)

### Observability & Ops
- Dashboards: latency, success, error budget, resources
- Sentinels: OpenAI/embedding detector; write success ratio; dim mismatch alarms
- Rollback: image tag + compose/env restore; DB invariants
- Logs: redaction enforced; evidence sanitized

### Resource Impact (Mac Studio M1 Max 32GB)
- PRD budgets:
  - mem0_server_prd: cpus 2.0; memory 4g
  - postgres: cpus 1.0; memory 1.5g
  - neo4j: cpus 1.0; memory 2g
  - grafana/bot: cpus 0.5; memory 512m each
  - Reserve ≥ 8–10 GB system headroom
- GPU: none; quantized models for CPU efficiency
- Concurrency caps: start 1–2 workers; raise post p95 ≤ 5s

### Milestones
- M1 (today): persistence fixed; telemetry non-blocking; write p95 ≤ 8s
- M2 (≤ 48h): write p95 ≤ 5s @ 10 RPS sustained; SLO dashboard live
- M3 (3–5 days): staged PRD rollout (5% → 50% → 100%)

### Risks & Mitigations
- Dim drift (768/1536): invariant check + migrations; alarms; fail-fast
- Model availability: pre-pull; health checks; fallback model
- Telemetry regressions: async/circuit-break; backlog replay

### Wingman Controls (Enforced)
- Pre-flight SLO gate; canary enforcement; live sentinels; rollback readiness; evidence capture required for any PRD change

---

## 🎯 NEXT ACTIONS (Sequenced, Safe to Execute)
1) Persistence fix (deterministic path):
   - Attempt raw add (`infer=false`) or minimal extract mode; verify DB increments and retrieval by `user_id`
   - If mem0’s add flow requires specific fields, supply them per OpenAPI (`user_id`/`agent_id`/`run_id` and message schema)
2) Telemetry isolation:
   - Make telemetry insert async/non-blocking; writes must not fail due to telemetry
3) Performance improvements:
   - Warm-up LLM + embedder; enable session caching; reduce prompt size and generation parameters; confirm p95 ≤ 8s, then ≤ 5s
4) Evidence update:
   - Append execution results with final counts, p95, and zero OpenAI proof

---

## 📌 NOTES
- Git push: blocked earlier by branch conflicts; will push to `wingman` after local commit is prepared and conflicts are resolved.  
- Security: Zero OpenAI usage enforced; logs redacted; credentials not committed.


