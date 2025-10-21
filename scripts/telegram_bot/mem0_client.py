"""
mem0 API client for Telegram bot
Handles all interactions with mem0 server
"""
import requests
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Mem0Client:
    """Client for interacting with mem0 server"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

        logger.info(f"Initialized mem0 client with base URL: {base_url}")

    def health_check(self) -> Dict[str, Any]:
        """Check if mem0 server is healthy"""
        try:
            response = requests.get(
                f"{self.base_url}/docs",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            return {'status': 'healthy'}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}

    def store_memory(self, user_id: str, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Store a new memory in mem0

        Args:
            user_id: Full user ID with namespace (e.g., "mark_carey/personal")
            content: Memory content to store
            metadata: Optional metadata to attach

        Returns:
            Response from mem0 server
        """
        try:
            payload = {
                "messages": [{"role": "user", "content": content}],
                "user_id": user_id
            }
            if metadata:
                payload['metadata'] = metadata

            logger.info(f"Storing memory for user_id: {user_id}")
            response = requests.post(
                f"{self.base_url}/memories",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Memory stored successfully: {result}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to store memory: {e}")
            raise Exception(f"Failed to store memory: {str(e)}")

    def search_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for memories matching a query

        Args:
            user_id: Full user ID with namespace
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching memories
        """
        try:
            logger.info(f"Searching memories for user_id: {user_id}, query: {query}")
            response = requests.get(
                f"{self.base_url}/memories",
                params={
                    "user_id": user_id,
                    "query": query,
                    "limit": limit
                },
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if isinstance(result, dict):
                memories = result.get('results', result.get('memories', []))
            else:
                memories = result

            logger.info(f"Found {len(memories)} memories")
            return memories
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to search memories: {e}")
            raise Exception(f"Failed to search memories: {str(e)}")

    def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all memories for a user_id (namespace)

        Args:
            user_id: Full user ID with namespace

        Returns:
            List of all memories
        """
        try:
            logger.info(f"Getting all memories for user_id: {user_id}")
            response = requests.get(
                f"{self.base_url}/memories",
                params={"user_id": user_id},
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if isinstance(result, dict):
                memories = result.get('results', result.get('memories', []))
            else:
                memories = result

            logger.info(f"Retrieved {len(memories)} total memories")
            return memories
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get memories: {e}")
            raise Exception(f"Failed to get memories: {str(e)}")

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory

        Args:
            memory_id: ID of memory to delete

        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting memory: {memory_id}")
            response = requests.delete(
                f"{self.base_url}/memories/{memory_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            logger.info("Memory deleted successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete memory: {e}")
            raise Exception(f"Failed to delete memory: {str(e)}")

    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics for a namespace

        Args:
            user_id: Full user ID with namespace

        Returns:
            Statistics dictionary
        """
        try:
            memories = self.get_all_memories(user_id)
            return {
                'total_memories': len(memories),
                'namespace': user_id.split('/')[-1]
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}
