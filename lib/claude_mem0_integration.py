#!/usr/bin/env python3
"""
Claude Code + mem0 Integration
Automatically captures important information from conversations
"""

import os
import requests
import json
from datetime import datetime

class ClaudeMemory:
    def __init__(self):
        self.base_url = os.getenv("MEM0_URL", "http://127.0.0.1:8888")
        self.api_key = os.getenv("MEM0_API_KEY")
        if not self.api_key:
            raise ValueError("MEM0_API_KEY environment variable is required")
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.user_id = "mark_carey/intel_system"  # Default namespace

    def auto_store(self, content, namespace="intel_system", context=""):
        """
        Automatically store important information

        Args:
            content: The information to store
            namespace: Which namespace (personal, progressief, etc.)
            context: Additional context about why this is being stored
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Enrich content with context
        full_content = f"[{timestamp}] {content}"
        if context:
            full_content += f" (Context: {context})"

        try:
            response = requests.post(
                f"{self.base_url}/memories",
                json={
                    "messages": [{"role": "user", "content": full_content}],
                    "user_id": f"mark_carey/{namespace}"
                },
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                print(f"✅ Auto-stored in {namespace}: {content[:50]}...")
                return True
            else:
                print(f"⚠️ Storage failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error storing: {e}")
            return False

    def intelligent_extract(self, conversation_text):
        """
        Extract important information from conversation

        Looks for:
        - Decisions made
        - Action items
        - System configurations
        - Important findings
        - Preferences stated
        """

        important_patterns = [
            # Decisions
            ("decided to", "decision"),
            ("going with", "decision"),
            ("will use", "decision"),

            # Configurations
            ("configured", "configuration"),
            ("set to", "configuration"),
            ("port is", "configuration"),
            ("password is", "configuration"),

            # Actions
            ("need to", "action_item"),
            ("should", "action_item"),
            ("must", "action_item"),
            ("todo", "action_item"),

            # Findings
            ("discovered", "finding"),
            ("found that", "finding"),
            ("turns out", "finding"),
            ("issue is", "finding"),

            # Preferences
            ("prefer", "preference"),
            ("like", "preference"),
            ("want", "preference"),
        ]

        # Simple pattern matching (could be enhanced with LLM)
        extracted = []
        lines = conversation_text.split('\n')

        for line in lines:
            line_lower = line.lower()
            for pattern, category in important_patterns:
                if pattern in line_lower:
                    extracted.append({
                        "content": line.strip(),
                        "category": category
                    })
                    break

        return extracted

    def store_conversation_insights(self, conversation, namespace="intel_system"):
        """
        Analyze conversation and store important parts
        """
        insights = self.intelligent_extract(conversation)

        print(f"\n🧠 Analyzing conversation... found {len(insights)} important items")

        for insight in insights:
            self.auto_store(
                insight["content"],
                namespace=namespace,
                context=f"Auto-captured: {insight['category']}"
            )

        return len(insights)


# Quick usage functions
def store(text, namespace="personal"):
    """Quick store function"""
    mem = ClaudeMemory()
    return mem.auto_store(text, namespace)

def recall(query, namespace="personal"):
    """Quick recall function"""
    mem = ClaudeMemory()
    response = requests.get(
        f"{mem.base_url}/memories",
        params={"user_id": f"mark_carey/{namespace}", "query": query},
        headers=mem.headers
    )

    if response.status_code == 200:
        results = response.json()
        return results.get('results', [])
    return []


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python claude_mem0_integration.py store 'Your note' [namespace]")
        print("  python claude_mem0_integration.py recall 'search query' [namespace]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "store":
        text = sys.argv[2]
        namespace = sys.argv[3] if len(sys.argv) > 3 else "personal"
        store(text, namespace)

    elif command == "recall":
        query = sys.argv[2]
        namespace = sys.argv[3] if len(sys.argv) > 3 else "personal"
        results = recall(query, namespace)

        print(f"\n🔍 Found {len(results)} memories:\n")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. {result.get('memory', 'N/A')}\n")
