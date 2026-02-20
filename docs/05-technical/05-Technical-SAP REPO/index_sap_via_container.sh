#!/bin/bash
# Index SAP documents via ChromaDB container
# This script runs indexing inside the container where ChromaDB has direct access

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAP_PATH="${SAP_PATH:-/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP}"
CONTAINER="intel-chromadb-prd"

echo "============================================================"
echo "SAP RAG Document Indexing - Container Method"
echo "============================================================"
echo ""

# Check container is running
if ! docker ps | grep -q "$CONTAINER"; then
    echo "❌ Container $CONTAINER is not running"
    exit 1
fi

echo "✅ Container $CONTAINER is running"
echo ""

# Create Python script inline
docker exec -i "$CONTAINER" python3 << 'PYEOF'
import chromadb
import sys
from pathlib import Path

print("Connecting to ChromaDB...")
client = chromadb.Client()

# Get or create collection
try:
    collection = client.get_collection('sap_workspace')
    print(f'✅ Using existing collection: {collection.count()} documents')
except:
    collection = client.create_collection(
        name='sap_workspace',
        metadata={'namespace': 'sap', 'client': 'SAP Deutschland', 'manager': 'Oliver Posselt'}
    )
    print('✅ Created collection: sap_workspace')

# For now, just verify connection works
print(f'✅ Collection ready: {collection.count()} documents')
print('✅ ChromaDB connection verified')
print('')
print('NOTE: Full indexing requires mounting SAP path to container')
print('      or using RAG pipeline indexing endpoint if available')

PYEOF

echo ""
echo "✅ Container ChromaDB connection verified"
echo ""
echo "Next steps:"
echo "1. Mount SAP workspace to container"
echo "2. Run full indexing script inside container"
echo "3. Or use RAG pipeline indexing endpoint (if available)"

