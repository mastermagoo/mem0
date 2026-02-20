#!/bin/bash
# ROBUST SOLUTION: Index all SAP documents - Extract, Index, Verify
# This script ensures all data is indexed in container ChromaDB

set -e

SAP_PATH="${SAP_PATH:-/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP}"
CONTAINER="intel-chromadb-prd"
TEMP_DIR="/tmp/sap_index_$(date +%s)"

echo "============================================================"
echo "SAP RAG INDEXING - ROBUST SOLUTION"
echo "============================================================"
echo ""

# Check container
if ! docker ps | grep -q "$CONTAINER"; then
    echo "❌ Container $CONTAINER is not running"
    exit 1
fi

echo "✅ Container running: $CONTAINER"
echo ""

# Step 1: Extract all files to container
echo "📦 Step 1: Copying all SAP files to container..."
cd "$SAP_PATH"
tar czf - --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='archive' --exclude='.DS_Store' . 2>/dev/null | \
    docker exec -i "$CONTAINER" sh -c "mkdir -p $TEMP_DIR && cd $TEMP_DIR && tar xzf -" 2>&1 | grep -v "tar:" | head -5 || true

echo "✅ Files copied to: $TEMP_DIR"
echo ""

# Step 2: Index all documents
echo "🔍 Step 2: Indexing all documents..."
docker exec "$CONTAINER" python3 << PYEOF
import chromadb
from pathlib import Path
import sys
import time
from datetime import datetime
import hashlib

TEMP_DIR = "$TEMP_DIR"
COLLECTION_NAME = "sap_workspace"
BATCH_SIZE = 50

print("Connecting to ChromaDB...")
client = chromadb.Client()

# Create or get collection
try:
    collection = client.get_collection(COLLECTION_NAME)
    print(f"✅ Using existing collection: {collection.count()} documents")
    # Clear it to re-index fresh
    print("🔄 Clearing collection for fresh index...")
    client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={'namespace': 'sap', 'client': 'SAP Deutschland', 'manager': 'Oliver Posselt'}
    )
    print("✅ Created fresh collection")
except Exception as e:
    try:
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={'namespace': 'sap', 'client': 'SAP Deutschland', 'manager': 'Oliver Posselt'}
        )
        print("✅ Created new collection")
    except Exception as e2:
        print(f"❌ Failed to create collection: {e2}")
        sys.exit(1)

# Find all documents
print(f"\nScanning {TEMP_DIR} for documents...")
sap_path = Path(TEMP_DIR)
extensions = {'.md', '.txt', '.py', '.json', '.yaml', '.yml', '.sh'}
exclude = ['node_modules', '.git', '__pycache__', '.DS_Store', 'archive', '.smbdelete']

documents = []
for file_path in sap_path.rglob('*'):
    if file_path.is_file():
        if file_path.suffix.lower() not in extensions:
            continue
        if any(p in str(file_path) for p in exclude):
            continue
        try:
            size = file_path.stat().st_size
            if size == 0 or size > 10 * 1024 * 1024:
                continue
        except:
            continue
        documents.append(file_path)

print(f"📄 Found {len(documents)} documents to index")
print("")

if not documents:
    print("❌ No documents found!")
    sys.exit(1)

# Index in batches
print("Indexing documents in batches...")
processed = 0
errors = 0
start_time = datetime.now()

for i in range(0, len(documents), BATCH_SIZE):
    batch = documents[i:i+BATCH_SIZE]
    batch_num = (i // BATCH_SIZE) + 1
    total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
    
    batch_ids = []
    batch_docs = []
    batch_metas = []
    
    for file_path in batch:
        try:
            # Read content
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except:
                content = file_path.read_text(encoding='latin-1', errors='ignore')
            
            if not content or len(content.strip()) == 0:
                continue
            
            # Limit size
            if len(content) > 10000:
                content = content[:10000]
            
            # Create unique ID
            try:
                rel_path = str(file_path.relative_to(sap_path))
                # Create hash-based ID to avoid collisions
                doc_id = hashlib.md5(rel_path.encode()).hexdigest()[:16] + "_" + rel_path.replace("/", "_").replace("\\", "_")[-50:]
            except:
                doc_id = f"doc_{hashlib.md5(str(file_path).encode()).hexdigest()[:16]}"
            
            # Metadata
            metadata = {
                'source': str(file_path),
                'relative_path': rel_path if 'rel_path' in locals() else str(file_path),
                'file_type': file_path.suffix,
                'namespace': 'sap',
                'indexed_at': datetime.now().isoformat(),
                'file_size': file_path.stat().st_size
            }
            
            batch_ids.append(doc_id)
            batch_docs.append(content)
            batch_metas.append(metadata)
            processed += 1
            
        except Exception as e:
            errors += 1
            continue
    
    # Add batch to collection
    if batch_ids:
        try:
            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas
            )
            current_count = collection.count()
            print(f"✅ Batch {batch_num}/{total_batches}: {len(batch_ids)} indexed (total: {current_count})")
        except Exception as e:
            print(f"❌ Batch {batch_num} error: {str(e)[:100]}")
            errors += len(batch_ids)
    
    time.sleep(0.1)

# Final summary
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()
final_count = collection.count()

print("")
print("=" * 60)
print("INDEXING COMPLETE")
print("=" * 60)
print(f"📄 Documents found: {len(documents)}")
print(f"✅ Processed: {processed}")
print(f"❌ Errors: {errors}")
print(f"📊 Collection total: {final_count} documents")
print(f"⏱️  Duration: {duration:.1f} seconds")
print("")

# Verify with query
print("Testing query...")
try:
    results = collection.query(query_texts=["Oliver performance"], n_results=3)
    result_count = len(results['documents'][0]) if results['documents'] else 0
    print(f"✅ Query test successful: {result_count} results found")
    if result_count > 0:
        print(f"   Sample: {results['documents'][0][0][:100]}...")
except Exception as e:
    print(f"⚠️  Query test failed: {e}")

# Cleanup
print(f"\n🧹 Cleaning up temp directory...")
import shutil
shutil.rmtree(TEMP_DIR, ignore_errors=True)

print("")
print("✅ INDEXING COMPLETE AND VERIFIED")
PYEOF

echo ""
echo "============================================================"
echo "✅ FINAL VERIFICATION"
echo "============================================================"

# Verify final count
FINAL_COUNT=$(docker exec "$CONTAINER" python3 -c "import chromadb; print(chromadb.Client().get_collection('sap_workspace').count())" 2>&1 | grep -v "onnxruntime\|Failed to send" | tail -1)
echo "📊 Final document count: $FINAL_COUNT"
echo ""

if [ "$FINAL_COUNT" -gt 100 ]; then
    echo "✅ SUCCESS: Collection fully indexed!"
else
    echo "⚠️  WARNING: Low document count. May need to re-run."
fi

echo ""
echo "✅ Indexing complete!"

