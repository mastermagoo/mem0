# mem0 PRD Optimization – Wingman 10‑Point Plan (Awaiting Approval)

Date: 2025-11-22  
Status: AWAITING APPROVAL (no execution until approved)  
Oversight: Wingman (per CLAUDE.md) with Three‑Layer Protection  
Branch policy: After every approved change, prepare commit + evidence; push to `wingman` only when User explicitly says “push to github”

---

## 1) Deliverables

- API accepts raw‑add:
  - Extend request model to include `infer` (default false) and pass to `add(..., infer)`
- Local layered image (no hardcoding, env‑driven) with Ollama‑only config:
  - LLM (extraction only): `provider=ollama`, `model=qwen2.5:3b`, `temperature=0.1`, `max_tokens=128`, `top_p=0.1`
  - Embedder: `provider=ollama`, `model=nomic-embed-text:latest`, `embedding_dims=768`
  - Base URL via env `OLLAMA_BASE_URL` (injected by compose/k8s per env). Default in compose: `http://ollama:11434` (service DNS)
- Session caching + warm‑up probes (LLM+embedder) at startup
- Telemetry non‑blocking (telemetry failures never block writes)
- Compose restored from backup, mounts verified as files, start via uvicorn
- External‑call sentinel active (policy/log monitoring only; zero external API usage by sentinel); evidence captured
- Evidence bundle + plan update after each approved step; prepare commit; push only on explicit approval

---

## 2) Success Criteria (SLOs)

- Writes: p95 ≤ 5s; success ≥ 99.9%
- Reads: p95 ≤ 1s; success ≥ 99.99%
- Persistence: +5 rows after test and retrievable by `user_id`
- External calls: 0 OpenAI/API calls (enforced with network policy + sentinel; evidenced)

---

## 3) Boundaries

- Scope: mem0 PRD only; no changes to other services
- `memories.vector` remains 768 (no schema changes)
- Telemetry is optional; may remain at 1536 but must never block writes
- Neo4j: out of scope for this plan (not required for raw‑add persistence)

---

## 4) Dependencies

- Ollama reachable at `${OLLAMA_BASE_URL}` (compose default `http://ollama:11434`); models pre‑pulled: `qwen2.5:3b`, `nomic-embed-text:latest`
- Compose restored from latest known‑good backup; `image: mem0-fixed:local` asserted
  - Backup artifact path + checksum recorded in evidence
- Postgres healthy (TCP:5432); Neo4j excluded from scope for this plan
- Secrets by env/secret store; no secrets in VCS

---

## 5) Mitigation (Three‑Layer Protection)

- Data: no destructive ops; DB snapshot available
- Image: record immutable image digest; tag current `mem0-fixed:local` as `mem0-fixed:broken-<ts>`; instant retag rollback to digest
- Orchestration: compose/env backups; `down`/`up` verified
- DB: pair app rollback with DB snapshot/PITR checklist (timestamps + hashes in evidence)
- Rollback verification: restore digest, bring up stack, health passes, canary write passes, logs clean (no errors)

---

## 6) Test Process (Wingman Gates)

1. Preflight
   - Assert compose image tag and mounts as files
   - Assert models exist in Ollama
   - Tag current image for rollback
2. Deploy and health
   - Force recreate; wait healthy
3. Canary
   - One write with `infer=false` → `id` present → DB +1 → OpenAI=0
4. Load gate (per SLO measurement)
   - Scenarios: concurrency = 1 / 4 / 8; duration 10–15 min each; N ≥ 500 per scenario
   - Metrics: p50/p95/p99, error rate, CPU/RAM; report cold vs warm cache separately
5. Retrieval
   - Query by `user_id`; verify rows present

### Persistence Test Dataset and Expected Deltas
- Phase 3 (Canary): 1 write → DB +1
- Phase 4 (Load): 500 writes × 3 scenarios (1/4/8 concurrency) = 1500 → DB +1500
- Phase 5 (Retrieval): 0 writes → DB +0
- Total expected delta across phases: +1501 rows

---

## 7) Test Results Format (Evidence)

`results.json` (committed with each approved step):
```json
{
  "config": { "llm": "...", "embedder": "...", "base_url": "..." },
  "writes": { "count": 0, "success": true, "p50_s": 0, "p95_s": 0, "p99_s": 0, "max_s": 0, "error_rate": 0 },
  "db": { "before": 0, "after": 0 },
  "sentinel": { "external_calls_last_10m": 0 },
  "containers": { "healthy": true }
}
```
Evidence also includes: iptables egress rules, docker stats snapshots, test dataset checksums, git commit SHA, OpenAPI hash, and redacted logs.

---

## 8) Task Classification

- Creative: configuration, behavior isolation (raw‑add)  
- Mechanical: build, deploy, verify, evidence capture

---

## 9) Retrospective (Post‑Execution)

- What fixed persistence; deltas vs baseline; final p95 and max; regressions (if any)  
- Lessons and follow‑ups recorded in the action plan

---

## 10) Performance & Resource Impact (Per CLAUDE.md Constraints)

- Targets: raw‑add (infer=false) p95 ≤ 2s; extraction path (infer=true) p95 ≤ 5s; reads p95 ≤ 1s
- Models:
  - LLM (extraction only): `qwen2.5:3b` with tight params (temperature=0.1, max_tokens=128, top_p=0.1)
  - Embedder: `nomic-embed-text:latest`, `embedding_dims=768`
- Warm‑up & caching (readiness‑gated):
  - Readiness requires 2× LLM extraction probes (<500ms each, 100% success) + 2× embedding probes (<200ms each, 100% success)
  - Cache: keys per model+params; TTL defined; invalidate on model/config change
  - Workers 1–2; raise only if SLOs met and error budget green
- Resource caps (compose, scoped to mem0 only):
  - mem0: cpus 2.0, memory 4g (tune based on load results to maintain p95 ≤ 5s)
  - Tuning process: if p95 > SLO at 2.0cpu/4g, increase by 0.5cpu/1g steps, retest per load gate; document final caps in retrospective

---

### Wingman Mandatory Controls (Per CLAUDE.md)

- No execution until you approve this plan
- After every approved change: prepare commit + evidence; push to `wingman` only when User explicitly says “push to github”
- External‑call sentinel stays active (no external API usage); logs redacted; Three‑Layer Protection enforced

---

### Enforcement & Controls Addendum

- Networking enforcement: deny‑all egress for mem0; allowlist only Postgres, Neo4j, Ollama; DNS pinning; runtime guard fails fast on non‑allowlisted hosts. Evidence includes iptables config and netflow showing zero egress.
- API contract: OpenAPI updated to include `infer` with default=false; compatibility tests ensure clients without `infer` continue to work. Deprecation window documented.
- Telemetry pipeline: async bounded queue with timeout <100ms (≈2% of write SLO) and circuit‑breaker; drops on pressure; alert if drop rate >1%. Telemetry embedding dimension (1536) is independent of storage vector size (768) and does not block writes.
- Persistence tests: deterministic dataset; idempotency key to avoid duplicates; cleanup post‑tests. Expected deltas per phase documented.
- Security/PII: data classification, TLS in‑cluster/off‑cluster, retention windows, redaction policy for evidence; no secrets in logs or VCS.
- Observability: standardized metrics (request_count, latency_histogram, error_count, queue_depth, cache_hit_rate), correlation IDs, dashboards and alerts (SLO breach, error spikes, queue saturation, egress attempts).

#### SLO & Error Budget
- Success criteria: writes success ≥ 99.9% (per 24h); error budget = 0.1% (≤ 86 failures per 86,400 requests in 24h rolling window).

#### Runtime Guard Implementation
- Code‑level Python socket wrapper validates DNS resolution against allowlist before connect; raises SecurityError on violation (defense‑in‑depth with network egress rules).

#### TLS Scope
- External API → mem0: TLS mandatory
- mem0 → Postgres: TLS with `sslmode=require`
- mem0 → Ollama: HTTP allowed on trusted internal network (same host/network); TLS optional if supported and configured

#### Circuit‑Breaker Parameters
- Open after 5 consecutive failures or >10% error rate in 1 min
- Half‑open after 30s; close after 3 successful attempts

#### Correlation IDs
- UUID v4 generated at API gateway; injected into all logs, added to DB payload (if schema allows), forwarded to Ollama via headers if supported

#### Alerts (Severity & Routing)
- P1 (immediate): any egress attempt, >1% error rate → PagerDuty + Slack #wingman‑alerts
- P2 (15 min): SLO breach
- P3 (1 h): queue saturation >80%

#### Redaction Policy
- Redact passwords, API keys, tokens, and PII (email/phone regex). Replace user_id with a stable hash in evidence. Redaction executed by pre‑processing script before committing evidence.

#### Workers
- Start with 1 worker; increase to 2 only if p95 SLO is met at 1 and throughput headroom is needed

#### Deployment Style
- Force‑recreate acceptable for testing. For PRD, use blue‑green rollout with zero downtime; document cutover steps and rollback.

#### Backup Restoration Preflight
- Validate latest compose/env backup restore in staging before using as baseline; record artifact paths and checksums in evidence.

---

Approve (Yes/No). No changes will be made until you approve.


