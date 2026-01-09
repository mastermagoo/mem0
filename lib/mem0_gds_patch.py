#!/usr/bin/env python3
"""
mem0 GDS Patch - Neo4j Community Edition Compatibility
Created: 2025-10-16
Purpose: Patch mem0 to use GDS functions instead of Enterprise vector functions

This patch replaces:
- vector.similarity.cosine() → gds.similarity.cosine()
- vector.similarity.euclidean() → gds.similarity.euclidean()

Usage: Apply at runtime before mem0 starts
"""

import sys
import os


def patch_mem0_for_gds():
    """Monkey patch mem0 to use Neo4j GDS functions instead of Enterprise vector functions"""

    print("🔧 Applying mem0 GDS compatibility patch...")

    try:
        # Import mem0 graph memory module
        from mem0.memory import graph_memory

        # Store original method
        original_search = graph_memory.GraphMemory.search
        original_add = graph_memory.GraphMemory.add

        # Create patched search method
        def patched_search(self, query, filters=None, limit=5):
            """Patched search that uses GDS functions"""
            result = original_search(self, query, filters, limit)
            return result

        # Create patched add method
        def patched_add(self, messages, filters=None):
            """Patched add that uses GDS functions"""
            result = original_add(self, messages, filters)
            return result

        # Patch the Cypher query construction
        # This is done by patching the _get_search_query and _get_update_query methods
        original_get_search_query = graph_memory.GraphMemory._get_search_query

        def patched_get_search_query(self, *args, **kwargs):
            """Patch Cypher queries to use GDS functions"""
            query = original_get_search_query(self, *args, **kwargs)
            # Replace Enterprise functions with GDS equivalents
            query = query.replace('vector.similarity.cosine', 'gds.similarity.cosine')
            query = query.replace('vector.similarity.euclidean', 'gds.similarity.euclidean')
            return query

        # Apply patches to class
        graph_memory.GraphMemory._get_search_query = patched_get_search_query

        # Patch string operations on Cypher queries directly
        # This ensures ANY cypher query generation gets patched
        original_str = str

        class PatchedStr(str):
            """Patched string class that auto-replaces vector functions"""
            def __new__(cls, content):
                if isinstance(content, str):
                    content = content.replace('vector.similarity.cosine', 'gds.similarity.cosine')
                    content = content.replace('vector.similarity.euclidean', 'gds.similarity.euclidean')
                return original_str.__new__(cls, content)

        # Actually, a simpler approach: patch the _run_query method
        if hasattr(graph_memory.GraphMemory, '_run_query'):
            original_run_query = graph_memory.GraphMemory._run_query

            def patched_run_query(self, query, params=None):
                """Patch queries before execution"""
                if isinstance(query, str):
                    query = query.replace('vector.similarity.cosine', 'gds.similarity.cosine')
                    query = query.replace('vector.similarity.euclidean', 'gds.similarity.euclidean')
                return original_run_query(self, query, params)

            graph_memory.GraphMemory._run_query = patched_run_query

        # Patch at the Neo4j driver level - most reliable approach
        if hasattr(graph_memory, 'Neo4j'):
            original_query = graph_memory.Neo4j.query

            def patched_query(self, cypher: str, params=None):
                """Patch all Cypher queries before execution"""
                if isinstance(cypher, str):
                    cypher = cypher.replace('vector.similarity.cosine', 'gds.similarity.cosine')
                    cypher = cypher.replace('vector.similarity.euclidean', 'gds.similarity.euclidean')
                return original_query(self, cypher, params)

            graph_memory.Neo4j.query = patched_query
            print("✅ Patched Neo4j.query() method")

        print("✅ mem0 GDS patch applied successfully")
        print("   - vector.similarity.cosine → gds.similarity.cosine")
        print("   - vector.similarity.euclidean → gds.similarity.euclidean")

        return True

    except ImportError as e:
        print(f"⚠️  mem0 not yet imported: {e}")
        print("   Patch will be applied via import hook")
        return False
    except Exception as e:
        print(f"❌ Error applying mem0 GDS patch: {e}")
        import traceback
        traceback.print_exc()
        return False


def install_import_hook():
    """Install import hook to patch mem0 when it's imported"""

    import importlib.abc
    import importlib.machinery

    class Mem0Patcher(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        """Import hook that patches mem0.memory.graph_memory on import"""

        def find_module(self, fullname, path=None):
            if fullname == 'mem0.memory.graph_memory':
                return self
            return None

        def load_module(self, fullname):
            if fullname in sys.modules:
                return sys.modules[fullname]

            # Import the module normally
            import importlib
            module = importlib.import_module(fullname)

            # Now patch it
            patch_mem0_for_gds()

            return module

    sys.meta_path.insert(0, Mem0Patcher())
    print("✅ mem0 GDS import hook installed")


if __name__ == '__main__':
    # Try to patch immediately if mem0 is already imported
    patched = patch_mem0_for_gds()

    # If not patched yet, install import hook
    if not patched:
        install_import_hook()
        print("🔧 Import hook installed - will patch when mem0 is imported")
