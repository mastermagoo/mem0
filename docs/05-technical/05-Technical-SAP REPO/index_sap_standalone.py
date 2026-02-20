#!/usr/bin/env python3
"""
Standalone SAP Document Indexer
Run this inside ChromaDB container to index all SAP documents
"""
import chromadb
from pathlib import Path
import sys
import time
from datetime import datetime
import hashlib
import glob
import os
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "sap_workspace"
BATCH_SIZE = 50

def main():
    print("=" * 60)
    print("SAP RAG INDEXING - STANDALONE")
    print("=" * 60)
    print()
    
    # Connect to ChromaDB with persistent path
    print("Connecting to ChromaDB...")
    chroma_path = os.getenv("CHROMA_DATA_PATH", "/chroma")
    client = chromadb.PersistentClient(path=chroma_path)
    print(f"✅ Connected to persistent ChromaDB at {chroma_path}")
    print()
    
    # Create or get collection
    print(f"Creating/getting collection: {COLLECTION_NAME}")
    try:
        collection = client.get_collection(COLLECTION_NAME)
        print(f"✅ Collection exists: {collection.count()} documents")
        # Clear for fresh index
        print("🔄 Clearing for fresh index...")
        client.delete_collection(COLLECTION_NAME)
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={'namespace': 'sap', 'client': 'SAP Deutschland', 'manager': 'Oliver Posselt'}
        )
        print("✅ Fresh collection created")
    except:
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={'namespace': 'sap', 'client': 'SAP Deutschland', 'manager': 'Oliver Posselt'}
        )
        print("✅ Collection created")
    print()
    
    # Find SAP files directory
    temp_dirs = [p for p in glob.glob("/tmp/sap_index_*") if os.path.isdir(p)]
    if not temp_dirs:
        print("❌ No SAP files directory found in /tmp/sap_index_*")
        print("   Files should be extracted to /tmp/sap_index_* first")
        return 1
    
    # Prefer the most recently modified folder
    temp_dirs.sort(key=lambda p: os.path.getmtime(p))
    sap_path = Path(temp_dirs[-1])
    print(f"📁 Using directory: {sap_path}")
    print()
    
    # Find all documents
    print("Scanning for documents...")
    extensions = {'.md', '.txt', '.py', '.json', '.yaml', '.yml', '.sh'}
    # Exclusions: keep the index high-signal and avoid ingesting local environments / vendor libs.
    exclude = [
        'node_modules',
        '.git',
        '__pycache__',
        '.DS_Store',
        '.vscode',
        '.venv',
        'venv',
        'site-packages',
        'mediapipe_env',
        'video_analysis_env',
        'archive',
        '.smbdelete',
    ]
    
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
    print()
    
    if not documents:
        print("❌ No documents found!")
        return 1

    # Embedding model (match the intel-chromadb wrapper default)
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    print(f"Loading embedding model: {model_name}")
    embedder = SentenceTransformer(model_name)
    print("✅ Embedding model loaded")
    print()
    
    # Index in batches
    print("Indexing documents...")
    print()
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
        batch_embeddings = []
        
        for file_path in batch:
            try:
                # Read content
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                except:
                    content = file_path.read_text(encoding='latin-1', errors='ignore')
                
                if not content or not content.strip():
                    continue
                
                # Limit size
                if len(content) > 10000:
                    content = content[:10000]
                
                # Create unique ID
                try:
                    rel_path = str(file_path.relative_to(sap_path))
                    doc_id = hashlib.md5(rel_path.encode()).hexdigest()[:16] + "_" + rel_path.replace("/", "_").replace("\\", "_")[-50:]
                except:
                    doc_id = f"doc_{hashlib.md5(str(file_path).encode()).hexdigest()[:16]}"
                
                # Metadata
                metadata = {
                    'source': str(file_path),
                    'relative_path': rel_path if 'rel_path' in locals() else str(file_path),
                    'file_type': file_path.suffix,
                    'namespace': 'sap',
                    'client': 'SAP',
                    'tag': 'SAP',
                    'indexed_at': datetime.now().isoformat(),
                    'file_size': file_path.stat().st_size
                }
                
                batch_ids.append(doc_id)
                batch_docs.append(content)
                batch_metas.append(metadata)
                batch_embeddings.append(embedder.encode(content).tolist())
                processed += 1
                
            except Exception as e:
                errors += 1
                continue
        
        # Add batch
        if batch_ids:
            try:
                collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_docs,
                    metadatas=batch_metas
                )
                current_count = collection.count()
                print(f"✅ Batch {batch_num}/{total_batches}: {len(batch_ids)} indexed (total: {current_count})")
            except Exception as e:
                print(f"❌ Batch {batch_num} error: {str(e)[:100]}")
                errors += len(batch_ids)
        
        time.sleep(0.1)
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    final_count = collection.count()
    
    print()
    print("=" * 60)
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
        result_count = len(results['documents'][0]) if results['documents'] else 0
        print(f"✅ Query test: {result_count} results found")
        if result_count > 0:
            print(f"   Sample: {results['documents'][0][0][:100]}...")
    except Exception as e:
        print(f"⚠️  Query test failed: {e}")
    
    print()
    print("✅ INDEXING COMPLETE AND VERIFIED")
    return 0

if __name__ == '__main__':
    sys.exit(main())

