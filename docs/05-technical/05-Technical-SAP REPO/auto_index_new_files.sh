#!/bin/bash
# Automatic indexing for new SAP files
# Uses the standalone Python script for reliable indexing

SAP_PATH="${SAP_PATH:-/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP}"
CONTAINER="intel-chromadb-prd"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/rag_auto_index.log"
CHROMA_DATA_PATH="/chroma"
EMBEDDING_MODEL="all-MiniLM-L6-v2"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Index new files using standalone script
index_new_files() {
    log "Checking for new files to index..."
    
    # Find files modified in last 24 hours
    new_files=$(find "$SAP_PATH" -type f \( -name "*.md" -o -name "*.txt" -o -name "*.py" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.sh" \) \
        ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/__pycache__/*" ! -path "*/archive/*" \
        -mtime -1 2>/dev/null | wc -l)
    
    if [ "$new_files" -eq 0 ]; then
        log "No new files found"
        return 0
    fi
    
    log "Found $new_files new/modified files - running full re-index for reliability"
    
    # Use the robust indexing script for reliability
    # Copy latest files and run standalone script
    cd "$SAP_PATH"
    TAR_BUNDLE="/tmp/sap_auto_index_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar czf "$TAR_BUNDLE" \
        --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='.DS_Store' \
        --exclude='docs/archive' --exclude='docs/Private_Intelligence' --exclude='docs/AAA_STRATEGIC_COMMAND' --exclude='docs/AAA_EMERGENCY_PROTECTION' \
        --exclude='**/site-packages/**' --exclude='**/mediapipe_env/**' --exclude='**/video_analysis_env/**' \
        . 2>/dev/null
    
    docker cp "$TAR_BUNDLE" "$CONTAINER:/tmp/" 2>/dev/null
    docker cp "$SCRIPT_DIR/index_sap_standalone.py" "$CONTAINER:/tmp/" 2>/dev/null
    
    docker exec "$CONTAINER" sh -c "cd /tmp && rm -rf sap_index_auto && mkdir -p sap_index_auto && cd sap_index_auto && tar xzf ../$(basename "$TAR_BUNDLE") 2>/dev/null" 2>&1 | grep -v "tar:" || true
    
    # Run indexing (script will update existing collection)
    docker exec -e CHROMA_DATA_PATH="$CHROMA_DATA_PATH" -e EMBEDDING_MODEL="$EMBEDDING_MODEL" "$CONTAINER" \
        python3 /tmp/index_sap_standalone.py 2>&1 | grep -E "(Batch|COMPLETE|documents)" | tail -5 >> "$LOG_FILE" 2>&1
    
    log "Indexing complete"
    
    # Cleanup
    rm -f "$TAR_BUNDLE"
}

# Run indexing
index_new_files

