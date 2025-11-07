# Namespace User Guide

**Created:** 2025-10-16
**Status:** Complete
**For:** Mark Carey - Personal Memory Management

---

## What Are Namespaces?

Namespaces are isolated memory contexts that keep different areas of your life completely separate. Think of them as "rooms" in your memory house - what happens in one room stays in that room.

**Why Use Namespaces?**
- **Context Switching:** Easily switch between work, personal, and other contexts
- **Privacy:** Keep business notes separate from personal thoughts
- **Organization:** Find memories faster by limiting search scope
- **Clarity:** Avoid context confusion when recalling information

---

## Your 5 Namespaces

### 1. `progressief` - Business Consulting

**Purpose:** Progressief B.V. consulting work

**Use For:**
- Client meetings and project notes
- Business development activities
- Consulting deliverables and proposals
- Company administration

**Examples:**
- "Meeting with Synovia Digital about SAP implementation"
- "Proposal draft for data platform modernization"
- "Invoice sent to client X for Q3 2025"

**Retention:** 7 years (business records)
**Sensitivity:** HIGH

---

### 2. `cv_automation` - Job Search

**Purpose:** Job search and application tracking

**Use For:**
- Job applications and tracking
- Interview notes and feedback
- CV customization context
- Recruiter interactions

**Examples:**
- "Applied to Booking.com Data Engineer position on Oct 15"
- "Interview with Ashish Tiwari went well, mentioned SAP expertise"
- "Need to follow up on Walter Kidde application next week"

**Retention:** 2 years
**Sensitivity:** MEDIUM

---

### 3. `investments` - Financial Tracking

**Purpose:** Investment decisions and analysis

**Use For:**
- Portfolio decisions and rationale
- Market research and analysis
- Financial planning notes
- Investment thesis development

**Examples:**
- "Researching NVIDIA fundamentals - strong AI/datacenter growth"
- "Sold 50 shares of XYZ at €150 based on valuation concerns"
- "2025 Q4 portfolio rebalancing: increase tech allocation to 30%"

**Retention:** 10 years (financial records)
**Sensitivity:** HIGH

---

### 4. `personal` - Personal Life

**Purpose:** Family, health, and personal matters

**Use For:**
- Family events and planning
- Health tracking and medical notes
- Personal goals and reflections
- Relationship management

**Examples:**
- "Dad's birthday is next month - plan surprise dinner"
- "Started new fitness routine - track progress weekly"
- "Reflect on 2025 goals: achieved X, still working on Y"

**Retention:** Indefinite
**Sensitivity:** HIGHEST

---

### 5. `intel_system` - Technical Projects

**Purpose:** Infrastructure and development work

**Use For:**
- System architecture decisions
- Technical troubleshooting notes
- Infrastructure changes and rationale
- Development project context

**Examples:**
- "Deployed mem0 namespace isolation feature on Oct 16"
- "PostgreSQL upgrade to version 17 completed successfully"
- "Resolved Redis connection issue by updating network configuration"

**Retention:** 3 years
**Sensitivity:** MEDIUM

---

## How to Use Namespaces

### Method 1: Telegram Bot (Easiest)

The Telegram bot automatically manages namespaces for you.

**Commands:**
```
/namespace                  # Show current namespace
/namespace list             # List all namespaces
/namespace switch <name>    # Switch to different namespace
/remember <text>            # Store in current namespace
/recall <query>             # Search in current namespace
```

**Example Session:**
```
You: /namespace
Bot: Current namespace: personal

You: /namespace switch progressief
Bot: Switched to progressief

You: /remember Meeting with Synovia went well
Bot: Memory stored in progressief namespace

You: /namespace switch cv_automation
Bot: Switched to cv_automation

You: /recall interview notes
Bot: [Shows only cv_automation memories about interviews]
```

---

### Method 2: API (Advanced)

Use the REST API directly for programmatic access.

**List Namespaces:**
```bash
curl http://localhost:8888/v1/namespace/list
```

**Response:**
```json
{
  "namespaces": ["progressief", "cv_automation", "investments", "personal", "intel_system"],
  "current": "personal",
  "count": 5
}
```

**Switch Namespace:**
```bash
curl -X POST http://localhost:8888/v1/namespace/switch \
  -H "Content-Type: application/json" \
  -d '{"namespace": "progressief"}'
```

**Add Memory with Namespace Header:**
```bash
curl -X POST http://localhost:8888/v1/memories \
  -H "Content-Type: application/json" \
  -H "X-Namespace: progressief" \
  -d '{
    "messages": [{"role": "user", "content": "Client meeting scheduled"}],
    "user_id": "mark_carey/progressief"
  }'
```

**Search in Namespace:**
```bash
curl "http://localhost:8888/v1/memories?user_id=mark_carey/progressief" \
  -H "X-Namespace: progressief"
```

**Get Namespace Statistics:**
```bash
curl http://localhost:8888/v1/namespace/progressief/stats
```

**Response:**
```json
{
  "namespace": "progressief",
  "memory_count": 47,
  "storage_bytes": 15234,
  "oldest_memory": "2025-01-15T10:30:00Z",
  "newest_memory": "2025-10-16T12:45:00Z",
  "activity_7d": 12
}
```

---

### Method 3: Python Script

Use the namespace manager in your Python scripts.

```python
from namespace_manager import NamespaceContext

# Get current namespace
current = NamespaceContext.get_namespace()
print(f"Current: {current}")

# Switch namespace
NamespaceContext.set_namespace('progressief')

# Use context manager for temporary switch
with NamespaceContext.use_namespace('cv_automation'):
    # All operations here use cv_automation namespace
    memory.add("Applied to new job")
    results = memory.search("applications")

# Back to previous namespace after context
```

---

## Best Practices

### 1. Default to Personal
When in doubt, use `personal` namespace. It's the default and has indefinite retention.

### 2. Switch Before Adding
Always switch to the correct namespace BEFORE storing memories. Double-check your context.

### 3. Use Descriptive Content
Add enough context to memories so they're useful later:
- ❌ Bad: "Meeting went well"
- ✅ Good: "Meeting with John at Synovia about SAP project went well - they're interested in Q1 2026 start"

### 4. Review Regularly
Check namespace stats weekly to see where memories are accumulating:
```bash
for ns in progressief cv_automation investments personal intel_system; do
  curl http://localhost:8888/v1/namespace/$ns/stats
done
```

### 5. Respect Retention Policies
Namespaces have different retention periods:
- Business records: 7-10 years
- Job search: 2 years
- Personal: Indefinite
- Technical: 3 years

Memories outside retention period will be automatically cleaned up.

---

## Common Workflows

### Morning Routine - Check Business Context
```bash
# Switch to business namespace
/namespace switch progressief

# Review recent memories
/recall last week

# Add today's priorities
/remember Today's priorities: finish proposal for Client X, call recruiter about SAP role
```

### Job Application - Track Progress
```bash
# Switch to job search namespace
/namespace switch cv_automation

# Record application
/remember Applied to Booking.com Senior Data Engineer position via LinkedIn. Role focuses on real-time data pipelines and Kafka. Mentioned Progressief B.V. and AkzoNobel experience.

# Search past applications
/recall Booking.com applications
```

### Investment Research - Document Thesis
```bash
# Switch to investments namespace
/namespace switch investments

# Record research
/remember NVIDIA Q3 2025 analysis: Strong datacenter revenue growth (+40% YoY), AI chip demand robust, valuation reasonable at 30x forward P/E given growth profile. Considering position increase.

# Review past decisions
/recall NVIDIA thesis
```

### Personal Reflection - End of Day
```bash
# Switch to personal namespace
/namespace switch personal

# Record daily reflection
/remember Productive day - made progress on job search, good workout, quality time with family. Feeling optimistic about upcoming opportunities.

# Review goals
/recall 2025 goals
```

### Technical Work - Document Decisions
```bash
# Switch to infrastructure namespace
/namespace switch intel_system

# Record architecture decision
/remember Deployed mem0 namespace isolation using PostgreSQL namespaces and Neo4j node labels. Chose composite user_id format (user/namespace) for simplicity. All tests passing, zero memory leakage verified.

# Search past decisions
/recall architecture decisions
```

---

## Troubleshooting

### Wrong Namespace Selected

**Problem:** Stored memory in wrong namespace
**Solution:**
1. Use `/namespace` to check current namespace
2. Switch to correct namespace: `/namespace switch <correct_name>`
3. Re-add the memory
4. Delete incorrect memory (if you remember its ID)

### Can't Find Memory

**Problem:** Memory seems to be missing
**Solution:**
1. Check which namespace you're in: `/namespace`
2. Switch to the namespace where you stored it
3. Try searching again

**Example:**
```
You: /recall client meeting
Bot: No memories found

You: /namespace
Bot: Current namespace: personal

You: /namespace switch progressief
Bot: Switched to progressief

You: /recall client meeting
Bot: Found 3 memories about client meetings...
```

### Namespace Confusion

**Problem:** Unsure which namespace to use
**Solution:** Use this decision tree:

1. **Is it about Progressief B.V. client work?** → `progressief`
2. **Is it about job search or applications?** → `cv_automation`
3. **Is it about investments or finances?** → `investments`
4. **Is it about infrastructure/technical projects?** → `intel_system`
5. **Everything else** → `personal`

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/namespace/list` | List all namespaces |
| GET | `/v1/namespace/current` | Get current namespace |
| POST | `/v1/namespace/switch` | Switch namespace |
| GET | `/v1/namespace/{name}/info` | Get namespace details |
| GET | `/v1/namespace/{name}/stats` | Get namespace statistics |
| GET | `/v1/namespace/access-log` | View access log |
| POST | `/v1/namespace/validate-user-id` | Validate user_id format |
| DELETE | `/v1/namespace/{name}/memories` | Delete all memories (DANGEROUS) |

### Headers

| Header | Description | Example |
|--------|-------------|---------|
| `X-Namespace` | Namespace for operation | `X-Namespace: progressief` |
| `Authorization` | API key | `Authorization: Bearer <api_key>` |

---

## Security & Privacy

### Access Control
- Currently single-user system (Mark Carey)
- All namespaces accessible by owner
- Future: Multi-user with access control per namespace

### Data Retention
- Each namespace has defined retention policy
- Automatic cleanup based on retention period
- Personal namespace: indefinite retention
- Business/financial: 7-10 years per legal requirements

### Audit Logging
- All namespace switches are logged
- Access log available via API
- Review with: `GET /v1/namespace/access-log`

### Backup
- All namespaces backed up together
- Restore preserves namespace isolation
- Test isolation after restore

---

## Technical Details

### User ID Format
```
{base_user}/{namespace}
```

**Examples:**
- `mark_carey/progressief`
- `mark_carey/cv_automation`
- `mark_carey/personal`

### Database Schema

**PostgreSQL:**
- `namespace` column on memories table
- Indexes: `(namespace, user_id)`, `(namespace, created_at)`
- Constraint: Only valid namespaces allowed

**Neo4j:**
- Namespace property on Memory nodes
- Namespace-specific labels (`:Progressief`, `:Personal`, etc.)
- Indexes on namespace for fast queries

### Performance
- Namespace filtering adds ~10-20ms to queries
- Compound indexes optimize common patterns
- Vector search respects namespace boundaries

---

## Examples

### Complete API Workflow

```bash
# 1. Check current namespace
curl http://localhost:8888/v1/namespace/current

# 2. List all namespaces
curl http://localhost:8888/v1/namespace/list

# 3. Get namespace details
curl http://localhost:8888/v1/namespace/progressief/info

# 4. Switch namespace
curl -X POST http://localhost:8888/v1/namespace/switch \
  -H "Content-Type: application/json" \
  -d '{"namespace": "progressief"}'

# 5. Add memory in namespace
curl -X POST http://localhost:8888/v1/memories \
  -H "Content-Type: application/json" \
  -H "X-Namespace: progressief" \
  -d '{
    "messages": [{"role": "user", "content": "Client deliverable completed"}],
    "user_id": "mark_carey/progressief"
  }'

# 6. Search in namespace
curl "http://localhost:8888/v1/memories?user_id=mark_carey/progressief" \
  -H "X-Namespace: progressief"

# 7. Get statistics
curl http://localhost:8888/v1/namespace/progressief/stats

# 8. View access log
curl "http://localhost:8888/v1/namespace/access-log?limit=10"
```

### Complete Python Workflow

```python
from namespace_manager import NamespaceContext
from mem0 import Memory

# Initialize memory client
memory = Memory()

# Work in progressief namespace
with NamespaceContext.use_namespace('progressief'):
    # Format user ID for namespace
    user_id = NamespaceContext.format_user_id('mark_carey')
    # user_id is now 'mark_carey/progressief'

    # Add memory
    memory.add(
        "Completed Q3 deliverables for Client X",
        user_id=user_id
    )

    # Search memories
    results = memory.search(
        "client deliverables",
        user_id=user_id
    )

    print(f"Found {len(results)} memories in progressief")

# Switch to cv_automation
with NamespaceContext.use_namespace('cv_automation'):
    user_id = NamespaceContext.format_user_id('mark_carey')
    # user_id is now 'mark_carey/cv_automation'

    # Add memory
    memory.add(
        "Interview scheduled with Booking.com for next week",
        user_id=user_id
    )

    # Search memories
    results = memory.search(
        "interviews",
        user_id=user_id
    )

    print(f"Found {len(results)} memories in cv_automation")
```

---

## FAQ

**Q: Can I move a memory from one namespace to another?**
A: Not directly. You need to:
1. Read memory from source namespace
2. Switch to target namespace
3. Add memory to target namespace
4. Delete from source namespace

**Q: What happens if I forget which namespace I'm in?**
A: Use `/namespace` (Telegram) or `GET /v1/namespace/current` (API) to check.

**Q: Can I search across multiple namespaces?**
A: Not currently. Each search is scoped to a single namespace for isolation. Future versions may support cross-namespace search with explicit permission.

**Q: What if I add a memory to the wrong namespace?**
A: Switch to the correct namespace and re-add. Delete the incorrect one if needed.

**Q: How do I see which namespace has the most memories?**
A: Use namespace statistics:
```bash
curl http://localhost:8888/v1/namespace/progressief/stats
```

**Q: Can I delete all memories in a namespace?**
A: Yes, but requires confirmation:
```bash
curl -X DELETE "http://localhost:8888/v1/namespace/progressief/memories?confirm=true"
```
**WARNING:** This is permanent and cannot be undone!

**Q: How do I export memories from a specific namespace?**
A: Query all memories in namespace and save to file:
```bash
curl "http://localhost:8888/v1/memories?user_id=mark_carey/progressief" \
  -H "X-Namespace: progressief" \
  > progressief_memories.json
```

---

## Support

**Documentation:**
- Architecture: `NAMESPACE_ARCHITECTURE.md`
- Implementation: Source code in `/Volumes/intel-system/deployment/docker/mem0_tailscale/`

**Testing:**
- Isolation tests: `python test_namespace_isolation.py`
- Manual verification: See "Troubleshooting" section

**Issues:**
- Check logs: `docker logs mem0_server`
- Verify database: `docker exec -it mem0_postgres psql -U mem0_user -d mem0`
- Check Neo4j: http://localhost:7474

---

**Last Updated:** 2025-10-16
**Version:** 1.0
**Status:** Production Ready
