#!/usr/bin/env python3
"""
Final SAP Document Indexing - Runs inside ChromaDB container
Mount SAP workspace to /mnt/sap in container before running
"""
import chromadb
from pathlib import Path
import sys
import time
from datetime import datetime

SAP_PATH = Path("/mnt/sap")
COLLECTION_NAME = "sap_workspace"
BATCH_SIZE = 50
SUPPORTED_EXTENSIONS = {'.md', '.txt', '.py', '.json', '.yaml', '.yml', '.sh'}
EXCLUDE_PATTERNS = ['node_modules', '.git', '__pycache__', '.DS_Store', 'archive', '.smbdelete']

def should_process(file_path):
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False
    if any(p in str(file_path) for p in EXCLUDE_PATTERNS):
        return False
    try:
        if file_path.stat().st_size > 10 * 1024 * 1024:
            return False
    except:
        return False
    return True

def read_file(file_path):
    try:
        return file_path.read_text(encoding='utf-8')
    except:
        try:
            return file_path.read_text(encoding='latin-1')
        except:
            return None

def main():
    print("=" * 60)
    print("SAP RAG Document Indexing - Container Version")
    print("=" * 60)
    print()
    
    # Check SAP path
    if not SAP_PATH.exists():
        print(f"❌ SAP path not found: {SAP_PATH}")
        print("   Mount SAP workspace to /mnt/sap in container")
        return 1
    
    # Connect to ChromaDB
    print("Connecting to ChromaDB...")
    try:
        client = chromadb.Client()
        print("✅ Connected to ChromaDB")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return 1
    
    # Get or create collection
    print(f"Getting/creating collection: {COLLECTION_NAME}")
    try:
        try:
            collection = client.get_collection(COLLECTION_NAME)
            print(f"✅ Using existing collection: {collection.count()} documents")
        except:
            collection = client.create_collection(
                name=COLLECTION_NAME,
                metadata={'namespace': 'sap', 'client': 'SAP Deutschland', 'manager': 'Oliver Posselt'}
            )
            print(f"✅ Created collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"❌ Failed to get/create collection: {e}")
        return 1
    
    # Find documents
    print(f"\nScanning documents in {SAP_PATH}...")
    documents = []
    for file_path in SAP_PATH.rglob('*'):
        if file_path.is_file() and should_process(file_path):
            documents.append(file_path)
    
    print(f"Found {len(documents)} documents to index")
    
    if not documents:
        print("❌ No documents found!")
        return 1
    
    # Index in batches
    print(f"\nIndexing {len(documents)} documents in batches of {BATCH_SIZE}...")
    start_time = datetime.now()
    processed = 0
    errors = 0
    
    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n--- Batch {batch_num}/{total_batches} ---")
        
        batch_ids = []
        batch_docs = []
        batch_metas = []
        
        for file_path in batch:
            content = read_file(file_path)
            if not content:
                errors += 1
                continue
            
            doc_id = str(file_path.relative_to(SAP_PATH))
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
            time.sleep(1)
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    final_count = collection.count()
    
    print("\n" + "=" * 60)
    print("INDEXING COMPLETE")
    print("=" * 60)
    print(f"📄 Documents found: {len(documents)}")
    print(f"✅ Processed: {processed}")
    print(f"❌ Errors: {errors}")
    print(f"📊 Collection total: {final_count} documents")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print()
    
    # Test query
    print("Testing query...")
    try:
        results = collection.query(query_texts=["Oliver performance"], n_results=3)
        print(f"✅ Query test: {len(results['documents'][0])} results found")
    except Exception as e:
        print(f"⚠️  Query test failed: {e}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

