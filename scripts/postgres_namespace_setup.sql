-- PostgreSQL Namespace Isolation Setup
-- Location: /Volumes/intel-system/deployment/docker/mem0_tailscale/postgres_namespace_setup.sql
-- Purpose: Configure PostgreSQL for namespace-based memory isolation
-- Scope: Adds namespace column, indexes, and constraints to memories table

-- ================================================================================
-- STEP 1: Add Namespace Column
-- ================================================================================

-- Add namespace column with default value 'personal' for existing rows
ALTER TABLE memories
ADD COLUMN IF NOT EXISTS namespace VARCHAR(50) NOT NULL DEFAULT 'personal';

-- Add comment to explain the column
COMMENT ON COLUMN memories.namespace IS
'Memory namespace for context isolation: progressief, cv_automation, investments, personal, intel_system';

-- ================================================================================
-- STEP 2: Add Constraints
-- ================================================================================

-- Ensure only valid namespaces are used
ALTER TABLE memories
DROP CONSTRAINT IF EXISTS chk_valid_namespace;

ALTER TABLE memories
ADD CONSTRAINT chk_valid_namespace
CHECK (namespace IN ('progressief', 'cv_automation', 'investments', 'personal', 'intel_system'));

-- ================================================================================
-- STEP 3: Create Indexes for Performance
-- ================================================================================

-- Compound index for namespace + user_id (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_memories_namespace_user
ON memories(namespace, user_id);

-- Index for namespace + created_at (temporal queries within namespace)
CREATE INDEX IF NOT EXISTS idx_memories_namespace_created
ON memories(namespace, created_at DESC);

-- Index for namespace alone (namespace-wide operations)
CREATE INDEX IF NOT EXISTS idx_memories_namespace
ON memories(namespace);

-- Partial index for most active namespace (performance optimization)
-- Uncomment if 'progressief' becomes the hottest namespace
-- CREATE INDEX IF NOT EXISTS idx_progressief_hot
-- ON memories(user_id, created_at DESC)
-- WHERE namespace = 'progressief';

-- ================================================================================
-- STEP 4: Vector Search with Namespace Support
-- ================================================================================

-- Verify pgvector extension is installed
CREATE EXTENSION IF NOT EXISTS vector;

-- Add index for vector similarity search within namespace
-- Note: This requires the embedding column to exist
-- CREATE INDEX IF NOT EXISTS idx_memories_namespace_embedding
-- ON memories USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100)
-- WHERE namespace IS NOT NULL;

-- ================================================================================
-- STEP 5: Create Namespace Statistics View
-- ================================================================================

CREATE OR REPLACE VIEW namespace_stats AS
SELECT
    namespace,
    COUNT(*) as memory_count,
    COUNT(DISTINCT user_id) as user_count,
    MIN(created_at) as oldest_memory,
    MAX(created_at) as newest_memory,
    AVG(LENGTH(content)) as avg_content_length,
    SUM(LENGTH(content)) as total_content_size
FROM memories
GROUP BY namespace
ORDER BY memory_count DESC;

COMMENT ON VIEW namespace_stats IS
'Statistics for each namespace: memory counts, date ranges, and storage usage';

-- ================================================================================
-- STEP 6: Create Namespace Isolation Verification Function
-- ================================================================================

CREATE OR REPLACE FUNCTION verify_namespace_isolation()
RETURNS TABLE(
    namespace VARCHAR(50),
    memory_count BIGINT,
    users TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.namespace,
        COUNT(*)::BIGINT as memory_count,
        ARRAY_AGG(DISTINCT m.user_id) as users
    FROM memories m
    GROUP BY m.namespace
    ORDER BY m.namespace;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION verify_namespace_isolation() IS
'Verify namespace isolation by showing memory distribution across namespaces';

-- ================================================================================
-- STEP 7: Sample Query Patterns
-- ================================================================================

-- Query memories in a specific namespace
-- SELECT id, content, user_id, created_at
-- FROM memories
-- WHERE namespace = 'progressief'
--   AND user_id = 'mark_carey'
-- ORDER BY created_at DESC
-- LIMIT 10;

-- Count memories per namespace
-- SELECT namespace, COUNT(*) as memory_count
-- FROM memories
-- GROUP BY namespace
-- ORDER BY memory_count DESC;

-- Vector similarity search within namespace
-- SELECT
--     id,
--     content,
--     user_id,
--     namespace,
--     1 - (embedding <=> $1::vector) as similarity
-- FROM memories
-- WHERE user_id = $2
--   AND namespace = $3
--   AND 1 - (embedding <=> $1::vector) > 0.7
-- ORDER BY embedding <=> $1::vector
-- LIMIT 10;

-- Find memories without proper namespace (should be 0)
-- SELECT COUNT(*)
-- FROM memories
-- WHERE namespace IS NULL OR namespace = '';

-- ================================================================================
-- STEP 8: Migration for Existing Data
-- ================================================================================

-- Update any NULL namespaces to 'personal' (safety check)
UPDATE memories
SET namespace = 'personal'
WHERE namespace IS NULL OR namespace = '';

-- Verify migration
-- SELECT COUNT(*) as memories_without_valid_namespace
-- FROM memories
-- WHERE namespace NOT IN ('progressief', 'cv_automation', 'investments', 'personal', 'intel_system');

-- ================================================================================
-- STEP 9: Performance Analysis Queries
-- ================================================================================

-- Analyze query performance with namespace filtering
-- EXPLAIN ANALYZE
-- SELECT * FROM memories
-- WHERE namespace = 'progressief'
--   AND user_id = 'mark_carey'
-- ORDER BY created_at DESC
-- LIMIT 10;

-- Check index usage
-- SELECT
--     schemaname,
--     tablename,
--     indexname,
--     idx_scan,
--     idx_tup_read,
--     idx_tup_fetch
-- FROM pg_stat_user_indexes
-- WHERE tablename = 'memories'
-- ORDER BY idx_scan DESC;

-- ================================================================================
-- STEP 10: Cleanup (for testing/development only)
-- ================================================================================

-- Drop namespace constraints and indexes (CAUTION)
-- DROP INDEX IF EXISTS idx_memories_namespace_user;
-- DROP INDEX IF EXISTS idx_memories_namespace_created;
-- DROP INDEX IF EXISTS idx_memories_namespace;
-- ALTER TABLE memories DROP CONSTRAINT IF EXISTS chk_valid_namespace;
-- ALTER TABLE memories DROP COLUMN IF EXISTS namespace;
-- DROP VIEW IF EXISTS namespace_stats;
-- DROP FUNCTION IF EXISTS verify_namespace_isolation();

-- ================================================================================
-- EXECUTION INSTRUCTIONS
-- ================================================================================
--
-- Method 1: Via psql (Recommended for automation)
-- docker exec -i mem0_postgres psql -U mem0_user -d mem0 < postgres_namespace_setup.sql
--
-- Method 2: Via psql interactive
-- docker exec -it mem0_postgres psql -U mem0_user -d mem0
-- Then paste the SQL commands
--
-- Method 3: Via Python Script
-- import psycopg2
-- conn = psycopg2.connect(...)
-- with conn.cursor() as cur:
--     with open('postgres_namespace_setup.sql') as f:
--         cur.execute(f.read())
-- conn.commit()
--
-- ================================================================================

-- Verify setup was successful
SELECT
    'Namespace column exists' as check,
    COUNT(*) > 0 as passed
FROM information_schema.columns
WHERE table_name = 'memories'
  AND column_name = 'namespace'

UNION ALL

SELECT
    'Valid namespace constraint exists' as check,
    COUNT(*) > 0 as passed
FROM information_schema.constraint_column_usage
WHERE table_name = 'memories'
  AND constraint_name = 'chk_valid_namespace'

UNION ALL

SELECT
    'Namespace indexes exist' as check,
    COUNT(*) >= 3 as passed
FROM pg_indexes
WHERE tablename = 'memories'
  AND indexname LIKE 'idx_memories_namespace%';

-- Show namespace statistics
SELECT * FROM namespace_stats;

-- Show isolation verification
SELECT * FROM verify_namespace_isolation();
