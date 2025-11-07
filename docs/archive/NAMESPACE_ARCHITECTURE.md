# Namespace Architecture - Multi-Context Memory Isolation

**Created:** 2025-10-16 12:30
**Status:** Design Complete, Implementation Ready
**Purpose:** Enable complete memory isolation between 5 different life contexts

---

## Executive Summary

This document defines the architecture for a multi-namespace memory system that allows Mark Carey to maintain completely isolated memory contexts for different areas of life (business, job search, investments, personal, infrastructure). The system ensures zero memory leakage between namespaces while sharing the same physical infrastructure.

---

## Architecture Decisions

### 1. User ID Format

**Decision:** Composite format `user_id/namespace`

**Rationale:**
- Simple and explicit
- Easy to parse and validate
- Works with existing mem0 string-based user IDs
- No need to modify mem0's core user identification logic

**Format:**
```
{user_id}/{namespace}
```

**Examples:**
```
mark_carey/progressief
mark_carey/cv_automation
mark_carey/investments
mark_carey/personal
mark_carey/intel_system
```

**Alternative Rejected:** Metadata-based approach would require modifying mem0's internal user tracking and add complexity.

### 2. Neo4j Isolation Strategy

**Decision:** Node labeling with namespace property + compound indexes

**Implementation:**
```cypher
// Memory node with namespace
CREATE (m:Memory:Progressief {
  id: 'mem_uuid',
  content: 'Meeting notes...',
  namespace: 'progressief',
  user_id: 'mark_carey',
  created_at: datetime(),
  metadata: {}
})

// Always include namespace in queries
MATCH (m:Memory {namespace: 'progressief', user_id: 'mark_carey'})
RETURN m
```

**Why Node Labeling:**
- Neo4j Community Edition supports only one database (no database-level isolation)
- Dynamic labels enable namespace-specific queries without scanning all nodes
- Label indexing provides O(log n) lookup performance
- Prevents accidental cross-namespace relationships

**Index Strategy:**
```cypher
// Compound index for efficient namespace + user queries
CREATE INDEX mem_namespace_user IF NOT EXISTS
FOR (m:Memory) ON (m.namespace, m.user_id);

// Additional indexes for common queries
CREATE INDEX mem_namespace_timestamp IF NOT EXISTS
FOR (m:Memory) ON (m.namespace, m.created_at);
```

**Constraint Enforcement:**
```cypher
// Prevent memories without namespace
CREATE CONSTRAINT mem_namespace_required IF NOT EXISTS
FOR (m:Memory) REQUIRE m.namespace IS NOT NULL;
```

**Alternative Rejected:** Namespace as relationship would add unnecessary graph complexity and slow down queries (requires traversing relationship before accessing memory).

### 3. PostgreSQL Isolation Strategy

**Decision:** Namespace column + filtered indexes + enforced constraints

**Schema:**
```sql
-- Add namespace column to memories table
ALTER TABLE memories
ADD COLUMN IF NOT EXISTS namespace VARCHAR(50) NOT NULL DEFAULT 'personal';

-- Add composite index for namespace + user queries
CREATE INDEX IF NOT EXISTS idx_memories_namespace_user
ON memories(namespace, user_id);

-- Add index for namespace + timestamp (temporal queries)
CREATE INDEX IF NOT EXISTS idx_memories_namespace_created
ON memories(namespace, created_at DESC);

-- Add constraint to ensure valid namespaces
ALTER TABLE memories
ADD CONSTRAINT chk_valid_namespace
CHECK (namespace IN ('progressief', 'cv_automation', 'investments', 'personal', 'intel_system'));
```

**Vector Search with Namespace:**
```sql
-- Vector similarity search within namespace
SELECT
  id,
  content,
  user_id,
  namespace,
  1 - (embedding <=> $1::vector) as similarity
FROM memories
WHERE user_id = $2
  AND namespace = $3
  AND 1 - (embedding <=> $1::vector) > 0.7
ORDER BY embedding <=> $1::vector
LIMIT 10;
```

**Why Column-Based:**
- Simple to implement and maintain
- Excellent query performance with proper indexing
- Native PostgreSQL support (no extensions needed)
- Easy to add constraints and validation

**Alternative Rejected:** Separate tables per namespace would create schema management overhead and complicate cross-namespace analytics.

### 4. Namespace Definitions

```python
NAMESPACES = {
    'progressief': {
        'description': 'Progressief B.V. consulting business',
        'use_cases': [
            'Client meetings and project notes',
            'Business development activities',
            'Consulting deliverables and proposals',
            'Company administration'
        ],
        'retention': '7 years',  # Business records
        'sensitivity': 'HIGH'
    },
    'cv_automation': {
        'description': 'Job search and CV generation',
        'use_cases': [
            'Job applications and tracking',
            'Interview notes and feedback',
            'CV customization context',
            'Recruiter interactions'
        ],
        'retention': '2 years',
        'sensitivity': 'MEDIUM'
    },
    'investments': {
        'description': 'Investment tracking and analysis',
        'use_cases': [
            'Portfolio decisions and rationale',
            'Market research and analysis',
            'Financial planning notes',
            'Investment thesis development'
        ],
        'retention': '10 years',  # Financial records
        'sensitivity': 'HIGH'
    },
    'personal': {
        'description': 'Personal life, family, health',
        'use_cases': [
            'Family events and planning',
            'Health tracking and medical notes',
            'Personal goals and reflections',
            'Relationship management'
        ],
        'retention': 'indefinite',
        'sensitivity': 'HIGHEST'
    },
    'intel_system': {
        'description': 'Infrastructure and technical projects',
        'use_cases': [
            'System architecture decisions',
            'Technical troubleshooting notes',
            'Infrastructure changes and rationale',
            'Development project context'
        ],
        'retention': '3 years',
        'sensitivity': 'MEDIUM'
    }
}
```

### 5. Memory Isolation Guarantees

**Hard Guarantees:**
1. **Storage Isolation:** Namespace field required in all queries (enforced by application layer)
2. **Search Isolation:** Vector similarity searches filtered by namespace
3. **Graph Isolation:** Neo4j queries always include namespace constraint
4. **Relationship Isolation:** No cross-namespace relationships allowed (enforced by Cypher queries)

**Verification Strategy:**
```python
# Periodic isolation audit
def verify_namespace_isolation():
    """Run daily to ensure no memory leakage"""
    checks = {
        'cross_namespace_relationships': check_neo4j_isolation(),
        'missing_namespace_fields': check_postgres_integrity(),
        'namespace_memory_counts': verify_memory_distribution(),
        'vector_search_isolation': test_search_boundaries()
    }
    return checks
```

### 6. Namespace Switching Mechanism

**Context Manager Approach:**

```python
class NamespaceContext:
    """Thread-safe namespace context manager"""

    _local = threading.local()

    VALID_NAMESPACES = [
        'progressief', 'cv_automation', 'investments',
        'personal', 'intel_system'
    ]

    @classmethod
    def set_namespace(cls, namespace: str):
        """Set current namespace for thread"""
        if namespace not in cls.VALID_NAMESPACES:
            raise ValueError(f"Invalid namespace: {namespace}")
        cls._local.namespace = namespace

    @classmethod
    def get_namespace(cls) -> str:
        """Get current namespace, default to personal"""
        return getattr(cls._local, 'namespace', 'personal')

    @classmethod
    @contextmanager
    def use_namespace(cls, namespace: str):
        """Context manager for temporary namespace switch"""
        previous = cls.get_namespace()
        try:
            cls.set_namespace(namespace)
            yield namespace
        finally:
            cls.set_namespace(previous)
```

**Usage:**
```python
# Explicit namespace
with NamespaceContext.use_namespace('progressief'):
    memory.add("Client meeting scheduled for next week")
    results = memory.search("client meetings")

# API endpoint with namespace header
@app.post("/v1/memories")
async def add_memory(
    request: MemoryRequest,
    x_namespace: str = Header('personal')
):
    with NamespaceContext.use_namespace(x_namespace):
        return memory.add(request.messages, user_id=request.user_id)
```

### 7. API Design

**New Endpoints:**

```
GET    /v1/namespaces                    # List all namespaces
POST   /v1/namespace/switch              # Switch active namespace
GET    /v1/namespace/current             # Get current namespace
GET    /v1/namespace/{name}/stats        # Memory stats per namespace
DELETE /v1/namespace/{name}/memories     # Bulk delete (with confirmation)
```

**Modified Endpoints (add X-Namespace header):**

```
POST   /v1/memories                      # Add memory (namespace from header)
GET    /v1/memories                      # List memories (namespace filtered)
PATCH  /v1/memories/{id}                 # Update memory (namespace validated)
DELETE /v1/memories/{id}                 # Delete memory (namespace validated)
POST   /v1/memories/search               # Search memories (namespace scoped)
```

**Header-Based Namespace:**
```http
POST /v1/memories HTTP/1.1
Host: localhost:8888
Content-Type: application/json
X-Namespace: progressief
X-API-Key: mem0_api_key

{
  "messages": [{"role": "user", "content": "Meeting with Synovia Digital"}],
  "user_id": "mark_carey"
}
```

### 8. Performance Considerations

**Query Performance:**
- Namespace filtering adds ~10-20ms overhead (acceptable)
- Compound indexes on (namespace, user_id) provide O(log n) lookups
- PostgreSQL partial indexes can optimize hot namespaces

**Storage Overhead:**
- Namespace column: 50 bytes per memory
- Index overhead: ~15% storage increase
- Negligible for <1M memories

**Optimization Strategies:**
```sql
-- Partial index for most active namespace
CREATE INDEX idx_progressief_hot
ON memories(user_id, created_at DESC)
WHERE namespace = 'progressief';

-- Partition table by namespace (if >1M memories)
CREATE TABLE memories_progressief
PARTITION OF memories
FOR VALUES IN ('progressief');
```

### 9. Migration Strategy

**Phase 1: Schema Updates**
1. Add namespace column to PostgreSQL (default 'personal')
2. Add Neo4j namespace property and indexes
3. Backfill existing memories with 'personal' namespace

**Phase 2: Application Layer**
1. Deploy namespace context manager
2. Update all queries to include namespace filtering
3. Add namespace validation middleware

**Phase 3: API Updates**
1. Add new namespace endpoints
2. Add X-Namespace header support
3. Update API documentation

**Phase 4: Validation**
1. Run isolation tests
2. Verify performance impact
3. Monitor for errors

**Rollback Plan:**
- Namespace column is nullable (can be removed)
- Keep old API endpoints active during transition
- Feature flag for namespace enforcement

### 10. Security & Privacy

**Access Control:**
```python
# Only owner can access namespace
def verify_namespace_access(user_id: str, namespace: str) -> bool:
    """Ensure user owns namespace"""
    base_user = user_id.split('/')[0]
    return base_user in NAMESPACE_OWNERS.get(namespace, [])
```

**Audit Logging:**
```python
# Log all namespace switches and cross-namespace attempts
logger.info(
    "namespace_access",
    user_id=user_id,
    namespace=namespace,
    action=action,
    timestamp=datetime.utcnow(),
    ip_address=request.client.host
)
```

**Data Retention:**
```python
# Automated cleanup based on namespace retention policy
async def cleanup_expired_memories():
    for namespace, config in NAMESPACES.items():
        if config['retention'] != 'indefinite':
            cutoff = datetime.utcnow() - timedelta(days=365 * config['retention_years'])
            await delete_memories_older_than(namespace, cutoff)
```

---

## Implementation Checklist

- [ ] PostgreSQL schema updates (namespace column, indexes, constraints)
- [ ] Neo4j schema updates (namespace property, labels, indexes)
- [ ] Namespace context manager implementation
- [ ] Update all database queries to include namespace filtering
- [ ] API endpoint additions (namespace CRUD)
- [ ] API endpoint modifications (X-Namespace header)
- [ ] Isolation verification tests
- [ ] Performance benchmarking
- [ ] Documentation (API docs, user guide)
- [ ] Migration scripts for existing data

---

## Success Criteria

✅ **Isolation:** Zero cross-namespace memory leakage (verified by audit queries)
✅ **Performance:** Namespace filtering adds <50ms query overhead
✅ **Usability:** Simple namespace switching via header or API
✅ **Reliability:** All tests pass, no regressions
✅ **Documentation:** Complete API docs and user guide

---

## References

- Neo4j Community Edition Documentation: https://neo4j.com/docs/
- PostgreSQL Indexing Best Practices: https://www.postgresql.org/docs/current/indexes.html
- pgvector Extension: https://github.com/pgvector/pgvector
- mem0 Repository: https://github.com/mem0ai/mem0

---

**Next Steps:**
1. Implement PostgreSQL schema updates
2. Implement Neo4j schema updates
3. Create namespace manager Python module
4. Update mem0 API handlers
5. Run isolation tests
6. Create user guide
