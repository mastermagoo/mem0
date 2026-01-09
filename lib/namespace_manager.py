"""
Namespace Manager - Multi-Context Memory Isolation
Location: /Volumes/intel-system/deployment/docker/mem0_tailscale/namespace_manager.py
Purpose: Thread-safe namespace context management for isolated memory contexts
Scope: Provides namespace switching, validation, and context management for 5 life contexts
"""

import threading
from contextlib import contextmanager
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class NamespaceConfig:
    """Configuration for a single namespace"""
    name: str
    description: str
    use_cases: List[str]
    retention_days: int  # -1 for indefinite
    sensitivity: str  # LOW, MEDIUM, HIGH, HIGHEST


class NamespaceRegistry:
    """
    Registry of all available namespaces with their configurations.
    This is the single source of truth for namespace definitions.
    """

    NAMESPACES: Dict[str, NamespaceConfig] = {
        'progressief': NamespaceConfig(
            name='progressief',
            description='Progressief B.V. consulting business',
            use_cases=[
                'Client meetings and project notes',
                'Business development activities',
                'Consulting deliverables and proposals',
                'Company administration'
            ],
            retention_days=365 * 7,  # 7 years for business records
            sensitivity='HIGH'
        ),
        'cv_automation': NamespaceConfig(
            name='cv_automation',
            description='Job search and CV generation',
            use_cases=[
                'Job applications and tracking',
                'Interview notes and feedback',
                'CV customization context',
                'Recruiter interactions'
            ],
            retention_days=365 * 2,  # 2 years
            sensitivity='MEDIUM'
        ),
        'investments': NamespaceConfig(
            name='investments',
            description='Investment tracking and analysis',
            use_cases=[
                'Portfolio decisions and rationale',
                'Market research and analysis',
                'Financial planning notes',
                'Investment thesis development'
            ],
            retention_days=365 * 10,  # 10 years for financial records
            sensitivity='HIGH'
        ),
        'personal': NamespaceConfig(
            name='personal',
            description='Personal life, family, health',
            use_cases=[
                'Family events and planning',
                'Health tracking and medical notes',
                'Personal goals and reflections',
                'Relationship management'
            ],
            retention_days=-1,  # Indefinite
            sensitivity='HIGHEST'
        ),
        'intel_system': NamespaceConfig(
            name='intel_system',
            description='Infrastructure and technical projects',
            use_cases=[
                'System architecture decisions',
                'Technical troubleshooting notes',
                'Infrastructure changes and rationale',
                'Development project context'
            ],
            retention_days=365 * 3,  # 3 years
            sensitivity='MEDIUM'
        )
    }

    @classmethod
    def get_all_namespaces(cls) -> List[str]:
        """Get list of all valid namespace names"""
        return list(cls.NAMESPACES.keys())

    @classmethod
    def get_namespace_config(cls, namespace: str) -> Optional[NamespaceConfig]:
        """Get configuration for a specific namespace"""
        return cls.NAMESPACES.get(namespace)

    @classmethod
    def is_valid_namespace(cls, namespace: str) -> bool:
        """Check if namespace is valid"""
        return namespace in cls.NAMESPACES

    @classmethod
    def get_namespace_info(cls, namespace: str) -> Dict:
        """Get detailed information about a namespace"""
        config = cls.get_namespace_config(namespace)
        if not config:
            return {}

        return {
            'name': config.name,
            'description': config.description,
            'use_cases': config.use_cases,
            'retention_policy': 'indefinite' if config.retention_days == -1
                               else f'{config.retention_days // 365} years',
            'sensitivity': config.sensitivity
        }


class NamespaceContext:
    """
    Thread-safe namespace context manager.
    Manages current namespace per thread and provides context switching.
    """

    _local = threading.local()
    _lock = threading.Lock()
    _access_log: List[Dict] = []

    # Default namespace for new threads
    DEFAULT_NAMESPACE = 'personal'

    @classmethod
    def set_namespace(cls, namespace: str) -> None:
        """
        Set current namespace for the current thread.

        Args:
            namespace: Namespace name to switch to

        Raises:
            ValueError: If namespace is not valid
        """
        if not NamespaceRegistry.is_valid_namespace(namespace):
            raise ValueError(
                f"Invalid namespace: {namespace}. "
                f"Valid namespaces: {NamespaceRegistry.get_all_namespaces()}"
            )

        previous = cls.get_namespace()
        cls._local.namespace = namespace

        # Log namespace switch
        cls._log_access(
            action='switch',
            from_namespace=previous,
            to_namespace=namespace
        )

        logger.info(f"Namespace switched: {previous} -> {namespace}")

    @classmethod
    def get_namespace(cls) -> str:
        """
        Get current namespace for the current thread.
        Returns default namespace if none is set.

        Returns:
            Current namespace name
        """
        return getattr(cls._local, 'namespace', cls.DEFAULT_NAMESPACE)

    @classmethod
    def get_namespace_config(cls) -> NamespaceConfig:
        """Get configuration for current namespace"""
        namespace = cls.get_namespace()
        return NamespaceRegistry.get_namespace_config(namespace)

    @classmethod
    @contextmanager
    def use_namespace(cls, namespace: str):
        """
        Context manager for temporary namespace switch.
        Automatically restores previous namespace on exit.

        Usage:
            with NamespaceContext.use_namespace('progressief'):
                # All operations use 'progressief' namespace
                memory.add("Client meeting notes")

        Args:
            namespace: Namespace to temporarily switch to

        Yields:
            The namespace name that was switched to
        """
        previous = cls.get_namespace()
        try:
            cls.set_namespace(namespace)
            yield namespace
        finally:
            # Restore previous namespace
            cls._local.namespace = previous
            logger.debug(f"Restored namespace: {previous}")

    @classmethod
    def format_user_id(cls, base_user_id: str, namespace: Optional[str] = None) -> str:
        """
        Format user ID with namespace prefix.

        Args:
            base_user_id: Base user identifier (e.g., 'mark_carey')
            namespace: Namespace to use (defaults to current)

        Returns:
            Formatted user ID: 'base_user_id/namespace'
        """
        ns = namespace or cls.get_namespace()
        return f"{base_user_id}/{ns}"

    @classmethod
    def parse_user_id(cls, user_id: str) -> tuple[str, str]:
        """
        Parse namespaced user ID into base user and namespace.

        Args:
            user_id: Formatted user ID ('base_user/namespace')

        Returns:
            Tuple of (base_user_id, namespace)

        Raises:
            ValueError: If user_id format is invalid
        """
        parts = user_id.split('/', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid user_id format: {user_id}. Expected 'user/namespace'")

        base_user, namespace = parts
        if not NamespaceRegistry.is_valid_namespace(namespace):
            raise ValueError(f"Invalid namespace in user_id: {namespace}")

        return base_user, namespace

    @classmethod
    def _log_access(cls, action: str, **kwargs) -> None:
        """Log namespace access for audit purposes"""
        with cls._lock:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'action': action,
                'thread_id': threading.get_ident(),
                **kwargs
            }
            cls._access_log.append(log_entry)

            # Keep only last 1000 entries
            if len(cls._access_log) > 1000:
                cls._access_log = cls._access_log[-1000:]

    @classmethod
    def get_access_log(cls, limit: int = 100) -> List[Dict]:
        """Get recent namespace access log entries"""
        with cls._lock:
            return cls._access_log[-limit:]

    @classmethod
    def clear_access_log(cls) -> None:
        """Clear access log (for testing)"""
        with cls._lock:
            cls._access_log.clear()


class NamespaceValidator:
    """Validation utilities for namespace operations"""

    @staticmethod
    def validate_namespace_access(user_id: str, namespace: str) -> bool:
        """
        Validate that user has access to namespace.
        Currently allows all access - extend for multi-user scenarios.

        Args:
            user_id: User identifier
            namespace: Namespace to access

        Returns:
            True if access is allowed, False otherwise
        """
        # Parse user_id to get base user
        try:
            base_user, _ = NamespaceContext.parse_user_id(user_id)
        except ValueError:
            # If user_id doesn't contain namespace, use it as-is
            base_user = user_id

        # For now, all users can access all namespaces
        # In multi-user scenario, implement access control here
        return NamespaceRegistry.is_valid_namespace(namespace)

    @staticmethod
    def validate_memory_namespace(memory_namespace: str, expected_namespace: str) -> bool:
        """
        Validate that memory belongs to expected namespace.

        Args:
            memory_namespace: Namespace stored in memory
            expected_namespace: Namespace expected for current context

        Returns:
            True if namespaces match, False otherwise
        """
        return memory_namespace == expected_namespace

    @staticmethod
    def get_retention_cutoff(namespace: str) -> Optional[datetime]:
        """
        Get retention cutoff date for namespace.

        Args:
            namespace: Namespace to check

        Returns:
            Cutoff datetime before which memories should be deleted,
            or None if retention is indefinite
        """
        config = NamespaceRegistry.get_namespace_config(namespace)
        if not config or config.retention_days == -1:
            return None

        return datetime.utcnow() - timedelta(days=config.retention_days)


class NamespaceStats:
    """Statistics and monitoring for namespace usage"""

    def __init__(self, db_connection=None):
        """
        Initialize namespace stats collector.

        Args:
            db_connection: Database connection for querying stats
        """
        self.db = db_connection

    def get_namespace_memory_counts(self) -> Dict[str, int]:
        """
        Get memory count for each namespace.

        Returns:
            Dict mapping namespace to memory count
        """
        # This would query the database
        # For now, return placeholder
        return {ns: 0 for ns in NamespaceRegistry.get_all_namespaces()}

    def get_namespace_storage_size(self) -> Dict[str, int]:
        """
        Get storage size (bytes) for each namespace.

        Returns:
            Dict mapping namespace to storage size in bytes
        """
        # This would query the database
        return {ns: 0 for ns in NamespaceRegistry.get_all_namespaces()}

    def get_namespace_activity(self, days: int = 7) -> Dict[str, int]:
        """
        Get memory addition activity for each namespace.

        Args:
            days: Number of days to look back

        Returns:
            Dict mapping namespace to number of memories added in timeframe
        """
        # This would query the database with timestamp filtering
        return {ns: 0 for ns in NamespaceRegistry.get_all_namespaces()}


# Convenience functions for common operations
def get_current_namespace() -> str:
    """Get the current namespace"""
    return NamespaceContext.get_namespace()


def switch_namespace(namespace: str) -> None:
    """Switch to a different namespace"""
    NamespaceContext.set_namespace(namespace)


def list_namespaces() -> List[str]:
    """List all available namespaces"""
    return NamespaceRegistry.get_all_namespaces()


def get_namespace_details(namespace: str) -> Dict:
    """Get detailed information about a namespace"""
    return NamespaceRegistry.get_namespace_info(namespace)


# Example usage
if __name__ == '__main__':
    print("Namespace Manager - Example Usage\n")

    # List all namespaces
    print("Available namespaces:")
    for ns in list_namespaces():
        info = get_namespace_details(ns)
        print(f"  - {ns}: {info['description']}")

    print("\n" + "="*60 + "\n")

    # Default namespace
    print(f"Current namespace: {get_current_namespace()}")

    # Switch namespace
    print("\nSwitching to 'progressief'...")
    switch_namespace('progressief')
    print(f"Current namespace: {get_current_namespace()}")

    # Use context manager
    print("\nUsing context manager for 'cv_automation'...")
    with NamespaceContext.use_namespace('cv_automation'):
        print(f"  Inside context: {get_current_namespace()}")
        # Operations here use cv_automation namespace

    print(f"After context: {get_current_namespace()}")

    # Format user ID
    print("\n" + "="*60 + "\n")
    user_id = NamespaceContext.format_user_id('mark_carey', 'investments')
    print(f"Formatted user_id: {user_id}")

    # Parse user ID
    base_user, namespace = NamespaceContext.parse_user_id(user_id)
    print(f"Parsed: base_user='{base_user}', namespace='{namespace}'")

    # Namespace info
    print("\n" + "="*60 + "\n")
    print("Namespace: progressief")
    info = get_namespace_details('progressief')
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Access log
    print("\n" + "="*60 + "\n")
    print("Recent namespace access:")
    for entry in NamespaceContext.get_access_log(limit=5):
        print(f"  {entry['timestamp']}: {entry['action']} "
              f"({entry.get('from_namespace', 'N/A')} -> {entry.get('to_namespace', 'N/A')})")
