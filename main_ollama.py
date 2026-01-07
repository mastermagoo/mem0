"""
mem0 API Server - Environment-Variable Driven Configuration
============================================================
Permanent fix: Reads LLM and embedder provider from environment variables.
Defaults to Ollama (not OpenAI) when not specified.

Created: 2026-01-07
Purpose: Strategic permanent fix for Ollama-only operation
Approved: User explicit approval via Wingman oversight
"""
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from mem0 import Memory

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_COLLECTION_NAME = os.environ.get("POSTGRES_COLLECTION_NAME", "memories")

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "mem0graph")

HISTORY_DB_PATH = os.environ.get("HISTORY_DB_PATH", "/app/history/history.db")

# =============================================================================
# LLM/EMBEDDER PROVIDER CONFIGURATION (Environment-Driven)
# =============================================================================
# Provider selection - defaults to Ollama (NOT OpenAI)
LLM_PROVIDER = os.environ.get("MEM0_LLM_PROVIDER", "ollama")
EMBEDDER_PROVIDER = os.environ.get("MEM0_EMBEDDER_PROVIDER", "ollama")

# Ollama configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
LLM_MODEL = os.environ.get("MEM0_LLM_MODEL", "mistral:7b-instruct-q5_K_M")
EMBEDDER_MODEL = os.environ.get("MEM0_EMBEDDER_MODEL", "nomic-embed-text:latest")

# OpenAI configuration (only used if provider explicitly set to openai)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_LLM_MODEL = os.environ.get("OPENAI_LLM_MODEL", "gpt-4o")
OPENAI_EMBEDDER_MODEL = os.environ.get("OPENAI_EMBEDDER_MODEL", "text-embedding-3-small")


def build_config() -> Dict:
    """
    Build mem0 configuration based on environment variables.
    Defaults to Ollama for both LLM and embedder.
    """
    # Build LLM config based on provider
    if LLM_PROVIDER.lower() == "ollama":
        llm_config = {
            "provider": "ollama",
            "config": {
                "model": LLM_MODEL,
                "ollama_base_url": OLLAMA_URL,
                "temperature": 0.3,
                "max_tokens": 1500,
            }
        }
        logging.info(f"LLM: Using Ollama provider with model {LLM_MODEL}")
    else:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required when MEM0_LLM_PROVIDER=openai")
        llm_config = {
            "provider": "openai",
            "config": {
                "api_key": OPENAI_API_KEY,
                "temperature": 0.2,
                "model": OPENAI_LLM_MODEL,
            }
        }
        logging.info(f"LLM: Using OpenAI provider with model {OPENAI_LLM_MODEL}")
    
    # Build embedder config based on provider
    if EMBEDDER_PROVIDER.lower() == "ollama":
        embedder_config = {
            "provider": "ollama",
            "config": {
                "model": EMBEDDER_MODEL,
                "ollama_base_url": OLLAMA_URL,
            }
        }
        logging.info(f"Embedder: Using Ollama provider with model {EMBEDDER_MODEL}")
    else:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required when MEM0_EMBEDDER_PROVIDER=openai")
        embedder_config = {
            "provider": "openai",
            "config": {
                "api_key": OPENAI_API_KEY,
                "model": OPENAI_EMBEDDER_MODEL,
            }
        }
        logging.info(f"Embedder: Using OpenAI provider with model {OPENAI_EMBEDDER_MODEL}")
    
    return {
        "version": "v1.1",
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "host": POSTGRES_HOST,
                "port": int(POSTGRES_PORT),
                "dbname": POSTGRES_DB,
                "user": POSTGRES_USER,
                "password": POSTGRES_PASSWORD,
                "collection_name": POSTGRES_COLLECTION_NAME,
            },
        },
        "graph_store": {
            "provider": "neo4j",
            "config": {
                "url": NEO4J_URI,
                "username": NEO4J_USERNAME,
                "password": NEO4J_PASSWORD,
            },
        },
        "llm": llm_config,
        "embedder": embedder_config,
        "history_db_path": HISTORY_DB_PATH,
    }


# =============================================================================
# INITIALIZATION
# =============================================================================
logging.info("=" * 60)
logging.info("mem0 Server Starting - Environment-Driven Configuration")
logging.info("=" * 60)
logging.info(f"LLM Provider: {LLM_PROVIDER}")
logging.info(f"Embedder Provider: {EMBEDDER_PROVIDER}")
if LLM_PROVIDER.lower() == "ollama":
    logging.info(f"Ollama URL: {OLLAMA_URL}")
    logging.info(f"LLM Model: {LLM_MODEL}")
    logging.info(f"Embedder Model: {EMBEDDER_MODEL}")
logging.info("=" * 60)

# Build config and initialize memory
DEFAULT_CONFIG = build_config()
MEMORY_INSTANCE = Memory.from_config(DEFAULT_CONFIG)

logging.info("mem0 Memory instance initialized successfully")

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================
app = FastAPI(
    title="Mem0 REST APIs",
    description="A REST API for managing and searching memories for your AI Agents and Apps.",
    version="1.0.0",
)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================
class Message(BaseModel):
    role: str = Field(..., description="Role of the message (user or assistant).")
    content: str = Field(..., description="Message content.")


class MemoryCreate(BaseModel):
    messages: List[Message] = Field(..., description="List of messages to store.")
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchQuery(BaseModel):
    query: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    limit: int = 10


class MemoryUpdate(BaseModel):
    data: str


# =============================================================================
# API ENDPOINTS
# =============================================================================
@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """Health check endpoint with provider information"""
    return {
        "status": "healthy",
        "llm_provider": LLM_PROVIDER,
        "embedder_provider": EMBEDDER_PROVIDER,
        "llm_model": LLM_MODEL if LLM_PROVIDER.lower() == "ollama" else OPENAI_LLM_MODEL,
        "embedder_model": EMBEDDER_MODEL if EMBEDDER_PROVIDER.lower() == "ollama" else OPENAI_EMBEDDER_MODEL,
    }


@app.get("/config")
async def get_config():
    """Get current configuration (without sensitive values)"""
    return {
        "llm_provider": LLM_PROVIDER,
        "llm_model": LLM_MODEL if LLM_PROVIDER.lower() == "ollama" else OPENAI_LLM_MODEL,
        "embedder_provider": EMBEDDER_PROVIDER,
        "embedder_model": EMBEDDER_MODEL if EMBEDDER_PROVIDER.lower() == "ollama" else OPENAI_EMBEDDER_MODEL,
        "ollama_url": OLLAMA_URL if LLM_PROVIDER.lower() == "ollama" else None,
        "vector_store": "pgvector",
        "graph_store": "neo4j",
    }


@app.post("/memories")
async def add_memory(memory: MemoryCreate):
    try:
        messages = [{"role": m.role, "content": m.content} for m in memory.messages]
        result = MEMORY_INSTANCE.add(
            messages,
            user_id=memory.user_id,
            agent_id=memory.agent_id,
            run_id=memory.run_id,
            metadata=memory.metadata,
        )
        return result
    except Exception as e:
        logging.error(f"Error adding memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories")
async def get_memories(
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    run_id: Optional[str] = None,
):
    try:
        result = MEMORY_INSTANCE.get_all(user_id=user_id, agent_id=agent_id, run_id=run_id)
        return {"memories": result}
    except Exception as e:
        logging.error(f"Error getting memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str):
    try:
        result = MEMORY_INSTANCE.get(memory_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/memories/{memory_id}")
async def update_memory(memory_id: str, memory: MemoryUpdate):
    try:
        result = MEMORY_INSTANCE.update(memory_id, memory.data)
        return result
    except Exception as e:
        logging.error(f"Error updating memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    try:
        MEMORY_INSTANCE.delete(memory_id)
        return {"status": "deleted", "memory_id": memory_id}
    except Exception as e:
        logging.error(f"Error deleting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search_memories(query: SearchQuery):
    try:
        result = MEMORY_INSTANCE.search(
            query.query,
            user_id=query.user_id,
            agent_id=query.agent_id,
            run_id=query.run_id,
            limit=query.limit,
        )
        return {"results": result}
    except Exception as e:
        logging.error(f"Error searching memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memories")
async def delete_all_memories(
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    run_id: Optional[str] = None,
):
    try:
        MEMORY_INSTANCE.delete_all(user_id=user_id, agent_id=agent_id, run_id=run_id)
        return {"status": "deleted"}
    except Exception as e:
        logging.error(f"Error deleting memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
async def reset():
    try:
        MEMORY_INSTANCE.reset()
        return {"status": "reset"}
    except Exception as e:
        logging.error(f"Error resetting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
