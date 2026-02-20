#!/usr/bin/env python3
"""
Simple RAG Query Helper for SAP Work
Usage: python3 rag_query.py "your question here"
"""

import requests
import json
import sys

RAG_URL = "http://localhost:8020"

def query(query_text, k=5, threshold=0.6):
    """Query RAG pipeline and display results."""
    try:
        response = requests.post(
            f"{RAG_URL}/rag/query",
            json={
                "query": query_text,
                "k": k,
                "threshold": threshold,
                "include_metadata": True
            },
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")
            return
        
        data = response.json()
        results = data.get("results", [])
        context = data.get("context", "")
        
        print(f"\n{'='*70}")
        print(f"🔍 Query: {query_text}")
        print(f"{'='*70}\n")
        
        if context:
            print(f"📄 Context:\n{context[:500]}...\n")
        
        if not results:
            print("❌ No documents found matching your query.")
            print("\n💡 Try:")
            print("   • Rephrasing your question")
            print("   • Using different keywords")
            print("   • Lowering threshold (currently 0.6)")
            return
        
        print(f"✅ Found {len(results)} relevant documents:\n")
        
        for i, result in enumerate(results, 1):
            content = result.get("content", result.get("document", ""))[:400]
            metadata = result.get("metadata", {})
            score = result.get("score", 0)
            source = metadata.get("source", metadata.get("relative_path", "Unknown"))
            
            print(f"{i}. [Score: {score:.3f}]")
            print(f"   {content}...")
            if source and source != "Unknown":
                print(f"   📄 Source: {source}")
            print()
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out. RAG service may be slow or unavailable.")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to RAG service at {RAG_URL}")
        print("   Make sure RAG pipeline is running:")
        print("   docker ps | grep rag-pipeline")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 rag_query.py 'your question here'")
        print("\nExamples:")
        print("  python3 rag_query.py 'What did Oliver say about performance?'")
        print("  python3 rag_query.py 'Status of INC17051865'")
        print("  python3 rag_query.py 'Marius logging findings'")
        sys.exit(1)
    
    query(" ".join(sys.argv[1:]))

