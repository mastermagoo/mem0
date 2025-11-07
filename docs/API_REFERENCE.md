# mem0 API Reference

**Version**: 2.0 (Local Neo4j with GDS Plugin)  
**Base URL**: http://localhost:8888  
**Date**: 2025-10-21

## 🎯 Overview

The mem0 API provides endpoints for creating, retrieving, and managing personal AI memories with graph-based knowledge storage.

## 🔗 Base Information

- **Base URL**: `http://localhost:8888`
- **API Documentation**: `http://localhost:8888/docs`
- **Authentication**: API Key required
- **Content Type**: `application/json`

## 📋 Authentication

### API Key
All requests require the `MEM0_API_KEY` header:

```bash
curl -H "MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d" \
     http://localhost:8888/memories
```

## 🚀 Core Endpoints

### 1. Create Memory

**POST** `/memories`

Creates a new memory from user messages.

#### Request Body
```json
{
  "messages": [
    {
      "role": "user",
      "content": "I learned that Python is great for data science"
    }
  ],
  "user_id": "user123",
  "namespace": "personal"
}
```

#### Parameters
- `messages` (array): List of message objects
- `user_id` (string): Unique user identifier
- `namespace` (string, optional): Memory namespace (default: "personal")

#### Response
```json
{
  "results": [
    {
      "id": "memory_123",
      "content": "Python is great for data science",
      "embedding": [0.1, 0.2, 0.3, ...],
      "metadata": {
        "created_at": "2025-10-21T12:00:00Z",
        "user_id": "user123",
        "namespace": "personal"
      }
    }
  ],
  "relations": {
    "added_entities": [
      [
        {
          "source": "user_id:user123",
          "relationship": "learned_about",
          "target": "python"
        },
        {
          "source": "python",
          "relationship": "is_good_for",
          "target": "data_science"
        }
      ]
    ],
    "deleted_entities": []
  }
}
```

#### Example
```bash
curl -X POST http://localhost:8888/memories \
  -H 'Content-Type: application/json' \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d' \
  -d '{
    "messages": [
      {"role": "user", "content": "I learned that Python is great for data science"}
    ],
    "user_id": "user123"
  }'
```

### 2. Retrieve Memories

**GET** `/memories`

Retrieves memories for a specific user.

#### Query Parameters
- `user_id` (string): User identifier
- `namespace` (string, optional): Memory namespace
- `limit` (integer, optional): Maximum number of memories to return
- `offset` (integer, optional): Number of memories to skip

#### Response
```json
{
  "results": [
    {
      "id": "memory_123",
      "content": "Python is great for data science",
      "embedding": [0.1, 0.2, 0.3, ...],
      "metadata": {
        "created_at": "2025-10-21T12:00:00Z",
        "user_id": "user123",
        "namespace": "personal"
      }
    }
  ],
  "total": 1
}
```

#### Example
```bash
curl "http://localhost:8888/memories?user_id=user123&limit=10" \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d'
```

### 3. Search Memories

**POST** `/memories/search`

Searches memories using semantic similarity.

#### Request Body
```json
{
  "query": "What did I learn about Python?",
  "user_id": "user123",
  "namespace": "personal",
  "limit": 5
}
```

#### Parameters
- `query` (string): Search query
- `user_id` (string): User identifier
- `namespace` (string, optional): Memory namespace
- `limit` (integer, optional): Maximum results to return

#### Response
```json
{
  "results": [
    {
      "id": "memory_123",
      "content": "Python is great for data science",
      "similarity": 0.95,
      "metadata": {
        "created_at": "2025-10-21T12:00:00Z",
        "user_id": "user123",
        "namespace": "personal"
      }
    }
  ]
}
```

#### Example
```bash
curl -X POST http://localhost:8888/memories/search \
  -H 'Content-Type: application/json' \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d' \
  -d '{
    "query": "What did I learn about Python?",
    "user_id": "user123",
    "limit": 5
  }'
```

### 4. Update Memory

**PUT** `/memories/{memory_id}`

Updates an existing memory.

#### Request Body
```json
{
  "content": "Updated content about Python",
  "metadata": {
    "tags": ["programming", "python", "data-science"]
  }
}
```

#### Response
```json
{
  "id": "memory_123",
  "content": "Updated content about Python",
  "metadata": {
    "created_at": "2025-10-21T12:00:00Z",
    "updated_at": "2025-10-21T12:30:00Z",
    "user_id": "user123",
    "namespace": "personal",
    "tags": ["programming", "python", "data-science"]
  }
}
```

#### Example
```bash
curl -X PUT http://localhost:8888/memories/memory_123 \
  -H 'Content-Type: application/json' \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d' \
  -d '{
    "content": "Updated content about Python",
    "metadata": {
      "tags": ["programming", "python", "data-science"]
    }
  }'
```

### 5. Delete Memory

**DELETE** `/memories/{memory_id}`

Deletes a specific memory.

#### Response
```json
{
  "message": "Memory deleted successfully",
  "id": "memory_123"
}
```

#### Example
```bash
curl -X DELETE http://localhost:8888/memories/memory_123 \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d'
```

## 🔍 Graph Endpoints

### 1. Get Knowledge Graph

**GET** `/graph`

Retrieves the knowledge graph for a user.

#### Query Parameters
- `user_id` (string): User identifier
- `namespace` (string, optional): Memory namespace
- `depth` (integer, optional): Graph traversal depth

#### Response
```json
{
  "nodes": [
    {
      "id": "python",
      "label": "Python",
      "type": "concept",
      "properties": {
        "frequency": 5,
        "first_mentioned": "2025-10-21T12:00:00Z"
      }
    },
    {
      "id": "data_science",
      "label": "Data Science",
      "type": "concept",
      "properties": {
        "frequency": 3,
        "first_mentioned": "2025-10-21T12:05:00Z"
      }
    }
  ],
  "relationships": [
    {
      "id": "rel_1",
      "source": "python",
      "target": "data_science",
      "type": "is_good_for",
      "properties": {
        "confidence": 0.95,
        "created_at": "2025-10-21T12:00:00Z"
      }
    }
  ]
}
```

#### Example
```bash
curl "http://localhost:8888/graph?user_id=user123&depth=2" \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d'
```

### 2. Get Related Concepts

**GET** `/graph/related/{concept}`

Gets concepts related to a specific concept.

#### Parameters
- `concept` (string): Concept identifier
- `user_id` (string): User identifier
- `limit` (integer, optional): Maximum related concepts

#### Response
```json
{
  "concept": "python",
  "related": [
    {
      "concept": "data_science",
      "relationship": "is_good_for",
      "confidence": 0.95
    },
    {
      "concept": "programming",
      "relationship": "is_a",
      "confidence": 0.90
    }
  ]
}
```

#### Example
```bash
curl "http://localhost:8888/graph/related/python?user_id=user123" \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d'
```

## 📊 Analytics Endpoints

### 1. Get Memory Statistics

**GET** `/analytics/stats`

Gets memory statistics for a user.

#### Query Parameters
- `user_id` (string): User identifier
- `namespace` (string, optional): Memory namespace
- `timeframe` (string, optional): Time period (day, week, month, year)

#### Response
```json
{
  "user_id": "user123",
  "total_memories": 150,
  "total_concepts": 45,
  "total_relationships": 120,
  "timeframe": "month",
  "period_stats": {
    "memories_created": 25,
    "concepts_added": 8,
    "relationships_created": 18
  },
  "top_concepts": [
    {"concept": "python", "frequency": 15},
    {"concept": "data_science", "frequency": 12},
    {"concept": "machine_learning", "frequency": 8}
  ]
}
```

#### Example
```bash
curl "http://localhost:8888/analytics/stats?user_id=user123&timeframe=month" \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d'
```

### 2. Get Learning Insights

**GET** `/analytics/insights`

Gets learning insights and patterns.

#### Query Parameters
- `user_id` (string): User identifier
- `namespace` (string, optional): Memory namespace

#### Response
```json
{
  "user_id": "user123",
  "insights": [
    {
      "type": "learning_pattern",
      "description": "You learn most about programming concepts in the morning",
      "confidence": 0.85,
      "data": {
        "peak_hours": ["09:00", "10:00", "11:00"],
        "concept_type": "programming"
      }
    },
    {
      "type": "knowledge_gap",
      "description": "You have limited knowledge about machine learning algorithms",
      "confidence": 0.70,
      "data": {
        "missing_concepts": ["neural_networks", "deep_learning", "reinforcement_learning"]
      }
    }
  ]
}
```

#### Example
```bash
curl "http://localhost:8888/analytics/insights?user_id=user123" \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d'
```

## 🔧 Health & Status Endpoints

### 1. Health Check

**GET** `/health`

Checks the health of the mem0 service.

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T12:00:00Z",
  "services": {
    "postgres": "healthy",
    "neo4j": "healthy",
    "gds_plugin": "healthy"
  },
  "version": "2.0"
}
```

#### Example
```bash
curl http://localhost:8888/health
```

### 2. Service Status

**GET** `/status`

Gets detailed service status information.

#### Response
```json
{
  "mem0": {
    "status": "running",
    "version": "2.0",
    "uptime": "2h 30m"
  },
  "postgres": {
    "status": "connected",
    "version": "17.0",
    "database": "mem0",
    "connections": 5
  },
  "neo4j": {
    "status": "connected",
    "version": "5.13.0",
    "gds_version": "2.6.9",
    "database": "neo4j"
  }
}
```

#### Example
```bash
curl http://localhost:8888/status
```

## 🚨 Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "MEMORY_NOT_FOUND",
    "message": "Memory with ID 'memory_123' not found",
    "details": {
      "memory_id": "memory_123",
      "user_id": "user123"
    },
    "timestamp": "2025-10-21T12:00:00Z"
  }
}
```

### Common Error Codes
- `INVALID_API_KEY`: API key is missing or invalid
- `MEMORY_NOT_FOUND`: Requested memory does not exist
- `USER_NOT_FOUND`: User ID not found
- `INVALID_REQUEST`: Request body is malformed
- `SERVICE_UNAVAILABLE`: Backend service is down
- `RATE_LIMIT_EXCEEDED`: Too many requests

### HTTP Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

## 📝 Examples

### Complete Workflow Example

```bash
# 1. Create a memory
curl -X POST http://localhost:8888/memories \
  -H 'Content-Type: application/json' \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d' \
  -d '{
    "messages": [
      {"role": "user", "content": "I learned that Python is great for data science and machine learning"}
    ],
    "user_id": "user123"
  }'

# 2. Search for related memories
curl -X POST http://localhost:8888/memories/search \
  -H 'Content-Type: application/json' \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d' \
  -d '{
    "query": "What do I know about Python?",
    "user_id": "user123",
    "limit": 5
  }'

# 3. Get knowledge graph
curl "http://localhost:8888/graph?user_id=user123" \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d'

# 4. Get analytics
curl "http://localhost:8888/analytics/stats?user_id=user123" \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d'
```

## 🔗 Integration Examples

### Python Client
```python
import requests

class Mem0Client:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'MEM0_API_KEY': api_key
        }
    
    def create_memory(self, messages, user_id, namespace="personal"):
        response = requests.post(
            f"{self.base_url}/memories",
            headers=self.headers,
            json={
                "messages": messages,
                "user_id": user_id,
                "namespace": namespace
            }
        )
        return response.json()
    
    def search_memories(self, query, user_id, limit=10):
        response = requests.post(
            f"{self.base_url}/memories/search",
            headers=self.headers,
            json={
                "query": query,
                "user_id": user_id,
                "limit": limit
            }
        )
        return response.json()

# Usage
client = Mem0Client("http://localhost:8888", "mem0-b0539021-c9a6-4aaa-9193-665f63851a0d")
result = client.create_memory(
    messages=[{"role": "user", "content": "Python is great for data science"}],
    user_id="user123"
)
```

### JavaScript Client
```javascript
class Mem0Client {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json',
            'MEM0_API_KEY': apiKey
        };
    }
    
    async createMemory(messages, userId, namespace = 'personal') {
        const response = await fetch(`${this.baseUrl}/memories`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                messages,
                user_id: userId,
                namespace
            })
        });
        return response.json();
    }
    
    async searchMemories(query, userId, limit = 10) {
        const response = await fetch(`${this.baseUrl}/memories/search`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                query,
                user_id: userId,
                limit
            })
        });
        return response.json();
    }
}

// Usage
const client = new Mem0Client('http://localhost:8888', 'mem0-b0539021-c9a6-4aaa-9193-665f63851a0d');
const result = await client.createMemory(
    [{role: 'user', content: 'Python is great for data science'}],
    'user123'
);
```

---

**✅ mem0 API Reference**  
**Last Updated**: 2025-10-21  
**Version**: 2.0 (Local Neo4j with GDS Plugin)
