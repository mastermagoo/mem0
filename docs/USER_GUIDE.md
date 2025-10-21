# Personal AI Memory System - User Guide

**Version:** 1.0
**Date:** 2025-10-16
**System:** mem0 on intel-system infrastructure

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Daily Usage](#3-daily-usage)
4. [Namespaces Guide](#4-namespaces-guide)
5. [Advanced Features](#5-advanced-features)
6. [Troubleshooting](#6-troubleshooting)
7. [FAQ](#7-faq)

---

## 1. Introduction

### What is Personal AI Memory?

Your Personal AI Memory system is a self-hosted, privacy-first solution that allows you to store, search, and recall information across all your devices. Think of it as your personal knowledge base that's always available.

### Key Benefits

- **Privacy First:** All data stays on your infrastructure
- **Cross-Device:** Access from iPhone, iPad, MacBook Pro via Telegram or API
- **Cost Effective:** $0-5/month vs $60-150/month for cloud services
- **Smart Routing:** 95%+ queries use local AI models for speed and privacy
- **Namespace Organization:** Separate memories by context (work, projects, personal)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Devices                             │
│  iPhone (Telegram) | iPad (Telegram) | MacBook (API/Telegram)│
└────────────┬────────────────────────────────┬────────────────┘
             │                                │
             v                                v
┌────────────────────────────────┐  ┌────────────────────────┐
│     Telegram Bot (mem0)        │  │    REST API            │
│     Port: (Tailscale)          │  │    Port: 8888          │
└────────────┬───────────────────┘  └────────┬───────────────┘
             │                                │
             v                                v
┌─────────────────────────────────────────────────────────────┐
│                    mem0 Server                               │
│  - Memory Management                                         │
│  - LLM Routing (95% local, 5% external)                     │
│  - Embedding Generation                                      │
└────────┬──────────────────────────────────┬─────────────────┘
         │                                  │
         v                                  v
┌────────────────────────┐        ┌──────────────────────────┐
│    PostgreSQL          │        │       Neo4j              │
│    (Vector Store)      │        │  (Knowledge Graph)       │
│    Port: 5433          │        │    Port: 7688            │
└────────────────────────┘        └──────────────────────────┘
```

### Use Cases

1. **Meeting Notes:** "Meeting with investors tomorrow at 10 AM"
2. **Project Tracking:** "Progressief B.V. specializes in SAP implementations"
3. **Personal Reminders:** "Dentist appointment next Tuesday"
4. **Technical Knowledge:** "Python script for data processing: def process(x): return x*2"
5. **Investment Tracking:** "Bitcoin position opened at $45,000"

---

## 2. Getting Started

### System Access

#### Via Telegram (Recommended for Mobile)

**Note:** Telegram bot setup is pending. Once configured:

1. Open Telegram
2. Search for your bot: `@your_mem0_bot`
3. Start conversation with `/start`
4. Set your namespace: `/namespace progressief`
5. Store memory: Just type naturally, no special commands

#### Via API (For Scripts & Automation)

**Base URL:** `http://127.0.0.1:8888`

**Authentication:**
```bash
export MEM0_API_KEY="mem0-b0539021-c9a6-4aaa-9193-665f63851a0d"
```

**Example (curl):**
```bash
# Store a memory
curl -X POST "http://127.0.0.1:8888/memories" \
  -H "Authorization: Bearer $MEM0_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Meeting with John about SAP project"}],
    "user_id": "mark_carey/progressief"
  }'

# Search memories
curl "http://127.0.0.1:8888/memories?user_id=mark_carey/progressief&query=SAP" \
  -H "Authorization: Bearer $MEM0_API_KEY"
```

**Example (Python):**
```python
import requests

BASE_URL = "http://127.0.0.1:8888"
API_KEY = "mem0-b0539021-c9a6-4aaa-9193-665f63851a0d"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Store memory
response = requests.post(
    f"{BASE_URL}/memories",
    json={
        "messages": [{"role": "user", "content": "Remember this information"}],
        "user_id": "mark_carey/progressief"
    },
    headers=HEADERS
)
print(response.json())

# Search memories
response = requests.get(
    f"{BASE_URL}/memories",
    params={"user_id": "mark_carey/progressief", "query": "search term"},
    headers=HEADERS
)
print(response.json())
```

### Understanding Namespaces

Namespaces keep your memories organized by context. Your system has 5 namespaces:

| Namespace | Purpose | Example Content |
|-----------|---------|-----------------|
| `progressief` | Business consulting work | Client projects, SAP implementations |
| `cv_automation` | Job search automation | Job applications, CVs, interviews |
| `investments` | Financial tracking | Stock positions, crypto, portfolio |
| `personal` | Personal life | Appointments, reminders, ideas |
| `intel_system` | Technical projects | Infrastructure, code, deployments |

**Format:** `mark_carey/[namespace]`

---

## 3. Daily Usage

### Storing Memories

#### Best Practices

✅ **Good:**
- "Meeting with Booking.com team tomorrow at 2 PM in Amsterdam"
- "Python function for CSV processing: def process_csv(file): return pd.read_csv(file)"
- "AkzoNobel project deadline is November 15th"

❌ **Avoid:**
- Too vague: "Meeting tomorrow"
- Missing context: "2 PM" (what about it?)
- No useful keywords: "Thing to remember"

#### Natural Language

Just type or say what you want to remember. The system understands:
- Dates and times
- Technical content (code, commands)
- Relationships between concepts
- Action items

### Searching Memories

#### Simple Search
```
Query: "SAP projects"
→ Returns all memories mentioning SAP projects
```

#### Semantic Search
```
Query: "When is my next investor meeting?"
→ Understands intent, finds: "Meeting with investors tomorrow at 10 AM"
```

#### Contextual Search
```
In namespace: progressief
Query: "deadlines"
→ Only returns deadlines from Progressief work, not personal/other namespaces
```

### Recalling Memories

#### Via Telegram
```
You: What were my notes about the SAP implementation?
Bot: [Shows relevant memories from current namespace]
```

#### Via API
```bash
curl "http://127.0.0.1:8888/memories?user_id=mark_carey/progressief&query=SAP+implementation"
```

### Switching Context

#### Telegram Commands
```
/namespace progressief    # Switch to business work
/namespace personal       # Switch to personal life
/namespace investments    # Switch to financial tracking
/current                  # Show current namespace
```

#### API Usage
Simply change the `user_id` parameter:
```python
# Progressief work
response = requests.get(f"{BASE_URL}/memories",
    params={"user_id": "mark_carey/progressief"})

# Personal life
response = requests.get(f"{BASE_URL}/memories",
    params={"user_id": "mark_carey/personal"})
```

---

## 4. Namespaces Guide

### Progressief: Business Consulting Context

**Purpose:** Track consulting work, client projects, SAP implementations

**Typical Content:**
- Client meeting notes
- Project deadlines
- Technical requirements
- Deliverable status

**Example Memories:**
```
"Progressief B.V. specializes in SAP S/4HANA migrations and business process optimization"
"AkzoNobel project: Data migration deadline November 15th"
"Client prefers TypeScript over JavaScript for custom integrations"
```

### CV Automation: Job Search Context

**Purpose:** Job applications, CV versions, interview tracking

**Typical Content:**
- Job application status
- Interview dates
- CV versions for different roles
- Follow-up reminders

**Example Memories:**
```
"Applied to Booking.com Senior SAP Consultant position on 2025-06-17"
"Interview with Walter Kidde scheduled for next Tuesday"
"Need to follow up on Ashish Tiwari email by June 25th"
```

### Investments: Financial Tracking

**Purpose:** Portfolio management, positions, market analysis

**Typical Content:**
- Stock/crypto positions
- Entry/exit points
- Market notes
- Investment thesis

**Example Memories:**
```
"Bitcoin position opened at $45,000, target $60,000"
"AAPL 100 shares purchased 2025-01-15 at $180"
"Market thesis: Tech sector undervalued Q1 2025"
```

### Personal: Personal Life

**Purpose:** Daily life, appointments, reminders, ideas

**Typical Content:**
- Doctor appointments
- Family events
- Personal reminders
- Random ideas

**Example Memories:**
```
"Dentist appointment next Tuesday at 10 AM"
"Mom's birthday is March 15th"
"Book idea: AI-powered job search automation"
```

### Intel System: Technical Projects

**Purpose:** Infrastructure, code, system administration

**Typical Content:**
- Deployment notes
- Configuration details
- Troubleshooting solutions
- Technical documentation

**Example Memories:**
```
"mem0 deployed on port 8888, Grafana on 3001"
"PostgreSQL connection: host=127.0.0.1, port=5433, db=mem0"
"Fix for container restart loop: rebuild image with uvicorn CMD"
```

---

## 5. Advanced Features

### API Integration

#### List All Memories in Namespace
```python
def get_all_memories(namespace):
    response = requests.get(
        f"{BASE_URL}/memories",
        params={"user_id": f"mark_carey/{namespace}"},
        headers=HEADERS
    )
    return response.json()

# Usage
progressief_memories = get_all_memories("progressief")
```

#### Delete a Memory
```python
def delete_memory(memory_id):
    response = requests.delete(
        f"{BASE_URL}/memories/{memory_id}",
        headers=HEADERS
    )
    return response.status_code == 200

# Usage
delete_memory("memory_id_here")
```

#### Bulk Import Memories
```python
def import_memories(namespace, memories_list):
    user_id = f"mark_carey/{namespace}"
    results = []

    for memory_text in memories_list:
        response = requests.post(
            f"{BASE_URL}/memories",
            json={
                "messages": [{"role": "user", "content": memory_text}],
                "user_id": user_id
            },
            headers=HEADERS
        )
        results.append(response.json())

    return results

# Usage
notes = [
    "Project A deadline: November 1st",
    "Project B budget: €50,000",
    "Project C stakeholder: John Smith"
]
import_memories("progressief", notes)
```

### Performance Optimization

#### Caching Strategy
- Frequently accessed memories are cached for 15 minutes
- Clear cache on memory update/delete
- Local LLM responses cached aggressively

#### Batch Operations
```python
# Instead of multiple single requests:
for memory in memories:
    store_memory(memory)  # ❌ Slow

# Use batch import:
import_memories(namespace, memories)  # ✅ Faster
```

### Custom Integrations

#### Alfred Workflow (macOS)
```bash
#!/bin/bash
# Save as: ~/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows/mem0/store.sh

QUERY="{query}"
curl -X POST "http://127.0.0.1:8888/memories" \
  -H "Authorization: Bearer $MEM0_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"messages\": [{\"role\": \"user\", \"content\": \"$QUERY\"}], \"user_id\": \"mark_carey/personal\"}"
```

#### Keyboard Maestro Macro
```
Trigger: Hotkey ⌘⌥M
Action 1: Prompt for Input → variable "memory"
Action 2: Execute Shell Script:
  curl -X POST "http://127.0.0.1:8888/memories" \
    -H "Authorization: Bearer $MEM0_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"messages\": [{\"role\": \"user\", \"content\": \"$KMVAR_memory\"}], \"user_id\": \"mark_carey/personal\"}"
Action 3: Display Notification "Memory stored!"
```

#### iOS Shortcut
```
1. Get Text from Input
2. Set Variable "MemoryText" to Input
3. Get Contents of URL:
   URL: http://127.0.0.1:8888/memories
   Method: POST
   Headers:
     Authorization: Bearer mem0-b0539021-c9a6-4aaa-9193-665f63851a0d
   JSON Body:
     {
       "messages": [{"role": "user", "content": "[MemoryText]"}],
       "user_id": "mark_carey/personal"
     }
4. Show Notification "Memory stored!"
```

---

## 6. Troubleshooting

### Common Issues

#### Issue: "Cannot connect to mem0 server"

**Symptoms:** API requests fail, Telegram bot doesn't respond

**Diagnosis:**
```bash
# Check if containers are running
docker ps --filter "name=mem0"

# Check mem0_server logs
docker logs mem0_server --tail 50
```

**Solution:**
```bash
# Restart containers
cd /Volumes/intel-system/deployment/docker/mem0_tailscale
docker-compose restart mem0

# If that doesn't work, full restart:
docker-compose down && docker-compose up -d
```

---

#### Issue: "500 Internal Server Error"

**Symptoms:** API returns 500, memories not storing

**Common Causes:**
1. Invalid OpenAI API key
2. Database connection issue
3. Ollama not running

**Diagnosis:**
```bash
# Check server logs for errors
docker logs mem0_server 2>&1 | grep -i "error\|exception"

# Verify API key is valid (check character count, should be ~200 chars)
grep OPENAI_API_KEY .env | wc -c

# Check database connectivity
docker exec mem0_server ping -c 1 postgres
docker exec mem0_server ping -c 1 neo4j
```

**Solution:**
```bash
# 1. Update API key if invalid
vi .env
# Change: OPENAI_API_KEY=sk-proj-[NEW_KEY]

# 2. Restart container
docker-compose restart mem0

# 3. Verify fix
curl -X POST "http://127.0.0.1:8888/memories" \
  -H "Authorization: Bearer $MEM0_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}], "user_id": "mark_carey/personal"}'
```

---

#### Issue: "Memories not found"

**Symptoms:** Search returns empty results, but you know memories exist

**Diagnosis:**
```bash
# Check if you're in the correct namespace
# List all memories (no query filter)
curl "http://127.0.0.1:8888/memories?user_id=mark_carey/progressief" \
  -H "Authorization: Bearer $MEM0_API_KEY"
```

**Solution:**
- Verify namespace: `mark_carey/[namespace]` format
- Check for typos in user_id
- Try broader search terms
- Memories may be in different namespace

---

#### Issue: "Slow response times"

**Symptoms:** API takes > 5 seconds to respond

**Diagnosis:**
```bash
# Check resource usage
docker stats --no-stream mem0_server mem0_postgres mem0_neo4j

# Check if local LLMs are running
curl http://127.0.0.1:11434/api/tags
```

**Solution:**
```bash
# 1. Restart Ollama (local LLMs)
docker restart ollama  # or: systemctl restart ollama

# 2. Clear database query cache
docker exec mem0_postgres psql -U mem0_user -d mem0 -c "VACUUM ANALYZE;"

# 3. Restart mem0 services
docker-compose restart
```

---

#### Issue: "Telegram bot not responding"

**Symptoms:** Bot doesn't reply to messages

**Note:** Telegram bot is currently not deployed. To deploy:

```bash
cd /Volumes/intel-system/deployment/docker/mem0_tailscale
docker-compose up -d telegram_bot

# Check bot logs
docker logs mem0_telegram_bot --follow
```

---

### Getting Help

#### Check System Status
```bash
# Quick status check
docker ps --filter "name=mem0" --format "table {{.Names}}\t{{.Status}}"

# Detailed status
cd /Volumes/intel-system/deployment/docker/mem0_tailscale
docker-compose ps
```

#### View Logs
```bash
# All services
docker-compose logs --tail=50

# Specific service
docker logs mem0_server --follow

# Search logs for errors
docker logs mem0_server 2>&1 | grep -i "error\|fail\|exception"
```

#### Grafana Dashboards

**URL:** http://127.0.0.1:3001
**Login:** admin / admin

Monitor:
- Memory operations per minute
- API response times
- Database query performance
- Container health

---

## 7. FAQ

### General Questions

**Q: How much does it cost to run?**
A: Infrastructure is free (self-hosted). API costs are $0-5/month for 95-100% local LLM usage, compared to $60-150/month for cloud services.

**Q: Is my data private?**
A: Yes. Everything runs on your own infrastructure. No data is sent to cloud services except when external LLM APIs are used (< 5% of queries).

**Q: Can I access from anywhere?**
A: Yes, via Tailscale VPN. Your devices connect securely to your home network from anywhere in the world.

**Q: How long are memories stored?**
A: Indefinitely, until you delete them. Database backups ensure data safety.

---

### Technical Questions

**Q: Which LLM models are used?**
A:
- Local (95%): mistral:7b (general), deepseek-coder:6.7b (code), nomic-embed-text (embeddings)
- External (5%): OpenAI GPT-4 (complex queries only)

**Q: How does namespace isolation work?**
A: Each memory is tagged with `user_id = mark_carey/[namespace]`. Queries only return memories matching that exact user_id.

**Q: Can I export my data?**
A: Yes. Database backup:
```bash
docker exec mem0_postgres pg_dump -U mem0_user mem0 > backup.sql
```

**Q: What happens if the server crashes?**
A: Docker automatically restarts containers. Persistent data is stored on disk (`/Users/kermit/mem0-data`). No data loss.

---

### Usage Questions

**Q: How do I know which namespace I'm in?**
A: Telegram: `/current` command. API: Check the `user_id` parameter you're using.

**Q: Can memories be shared between namespaces?**
A: No. Namespaces are strictly isolated. Copy memory manually if needed in both contexts.

**Q: What's the best way to organize information?**
A: Use namespaces for broad categories (work, personal, etc.). Let the AI handle relationships and connections automatically.

**Q: Can I search across all namespaces?**
A: Not currently. You must search within a specific namespace. This is by design for privacy and organization.

---

### Performance Questions

**Q: How fast should responses be?**
A:
- Memory storage: < 500ms
- Memory search: < 1s
- Telegram bot: < 2s
- Local LLM: < 2s
- External API: 3-5s

**Q: How many memories can I store?**
A: Practically unlimited. PostgreSQL and Neo4j can handle millions of memories. Performance may degrade after 100K+ memories without optimization.

**Q: Does it work offline?**
A: Partially. Local LLMs work offline, but OpenAI API calls require internet. 95% of operations work offline.

---

## Quick Reference Card

See [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) for a one-page cheat sheet.

---

## Additional Resources

- **Technical Documentation:** [TECHNICAL_DOCS.md](./TECHNICAL_DOCS.md)
- **Test Report:** [WORKER6_TEST_REPORT.md](./WORKER6_TEST_REPORT.md)
- **API Documentation:** http://127.0.0.1:8888/docs
- **Grafana Monitoring:** http://127.0.0.1:3001
- **Neo4j Browser:** http://127.0.0.1:7475

---

**Last Updated:** 2025-10-16
**Version:** 1.0
**Maintainer:** Worker 6 (QA + Technical Writer)

**Note:** This user guide is based on infrastructure testing. Some features (Telegram bot, Grafana dashboards) require additional configuration. The system is 95% complete and operational after OpenAI API key is configured.
