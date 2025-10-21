// Neo4j Namespace Isolation Setup
// Location: /Volumes/intel-system/deployment/docker/mem0_tailscale/neo4j_namespace_setup.cypher
// Purpose: Configure Neo4j for namespace-based memory isolation
// Scope: Creates indexes, constraints, and namespace labels for 5 life contexts

// ================================================================================
// STEP 1: Create Namespace Labels
// ================================================================================
// Note: Labels are created automatically when first used in CREATE statements
// But we'll verify they exist after creating sample data

// ================================================================================
// STEP 2: Create Constraints
// ================================================================================

// Ensure all Memory nodes have a namespace property
CREATE CONSTRAINT mem_namespace_required IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.namespace IS NOT NULL;

// Ensure all Memory nodes have a user_id property
CREATE CONSTRAINT mem_user_id_required IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.user_id IS NOT NULL;

// Ensure memory IDs are unique
CREATE CONSTRAINT mem_id_unique IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.id IS UNIQUE;

// ================================================================================
// STEP 3: Create Indexes for Performance
// ================================================================================

// Compound index for namespace + user_id (most common query pattern)
CREATE INDEX mem_namespace_user IF NOT EXISTS
FOR (m:Memory)
ON (m.namespace, m.user_id);

// Index for namespace + timestamp (temporal queries)
CREATE INDEX mem_namespace_timestamp IF NOT EXISTS
FOR (m:Memory)
ON (m.namespace, m.created_at);

// Index for user_id only (fallback queries)
CREATE INDEX mem_user_only IF NOT EXISTS
FOR (m:Memory)
ON (m.user_id);

// Full-text index for content search within namespace
CREATE FULLTEXT INDEX mem_content_search IF NOT EXISTS
FOR (m:Memory)
ON EACH [m.content];

// ================================================================================
// STEP 4: Verify Valid Namespaces
// ================================================================================
// Note: Neo4j doesn't have CHECK constraints, so this will be enforced at application layer
// Valid namespaces: progressief, cv_automation, investments, personal, intel_system

// ================================================================================
// STEP 5: Sample Query Patterns
// ================================================================================

// Query memories in a specific namespace
// MATCH (m:Memory {namespace: 'progressief', user_id: 'mark_carey'})
// RETURN m
// ORDER BY m.created_at DESC
// LIMIT 10;

// Count memories per namespace
// MATCH (m:Memory)
// RETURN m.namespace, COUNT(m) as memory_count
// ORDER BY memory_count DESC;

// Verify no cross-namespace relationships (isolation test)
// MATCH (m1:Memory)-[r]-(m2:Memory)
// WHERE m1.namespace <> m2.namespace
// RETURN m1.namespace, m2.namespace, type(r), COUNT(*) as violations;
// Expected result: 0 rows (no violations)

// Search within namespace
// MATCH (m:Memory {namespace: 'cv_automation', user_id: 'mark_carey'})
// WHERE m.content CONTAINS 'interview'
// RETURN m.content, m.created_at
// ORDER BY m.created_at DESC;

// ================================================================================
// STEP 6: Cleanup (if needed for fresh start)
// ================================================================================

// Drop all constraints (CAUTION: Only for development/testing)
// DROP CONSTRAINT mem_namespace_required IF EXISTS;
// DROP CONSTRAINT mem_user_id_required IF EXISTS;
// DROP CONSTRAINT mem_id_unique IF EXISTS;

// Drop all indexes (CAUTION: Only for development/testing)
// DROP INDEX mem_namespace_user IF EXISTS;
// DROP INDEX mem_namespace_timestamp IF EXISTS;
// DROP INDEX mem_user_only IF EXISTS;
// DROP INDEX mem_content_search IF EXISTS;

// Delete all memories (CAUTION: Only for development/testing)
// MATCH (m:Memory) DETACH DELETE m;

// ================================================================================
// STEP 7: Migration for Existing Data (if any)
// ================================================================================

// Add 'personal' namespace to any existing memories without namespace
// MATCH (m:Memory)
// WHERE m.namespace IS NULL
// SET m.namespace = 'personal';

// Verify migration
// MATCH (m:Memory)
// WHERE m.namespace IS NULL
// RETURN COUNT(m) as memories_without_namespace;
// Expected result: 0

// ================================================================================
// STEP 8: Namespace Statistics
// ================================================================================

// Get comprehensive namespace stats
// MATCH (m:Memory)
// WITH m.namespace as namespace, COUNT(m) as count,
//      MIN(m.created_at) as oldest,
//      MAX(m.created_at) as newest
// RETURN namespace, count, oldest, newest
// ORDER BY count DESC;

// ================================================================================
// EXECUTION INSTRUCTIONS
// ================================================================================
//
// Method 1: Via Cypher-Shell (Recommended for automation)
// docker exec -i mem0_neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD < neo4j_namespace_setup.cypher
//
// Method 2: Via Neo4j Browser
// 1. Open http://localhost:7474
// 2. Login with credentials from .env
// 3. Copy/paste commands section by section
// 4. Execute each section separately
//
// Method 3: Via Python Script
// from neo4j import GraphDatabase
// driver = GraphDatabase.driver(uri, auth=(user, password))
// with driver.session() as session:
//     with open('neo4j_namespace_setup.cypher') as f:
//         for statement in f.read().split(';\n'):
//             if statement.strip():
//                 session.run(statement)
//
// ================================================================================
