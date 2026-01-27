#!/usr/bin/env python3
"""
Direct re-embedding script - bypasses mem0 API to preserve all memories
Generates Ollama embeddings and inserts directly into PostgreSQL
"""
import psycopg
import requests
import json
import sys
from datetime import datetime

# Configuration
POSTGRES_HOST = "postgres"  # Docker network name
POSTGRES_PORT = 5432
POSTGRES_USER = "mem0_user_prd"
POSTGRES_DB = "mem0_prd"
POSTGRES_PASSWORD = "mem0PrdPassword2026SecureV2"  # From .env

OLLAMA_URL = "http://host.docker.internal:11434"  # Host machine Ollama
OLLAMA_MODEL = "nomic-embed-text:latest"

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def get_embedding(text):
    """Get embedding from Ollama"""
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": OLLAMA_MODEL, "prompt": text}
    )
    response.raise_for_status()
    return response.json()["embedding"]

def main():
    log("Starting direct re-embedding...")

    # Connect to database
    conn = psycopg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        dbname=POSTGRES_DB,
        password=POSTGRES_PASSWORD
    )

    log("Connected to database")

    # Get all memories
    with conn.cursor() as cur:
        cur.execute("SELECT id, payload FROM memories ORDER BY id")
        memories = cur.fetchall()

    total = len(memories)
    log(f"Found {total} memories to re-embed")

    # Drop and recreate table with 768 dims
    log("Dropping old table...")
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS memories CASCADE")
        conn.commit()

    log("Creating new table with 768 dimensions...")
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE memories (
                id UUID PRIMARY KEY,
                vector vector(768),
                payload JSONB
            )
        """)
        cur.execute("CREATE INDEX ON memories USING hnsw (vector vector_cosine_ops)")
        conn.commit()

    # Re-embed each memory
    processed = 0
    failed = 0

    for mem_id, payload in memories:
        processed += 1

        try:
            content = payload.get("data", "")
            if not content:
                log(f"[{processed}/{total}] Skipping {mem_id} (empty content)")
                continue

            # Generate embedding
            embedding = get_embedding(content)

            # Insert
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO memories (id, vector, payload) VALUES (%s, %s, %s)",
                    (mem_id, embedding, json.dumps(payload))
                )
            conn.commit()

            if processed % 10 == 0:
                log(f"[{processed}/{total}] Progress... (Failed: {failed})")

        except Exception as e:
            failed += 1
            log(f"[{processed}/{total}] FAILED {mem_id}: {e}")
            continue

    log(f"Re-embedding complete! Processed: {processed}, Failed: {failed}")

    # Verify count
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM memories")
        new_count = cur.fetchone()[0]

    log(f"Final count: {new_count}/{total}")
    conn.close()

if __name__ == "__main__":
    main()
