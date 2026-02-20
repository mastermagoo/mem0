#!/usr/bin/env python3
"""
RAG Demo for Tomorrow's SAP Work
Shows how RAG can improve productivity during Friday meeting prep
"""

import requests
import json
from datetime import datetime

RAG_URL = "http://localhost:8020"

def query_rag(query: str, k: int = 5, threshold: float = 0.7):
    """Query RAG pipeline for SAP documents."""
    try:
        response = requests.post(
            f"{RAG_URL}/rag/query",
            json={
                "query": query,
                "k": k,
                "threshold": threshold,
                "include_metadata": True
            },
            timeout=15
        )
        
        if response.status_code != 200:
            return None, f"Error {response.status_code}: {response.text[:200]}"
        
        return response.json(), None
        
    except Exception as e:
        return None, str(e)

def format_result(data, query):
    """Format RAG results for display."""
    if not data:
        return "No results"
    
    results = data.get("results", [])
    context = data.get("context", "")
    
    output = [f"\n{'='*70}"]
    output.append(f"🔍 Query: {query}")
    output.append(f"{'='*70}\n")
    
    if context:
        output.append(f"📄 Context:\n{context[:500]}...\n")
    
    if not results:
        output.append("❌ No documents found matching your query.")
        return "\n".join(output)
    
    output.append(f"✅ Found {len(results)} relevant documents:\n")
    
    for i, result in enumerate(results[:5], 1):
        content = result.get("content", result.get("document", ""))[:400]
        metadata = result.get("metadata", {})
        score = result.get("score", 0)
        source = metadata.get("source", metadata.get("relative_path", "Unknown"))
        
        output.append(f"\n{i}. [Score: {score:.3f}]")
        output.append(f"   {content}...")
        if source and source != "Unknown":
            output.append(f"   📄 Source: {source}")
    
    return "\n".join(output)

def main():
    """Run RAG demo queries for tomorrow's work."""
    
    print("\n" + "="*70)
    print("🚀 RAG PRODUCTIVITY DEMO - Tomorrow's SAP Work")
    print("="*70)
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🎯 Purpose: Show how RAG improves Friday meeting prep\n")
    
    # Check RAG service health
    print("🔍 Checking RAG service...")
    try:
        health = requests.get(f"{RAG_URL}/rag/stats", timeout=5)
        if health.status_code == 200:
            print("✅ RAG service is running\n")
        else:
            print(f"⚠️  RAG service returned {health.status_code}\n")
    except Exception as e:
        print(f"❌ Cannot connect to RAG service: {e}")
        print(f"   Make sure RAG pipeline is running on {RAG_URL}\n")
        return
    
    # Tomorrow's key queries based on Friday crib sheet
    queries = [
        # Performance investigation queries
        "What did Oliver say about performance priorities and delays?",
        "What is the status of INC17051865 and performance investigation?",
        "What evidence exists about the 40-45 second delay vs 6-7 second baseline?",
        
        # Technical context queries
        "What are the findings about AI Core infrastructure and token acquisition?",
        "What did Marius and Siva say about logging and testing?",
        "What are the current blockers and risks for CR143?",
        
        # Stakeholder intelligence
        "What do we know about Marius, Siva, and Amar's roles and concerns?",
        "What are the key decisions and actions from recent meetings?",
    ]
    
    print("📋 Running queries relevant to tomorrow's Friday meeting...\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'─'*70}")
        print(f"Query {i}/{len(queries)}")
        print(f"{'─'*70}")
        
        data, error = query_rag(query, k=5, threshold=0.6)
        
        if error:
            print(f"❌ Error: {error}")
            continue
        
        result = format_result(data, query)
        print(result)
        
        # Pause between queries for readability
        if i < len(queries):
            input("\n⏸️  Press Enter to continue to next query...")
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETE")
    print("="*70)
    print("\n💡 How RAG helps tomorrow:")
    print("   • Instant answers to meeting prep questions")
    print("   • Find relevant context without manual searching")
    print("   • Get stakeholder intelligence on demand")
    print("   • Access 705 indexed documents in seconds")
    print("\n🚀 Ready for productive Friday meeting prep!\n")

if __name__ == "__main__":
    main()

