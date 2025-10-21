"""
Configuration management for mem0 Telegram bot
Loads environment variables and provides typed configuration
"""
import os
from typing import Optional

class Config:
    """Bot configuration from environment variables"""

    def __init__(self):
        # Telegram configuration
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        # mem0 API configuration
        self.mem0_url = os.getenv('MEM0_URL', 'http://mem0_server:8888')
        self.mem0_api_key = os.getenv('MEM0_API_KEY')

        # Bot behavior
        self.default_namespace = os.getenv('DEFAULT_NAMESPACE', 'personal')
        self.max_recall_results = int(os.getenv('MAX_RECALL_RESULTS', '5'))
        self.response_timeout = int(os.getenv('RESPONSE_TIMEOUT', '10'))

        # User identification (for single-user deployment)
        self.user_prefix = os.getenv('USER_PREFIX', 'mark_carey')

        # Available namespaces (can be expanded)
        self.namespaces = [
            'personal',
            'progressief',
            'cv_automation',
            'investments',
            'intel_system',
            'ai_projects',
            'vectal'
        ]

    def get_full_user_id(self, namespace: str) -> str:
        """Construct full user ID for mem0 with namespace"""
        return f"{self.user_prefix}/{namespace}"

# Global config instance
config = Config()
