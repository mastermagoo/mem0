#!/bin/bash
# Setup automatic indexing for new SAP files
# Creates cron job to run every hour

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INDEX_SCRIPT="$SCRIPT_DIR/auto_index_new_files.sh"

echo "Setting up automatic RAG indexing..."
echo ""

# Make script executable
chmod +x "$INDEX_SCRIPT"

# Add to crontab (runs every hour)
(crontab -l 2>/dev/null | grep -v "auto_index_new_files.sh"; echo "0 * * * * $INDEX_SCRIPT >> /tmp/rag_auto_index.log 2>&1") | crontab -

echo "✅ Automatic indexing configured"
echo "   - Runs every hour"
echo "   - Logs to: /tmp/rag_auto_index.log"
echo "   - Indexes new/modified files in last 24 hours"
echo ""
echo "To test now: $INDEX_SCRIPT"
echo "To view logs: tail -f /tmp/rag_auto_index.log"

