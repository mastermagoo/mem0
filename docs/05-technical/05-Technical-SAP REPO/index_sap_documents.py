#!/usr/bin/env python3
"""
SAP RAG Document Indexing Script
Indexes SAP workspace documents into ChromaDB for RAG pipeline

Date: 2025-11-28
Status: Production Ready
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ERROR: chromadb not installed. Install with: pip install chromadb")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Install with: pip install requests")
    sys.exit(1)

# Configuration
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8001"))
CHROMADB_URL = os.getenv("CHROMADB_URL", f"http://{CHROMADB_HOST}:{CHROMADB_PORT}")
EMBEDDINGS_URL = os.getenv("EMBEDDINGS_URL", "http://localhost:8022")
SAP_PATH = Path(os.environ.get("SAP_PATH", "/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP"))
COLLECTION_NAME = "sap_workspace"
BATCH_SIZE = 50
BATCH_DELAY = 1.0  # seconds
FORCE_HTTP = os.getenv("FORCE_HTTP", "true").lower() == "true"  # Force HTTP client for container

# File extensions to process
SUPPORTED_EXTENSIONS = {'.md', '.txt', '.py', '.json', '.yaml', '.yml', '.sh'}

# Exclude patterns
EXCLUDE_PATTERNS = [
    'node_modules',
    '.git',
    '__pycache__',
    '.DS_Store',
    'archive',
    '.smbdelete'
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_indexing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SAPDocumentIndexer:
    """Index SAP documents into ChromaDB for RAG"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.embeddings_url = EMBEDDINGS_URL
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'skipped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def connect_chromadb(self) -> bool:
        """Connect to ChromaDB - Force HTTP client for container"""
        try:
            logger.info(f"Connecting to ChromaDB at {CHROMADB_URL}")
            
            # Force HTTP client for container ChromaDB
            if FORCE_HTTP:
                logger.info("Using HttpClient (container mode)")
                self.client = chromadb.HttpClient(
                    host=CHROMADB_HOST,
                    port=CHROMADB_PORT
                )
                # Test connection
                try:
                    collections = self.client.list_collections()
                    logger.info(f"✅ Connected via HttpClient - Found {len(collections)} collections")
                except Exception as e:
                    logger.error(f"HttpClient connection test failed: {e}")
                    raise
            else:
                # Fallback to persistent client (for local mode)
                logger.info("Using PersistentClient (local mode)")
                self.client = chromadb.PersistentClient(
                    path=f"/tmp/chromadb_{COLLECTION_NAME}"
                )
                logger.info("✅ Connected via PersistentClient")
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            return False
    
    def get_or_create_collection(self) -> bool:
        """Get or create SAP workspace collection"""
        try:
            logger.info(f"Getting/creating collection: {COLLECTION_NAME}")
            
            # Try to get existing collection
            try:
                self.collection = self.client.get_collection(
                    name=COLLECTION_NAME,
                    metadata={"namespace": "sap", "client": "SAP Deutschland"}
                )
                logger.info(f"✅ Found existing collection: {COLLECTION_NAME}")
                logger.info(f"   Current count: {self.collection.count()}")
            except Exception:
                # Create new collection
                self.collection = self.client.create_collection(
                    name=COLLECTION_NAME,
                    metadata={
                        "namespace": "sap",
                        "client": "SAP Deutschland",
                        "manager": "Oliver Posselt",
                        "created": datetime.now().isoformat()
                    }
                )
                logger.info(f"✅ Created new collection: {COLLECTION_NAME}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to get/create collection: {e}")
            return False
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from embeddings service"""
        try:
            response = requests.post(
                f"{self.embeddings_url}/embed",
                json={"text": text},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding")
            else:
                logger.warning(f"Embedding service returned {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"Failed to get embedding: {e}")
            return None
    
    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed"""
        # Check extension
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return False
        
        # Check exclude patterns
        path_str = str(file_path)
        for pattern in EXCLUDE_PATTERNS:
            if pattern in path_str:
                return False
        
        # Check file size (skip very large files)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"Skipping large file: {file_path}")
                return False
        except Exception:
            return False
        
        return True
    
    def read_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content with encoding handling"""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip if too short (likely not useful)
            if len(content.strip()) < 50:
                return None
            
            return content
        except UnicodeDecodeError:
            # Try latin-1 as fallback
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                return content
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                return None
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            return None
    
    def find_documents(self) -> List[Path]:
        """Find all documents to index"""
        logger.info(f"Scanning for documents in: {SAP_PATH}")
        
        documents = []
        for root, dirs, files in os.walk(SAP_PATH):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(p in d for p in EXCLUDE_PATTERNS)]
            
            for file in files:
                file_path = Path(root) / file
                if self.should_process_file(file_path):
                    documents.append(file_path)
        
        logger.info(f"Found {len(documents)} documents to process")
        return documents
    
    def index_documents(self, documents: List[Path]) -> bool:
        """Index documents in batches"""
        self.stats['start_time'] = datetime.now()
        self.stats['total_files'] = len(documents)
        
        logger.info(f"Starting indexing of {len(documents)} documents")
        logger.info(f"Batch size: {BATCH_SIZE}, Delay: {BATCH_DELAY}s")
        
        # Process in batches
        for i in range(0, len(documents), BATCH_SIZE):
            batch = documents[i:i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
            
            logger.info(f"\n--- Processing batch {batch_num}/{total_batches} ---")
            
            batch_ids = []
            batch_documents = []
            batch_metadatas = []
            
            for file_path in batch:
                try:
                    # Read content
                    content = self.read_file_content(file_path)
                    if not content:
                        self.stats['skipped'] += 1
                        continue
                    
                    # Create document ID
                    doc_id = str(file_path.relative_to(SAP_PATH))
                    
                    # Create metadata
                    metadata = {
                        "source": str(file_path),
                        "relative_path": doc_id,
                        "file_type": file_path.suffix,
                        "indexed_at": datetime.now().isoformat(),
                        "namespace": "sap"
                    }
                    
                    batch_ids.append(doc_id)
                    batch_documents.append(content[:10000])  # Limit to 10k chars
                    batch_metadatas.append(metadata)
                    
                    self.stats['processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    self.stats['errors'] += 1
                    self.stats['skipped'] += 1
            
            # Add batch to collection
            if batch_ids:
                try:
                    self.collection.add(
                        ids=batch_ids,
                        documents=batch_documents,
                        metadatas=batch_metadatas
                    )
                    logger.info(f"✅ Indexed {len(batch_ids)} documents in batch {batch_num}")
                except Exception as e:
                    logger.error(f"Failed to index batch {batch_num}: {e}")
                    self.stats['errors'] += len(batch_ids)
            
            # Delay between batches
            if i + BATCH_SIZE < len(documents):
                time.sleep(BATCH_DELAY)
        
        self.stats['end_time'] = datetime.now()
        return True
    
    def verify_indexing(self) -> bool:
        """Verify indexing completed successfully"""
        try:
            count = self.collection.count()
            logger.info(f"\n✅ Verification complete:")
            logger.info(f"   Collection: {COLLECTION_NAME}")
            logger.info(f"   Documents indexed: {count}")
            logger.info(f"   Files processed: {self.stats['processed']}")
            logger.info(f"   Files skipped: {self.stats['skipped']}")
            logger.info(f"   Errors: {self.stats['errors']}")
            
            # Test query
            logger.info("\nTesting query...")
            results = self.collection.query(
                query_texts=["SAP stakeholders"],
                n_results=3
            )
            if results['ids']:
                logger.info(f"✅ Query test successful: Found {len(results['ids'][0])} results")
            else:
                logger.warning("⚠️ Query test returned no results")
            
            return True
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False
    
    def print_summary(self):
        """Print execution summary"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        print("\n" + "="*60)
        print("SAP RAG INDEXING SUMMARY")
        print("="*60)
        print(f"Total files found:    {self.stats['total_files']}")
        print(f"Files processed:       {self.stats['processed']}")
        print(f"Files skipped:         {self.stats['skipped']}")
        print(f"Errors:                {self.stats['errors']}")
        print(f"Duration:              {duration:.1f} seconds")
        print(f"Collection:           {COLLECTION_NAME}")
        print(f"Documents in DB:      {self.collection.count() if self.collection else 'N/A'}")
        print("="*60)
    
    def run(self) -> bool:
        """Main execution"""
        logger.info("="*60)
        logger.info("SAP RAG Document Indexing")
        logger.info("="*60)
        
        # Connect to ChromaDB
        if not self.connect_chromadb():
            return False
        
        # Get or create collection
        if not self.get_or_create_collection():
            return False
        
        # Find documents
        documents = self.find_documents()
        if not documents:
            logger.warning("No documents found to index")
            return False
        
        # Index documents
        if not self.index_documents(documents):
            return False
        
        # Verify
        if not self.verify_indexing():
            return False
        
        # Print summary
        self.print_summary()
        
        logger.info("\n✅ Indexing complete!")
        return True


def main():
    """Main entry point"""
    indexer = SAPDocumentIndexer()
    success = indexer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

