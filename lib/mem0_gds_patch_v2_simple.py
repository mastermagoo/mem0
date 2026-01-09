#!/usr/bin/env python3
"""
mem0 GDS Patch v2 - Simplified Neo4j Community Edition Compatibility
Created: 2025-10-16
Purpose: Patch Neo4jGraph.query() to replace Enterprise vector functions with GDS equivalents

Replaces:
- vector.similarity.cosine() → gds.similarity.cosine()
- vector.similarity.euclidean() → gds.similarity.euclidean()
"""

import sys


def patch_neo4j_graph():
    """Simple patch at the Neo4jGraph query execution level"""
    print("🔧 Applying mem0 Neo4j GDS patch v2...")

    try:
        # Import Neo4jGraph
        from mem0.memory.graph_memory import Neo4jGraph

        # Store original query method
        original_query = Neo4jGraph.query

        # Create patched query method
        def patched_query(self, cypher: str, params=None):
            """Patch Cypher queries before execution"""
            if isinstance(cypher, str):
                # Replace Enterprise vector functions with GDS equivalents
                cypher = cypher.replace("vector.similarity.cosine", "gds.similarity.cosine")
                cypher = cypher.replace("vector.similarity.euclidean", "gds.similarity.euclidean")

            # Call original method with patched query
            return original_query(self, cypher, params)

        # Apply patch
        Neo4jGraph.query = patched_query

        print("✅ Neo4jGraph.query() patched successfully")
        print("   - vector.similarity.cosine → gds.similarity.cosine")
        print("   - vector.similarity.euclidean → gds.similarity.euclidean")

        return True

    except ImportError as e:
        print(f"⚠️  Could not import Neo4jGraph: {e}")
        return False
    except Exception as e:
        print(f"❌ Error applying patch: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Apply patch immediately
    success = patch_neo4j_graph()
    sys.exit(0 if success else 1)

