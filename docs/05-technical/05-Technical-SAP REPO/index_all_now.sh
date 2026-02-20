#!/bin/bash
# Index all SAP documents NOW - Container Method
# This script indexes all documents by running Python inside the ChromaDB container

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAP_PATH="${SAP_PATH:-/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP}"
CONTAINER="intel-chromadb-prd"
COLLECTION="sap_workspace"

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

# Copy indexing script to container
echo "Preparing indexing script..."
docker cp "$SCRIPT_DIR/index_sap_final.py" "$CONTAINER:/tmp/index_sap_final.py" 2>/dev/null || true

# Create Python script that reads from host filesystem via docker exec
# We'll use a different approach - copy files to container first, then index

echo "Indexing all documents..."
echo ""

# Run indexing via container with mounted volume approach
# Since we can't easily mount, we'll use docker exec with file copying

docker exec "$CONTAINER" python3 << 'PYEOF'
import chromadb
import sys
import os
from pathlib import Path
import time
from datetime import datetime

# Connect to ChromaDB
client = chromadb.Client()
collection = client.get_collection('sap_workspace')

print(f"📊 Starting with {collection.count()} documents")
print("")

# We need to get files from host
# Since we can't mount easily, we'll use a workaround:
# Copy files to container via docker cp, then index

print("⚠️  Direct indexing from host requires volume mount")
print("")
print("Alternative: Using file-by-file approach via docker exec...")
print("")

# For now, let's try to access files if they're accessible
# Check common mount points
possible_paths = [
    "/mnt/sap",
    "/sap",
    "/data/sap",
    "/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP"
]

sap_path = None
for path in possible_paths:
    if Path(path).exists():
        sap_path = Path(path)
        print(f"✅ Found SAP path: {sap_path}")
        break

if not sap_path:
    print("❌ SAP path not accessible from container")
    print("")
    print("SOLUTION: Need to mount SAP workspace to container")
    print("  Option 1: Update docker-compose to add volume mount")
    print("  Option 2: Use docker run with -v flag")
    print("  Option 3: Copy files to container, then index")
    sys.exit(1)

# Index files
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
BATCH_SIZE = 50
processed = 0
errors = 0

for i in range(0, len(documents), BATCH_SIZE):
    batch = documents[i:i+BATCH_SIZE]
    batch_num = (i // BATCH_SIZE) + 1
    total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"Processing batch {batch_num}/{total_batches}...")
    
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
        
        doc_id = str(file_path.relative_to(sap_path))
        metadata = {
            'source': str(file_path),
            'relative_path': doc_id,
            'file_type': file_path.suffix,
            'namespace': 'sap',
            'indexed_at': datetime.now().isoformat()
        }
        
        batch_ids.append(doc_id)
        batch_docs.append(content[:10000])
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
        time.sleep(1)

# Summary
final_count = collection.count()
print("")
print("=" * 60)
print("INDEXING COMPLETE")
print("=" * 60)
print(f"📄 Documents found: {len(documents)}")
print(f"✅ Processed: {processed}")
print(f"❌ Errors: {errors}")
print(f"📊 Collection total: {final_count} documents")
print("")

# Test query
try:
    results = collection.query(query_texts=["Oliver performance"], n_results=3)
    print(f"✅ Query test: {len(results['documents'][0])} results found")
except Exception as e:
    print(f"⚠️  Query test failed: {e}")

PYEOF

echo ""
echo "✅ Indexing complete!"

