#!/bin/bash
# mem0 Startup Script with GDS Patch
# Created: 2025-10-16
# Purpose: Apply GDS compatibility patch before starting mem0 server

set -e

echo "================================================"
echo "🚀 Starting mem0 with Neo4j GDS Patch"
echo "================================================"
echo ""

# Apply GDS patch before starting server
echo "🔧 Applying GDS patch..."
python3 /app/mem0_gds_patch_v2.py

# Start mem0 server with uvicorn
echo "🚀 Starting mem0 server..."
cd /app

# Run uvicorn with the patch already loaded
python3 <<'PYTHON'
# Import and apply patch before uvicorn loads the app
import sys
import os
sys.path.insert(0, '/app')

# Import and apply the GDS patch
from mem0_gds_patch_v2 import patch_neo4j_graph
patch_neo4j_graph()

# Now start uvicorn
import uvicorn
port = int(os.getenv('MEM0_PORT', '8888'))
uvicorn.run('main:app', host='0.0.0.0', port=port, reload=False)
PYTHON
