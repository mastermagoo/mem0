#!/bin/bash
# WORKING SOLUTION: Index all SAP documents NOW
# Copies files to container, then indexes them

set -e

SAP_PATH="${SAP_PATH:-/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP}"
CONTAINER="intel-chromadb-prd"
TEMP_DIR="/tmp/sap_indexing_$$"

echo "============================================================"
echo "SAP RAG Document Indexing - FULL INDEXING NOW"
echo "============================================================"
echo ""

# Check container
if ! docker ps | grep -q "$CONTAINER"; then
    echo "❌ Container $CONTAINER is not running"
    exit 1
fi

echo "✅ Container $CONTAINER is running"
echo ""

# Copy files to container
echo "📦 Copying SAP files to container..."
cd "$SAP_PATH"
tar czf - --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='archive' --exclude='.DS_Store' . 2>/dev/null | \
    docker exec -i "$CONTAINER" sh -c "mkdir -p $TEMP_DIR && cd $TEMP_DIR && tar xzf -" 2>&1 | grep -v "tar:" || true

echo "✅ Files copied to container"
echo ""

# Run indexing
echo "🔍 Indexing documents..."
docker exec "$CONTAINER" python3 << PYEOF
import chromadb
from pathlib import Path
import sys
import time
from datetime import datetime

TEMP_DIR = "$TEMP_DIR"
COLLECTION_NAME = "sap_workspace"
BATCH_SIZE = 50

# Connect
client = chromadb.Client()
collection = client.get_collection(COLLECTION_NAME)

print(f"📊 Starting with {collection.count()} documents")
print("")

# Find documents
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
            if file_path.stat().st_size > 10 * 1024 * 1024:
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
processed = 0
errors = 0
start_time = datetime.now()

for i in range(0, len(documents), BATCH_SIZE):
    batch = documents[i:i+BATCH_SIZE]
    batch_num = (i // BATCH_SIZE) + 1
    total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)...")
    
    batch_ids = []
    batch_docs = []
    batch_metas = []
    
    for file_path in batch:
        try:
            content = file_path.read_text(encoding='utf-8')
        except:
            try:
                content = file_path.read_text(encoding='latin-1')
            except:
                errors += 1
                continue
        
        # Create relative path for ID
        try:
            rel_path = file_path.relative_to(sap_path)
            doc_id = str(rel_path)
        except:
            doc_id = str(file_path.name)
        
        metadata = {
            'source': str(file_path),
            'relative_path': doc_id,
            'file_type': file_path.suffix,
            'namespace': 'sap',
            'indexed_at': datetime.now().isoformat()
        }
        
        batch_ids.append(doc_id)
        batch_docs.append(content[:10000])  # Limit size
        batch_metas.append(metadata)
        processed += 1
    
    # Add batch
    if batch_ids:
        try:
            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas
            )
            print(f"✅ Indexed {len(batch_ids)} documents")
        except Exception as e:
            print(f"❌ Batch error: {e}")
            errors += len(batch_ids)
    
    if i + BATCH_SIZE < len(documents):
        time.sleep(0.5)

# Summary
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

# Test query
try:
    results = collection.query(query_texts=["Oliver performance"], n_results=3)
    print(f"✅ Query test: {len(results['documents'][0])} results found")
except Exception as e:
    print(f"⚠️  Query test failed: {e}")

# Cleanup
import shutil
shutil.rmtree(TEMP_DIR, ignore_errors=True)
print(f"🧹 Cleaned up temp directory")

PYEOF

echo ""
echo "✅ Indexing complete!"

