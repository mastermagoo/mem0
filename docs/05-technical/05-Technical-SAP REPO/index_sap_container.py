#!/usr/bin/env python3
"""
SAP RAG Document Indexing Script - Container Version
Runs inside ChromaDB container to index documents directly
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional

try:
    import chromadb
except ImportError:
    print("ERROR: chromadb not installed")
    sys.exit(1)

# Configuration
SAP_PATH = Path("/mnt/sap")  # Mount point in container
COLLECTION_NAME = "sap_workspace"
BATCH_SIZE = 50
BATCH_DELAY = 1.0

# File extensions to process
SUPPORTED_EXTENSIONS = {'.md', '.txt', '.py', '.json', '.yaml', '.yml', '.sh'}

# Exclude patterns
EXCLUDE_PATTERNS = [
    'node_modules', '.git', '__pycache__', '.DS_Store', 'archive', '.smbdelete'
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_documents(path: Path) -> List[Dict]:
    """Scan and collect documents"""
    documents = []
    for file_path in path.rglob('*'):
        if file_path.is_file():
            # Check extension
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            # Check exclude patterns
            if any(pattern in str(file_path) for pattern in EXCLUDE_PATTERNS):
                continue
            # Check size (skip > 10MB)
            try:
                if file_path.stat().st_size > 10 * 1024 * 1024:
                    continue
            except:
                continue
            
            # Read content
            try:
                content = file_path.read_text(encoding='utf-8')
            except:
                try:
                    content = file_path.read_text(encoding='latin-1')
                except:
                    continue
            
            documents.append({
                'content': content,
                'metadata': {
                    'source': str(file_path.relative_to(path)),
                    'namespace': 'sap',
                    'client': 'SAP Deutschland',
                    'manager': 'Oliver Posselt'
                }
            })
    
    return documents


def main():
    logger.info("Starting SAP document indexing in container...")
    
    # Connect to ChromaDB (local in container)
    try:
        client = chromadb.Client()
        logger.info("✅ Connected to ChromaDB")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return 1
    
    # Get or create collection
    try:
        try:
            collection = client.get_collection(COLLECTION_NAME)
            logger.info(f"✅ Using existing collection: {COLLECTION_NAME}")
        except:
            collection = client.create_collection(
                name=COLLECTION_NAME,
                metadata={"namespace": "sap", "client": "SAP Deutschland", "manager": "Oliver Posselt"}
            )
            logger.info(f"✅ Created collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.error(f"Failed to get/create collection: {e}")
        return 1
    
    # Check if SAP path is mounted
    if not SAP_PATH.exists():
        logger.error(f"SAP path not found: {SAP_PATH}")
        logger.info("Mount SAP workspace to /mnt/sap in container")
        return 1
    
    # Get documents
    logger.info(f"Scanning documents in {SAP_PATH}...")
    documents = get_documents(SAP_PATH)
    logger.info(f"Found {len(documents)} documents")
    
    if not documents:
        logger.warning("No documents found!")
        return 1
    
    # Index in batches
    logger.info(f"Indexing {len(documents)} documents in batches of {BATCH_SIZE}...")
    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i:i+BATCH_SIZE]
        try:
            collection.add(
                documents=[d['content'] for d in batch],
                metadatas=[d['metadata'] for d in batch],
                ids=[f"doc_{i+j}" for j in range(len(batch))]
            )
            logger.info(f"✅ Indexed batch {i//BATCH_SIZE + 1} ({len(batch)} documents)")
        except Exception as e:
            logger.error(f"Failed to index batch {i//BATCH_SIZE + 1}: {e}")
        
        if i + BATCH_SIZE < len(documents):
            time.sleep(BATCH_DELAY)
    
    # Verify
    count = collection.count()
    logger.info(f"✅ Indexing complete! Collection has {count} documents")
    
    # Test query
    try:
        results = collection.query(query_texts=["Oliver performance"], n_results=3)
        logger.info(f"✅ Test query successful: {len(results['documents'][0])} results")
    except Exception as e:
        logger.warning(f"Test query failed: {e}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

