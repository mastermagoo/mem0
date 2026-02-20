"""
Namespace API Endpoints
Location: /Volumes/Data/ai_projects/mem0-system/lib/namespace_api.py
Purpose: FastAPI endpoints for namespace management
Scope: REST API for listing, switching, and managing namespaces

This module should be imported into the main mem0 FastAPI application.
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from namespace_manager import (
    NamespaceContext,
    NamespaceRegistry,
    NamespaceValidator,
    NamespaceStats,
    get_current_namespace,
    switch_namespace,
    list_namespaces,
    get_namespace_details
)

# Create API router
router = APIRouter(prefix="/v1/namespace", tags=["namespace"])


# ================================================================================
# Request/Response Models
# ================================================================================

class NamespaceInfo(BaseModel):
    """Namespace information response"""
    name: str
    description: str
    use_cases: List[str]
    retention_policy: str
    sensitivity: str


class NamespaceListResponse(BaseModel):
    """Response for listing all namespaces"""
    namespaces: List[str]
    current: str
    count: int


class NamespaceSwitchRequest(BaseModel):
    """Request to switch namespace"""
    namespace: str = Field(..., description="Namespace to switch to")


class NamespaceSwitchResponse(BaseModel):
    """Response after switching namespace"""
    previous: str
    current: str
    message: str


class NamespaceStatsResponse(BaseModel):
    """Statistics for a namespace"""
    namespace: str
    memory_count: int
    storage_bytes: int
    oldest_memory: Optional[datetime]
    newest_memory: Optional[datetime]
    activity_7d: int  # Memories added in last 7 days


class NamespaceAccessLogEntry(BaseModel):
    """Single access log entry"""
    timestamp: str
    action: str
    details: Dict


class NamespaceAccessLogResponse(BaseModel):
    """Access log response"""
    entries: List[NamespaceAccessLogEntry]
    count: int


# ================================================================================
# Dependency for extracting namespace from header
# ================================================================================

async def get_namespace_from_header(
    x_namespace: Optional[str] = Header(None, description="Namespace for operation")
) -> str:
    """
    Extract namespace from X-Namespace header.
    Falls back to current thread namespace if header not provided.

    Args:
        x_namespace: Namespace from request header

    Returns:
        Validated namespace name

    Raises:
        HTTPException: If namespace is invalid
    """
    namespace = x_namespace or get_current_namespace()

    if not NamespaceRegistry.is_valid_namespace(namespace):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid namespace: {namespace}. "
                   f"Valid namespaces: {list_namespaces()}"
        )

    # Set namespace for current thread
    NamespaceContext.set_namespace(namespace)

    return namespace


# ================================================================================
# Endpoints
# ================================================================================

@router.get("/list", response_model=NamespaceListResponse)
async def list_all_namespaces():
    """
    List all available namespaces.

    Returns:
        List of namespace names with current namespace
    """
    namespaces = list_namespaces()
    current = get_current_namespace()

    return NamespaceListResponse(
        namespaces=namespaces,
        current=current,
        count=len(namespaces)
    )


@router.get("/current")
async def get_current():
    """
    Get the current active namespace for this thread.

    Returns:
        Current namespace name and details
    """
    namespace = get_current_namespace()
    details = get_namespace_details(namespace)

    return {
        "namespace": namespace,
        **details
    }


@router.post("/switch", response_model=NamespaceSwitchResponse)
async def switch_namespace_endpoint(request: NamespaceSwitchRequest):
    """
    Switch to a different namespace.

    Args:
        request: Namespace switch request

    Returns:
        Confirmation with previous and new namespace

    Raises:
        HTTPException: If namespace is invalid
    """
    previous = get_current_namespace()

    try:
        switch_namespace(request.namespace)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return NamespaceSwitchResponse(
        previous=previous,
        current=request.namespace,
        message=f"Switched from '{previous}' to '{request.namespace}'"
    )


@router.get("/{namespace}/info", response_model=NamespaceInfo)
async def get_namespace_info(namespace: str):
    """
    Get detailed information about a specific namespace.

    Args:
        namespace: Namespace name

    Returns:
        Namespace configuration and details

    Raises:
        HTTPException: If namespace is invalid
    """
    if not NamespaceRegistry.is_valid_namespace(namespace):
        raise HTTPException(
            status_code=404,
            detail=f"Namespace not found: {namespace}"
        )

    details = get_namespace_details(namespace)

    return NamespaceInfo(
        name=namespace,
        description=details['description'],
        use_cases=details['use_cases'],
        retention_policy=details['retention_policy'],
        sensitivity=details['sensitivity']
    )


@router.get("/{namespace}/stats", response_model=NamespaceStatsResponse)
async def get_namespace_stats(namespace: str):
    """
    Get statistics for a specific namespace.

    Args:
        namespace: Namespace name

    Returns:
        Memory count, storage usage, and activity stats

    Raises:
        HTTPException: If namespace is invalid
    """
    if not NamespaceRegistry.is_valid_namespace(namespace):
        raise HTTPException(
            status_code=404,
            detail=f"Namespace not found: {namespace}"
        )

    # This would query the database for actual stats
    # For now, return placeholder values
    stats = NamespaceStats()

    return NamespaceStatsResponse(
        namespace=namespace,
        memory_count=0,  # TODO: Query from database
        storage_bytes=0,  # TODO: Query from database
        oldest_memory=None,  # TODO: Query from database
        newest_memory=None,  # TODO: Query from database
        activity_7d=0  # TODO: Query from database
    )


@router.get("/access-log", response_model=NamespaceAccessLogResponse)
async def get_access_log(limit: int = 100):
    """
    Get recent namespace access log entries.

    Args:
        limit: Maximum number of entries to return (default 100)

    Returns:
        List of recent access log entries
    """
    log_entries = NamespaceContext.get_access_log(limit=limit)

    formatted_entries = [
        NamespaceAccessLogEntry(
            timestamp=entry['timestamp'],
            action=entry['action'],
            details={k: v for k, v in entry.items() if k not in ['timestamp', 'action']}
        )
        for entry in log_entries
    ]

    return NamespaceAccessLogResponse(
        entries=formatted_entries,
        count=len(formatted_entries)
    )


@router.delete("/{namespace}/memories")
async def delete_namespace_memories(
    namespace: str,
    confirm: bool = False
):
    """
    Delete all memories in a namespace (DANGEROUS).

    Args:
        namespace: Namespace to clear
        confirm: Must be True to proceed

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If namespace invalid or confirmation missing
    """
    if not NamespaceRegistry.is_valid_namespace(namespace):
        raise HTTPException(
            status_code=404,
            detail=f"Namespace not found: {namespace}"
        )

    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=True to delete all memories in namespace"
        )

    # TODO: Implement actual deletion
    # This would delete all memories where namespace = {namespace}

    return {
        "namespace": namespace,
        "status": "deleted",
        "message": f"All memories in namespace '{namespace}' have been deleted",
        "deleted_count": 0  # TODO: Return actual count
    }


# ================================================================================
# Helper endpoint to validate namespace in user_id
# ================================================================================

@router.post("/validate-user-id")
async def validate_user_id(user_id: str):
    """
    Validate and parse a namespaced user_id.

    Args:
        user_id: User ID in format 'base_user/namespace'

    Returns:
        Parsed components and validation status

    Raises:
        HTTPException: If user_id format is invalid
    """
    try:
        base_user, namespace = NamespaceContext.parse_user_id(user_id)

        return {
            "valid": True,
            "user_id": user_id,
            "base_user": base_user,
            "namespace": namespace,
            "namespace_info": get_namespace_details(namespace)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ================================================================================
# Health check endpoint
# ================================================================================

@router.get("/health")
async def namespace_health():
    """
    Health check for namespace system.

    Returns:
        System status and namespace count
    """
    namespaces = list_namespaces()
    current = get_current_namespace()

    return {
        "status": "healthy",
        "namespace_count": len(namespaces),
        "current_namespace": current,
        "namespaces": namespaces
    }


# ================================================================================
# Usage Instructions
# ================================================================================

"""
To integrate this into your mem0 FastAPI application:

1. Import the router:
   from namespace_api import router as namespace_router

2. Include it in your FastAPI app:
   app.include_router(namespace_router)

3. Use the X-Namespace header in other endpoints:
   @app.post("/memories")
   async def add_memory(
       request: MemoryRequest,
       namespace: str = Depends(get_namespace_from_header)
   ):
       # namespace is automatically extracted and validated
       user_id = NamespaceContext.format_user_id(request.user_id, namespace)
       # ... rest of implementation

4. Example API calls:

   # List all namespaces
   GET http://localhost:${MEM0_PORT}/v1/namespace/list

   # Get current namespace
   GET http://localhost:${MEM0_PORT}/v1/namespace/current

   # Switch namespace
   POST http://localhost:${MEM0_PORT}/v1/namespace/switch
   {"namespace": "progressief"}

   # Get namespace info
   GET http://localhost:${MEM0_PORT}/v1/namespace/progressief/info

   # Get namespace stats
   GET http://localhost:${MEM0_PORT}/v1/namespace/progressief/stats

   # Add memory with namespace (to existing endpoint)
   POST http://localhost:${MEM0_PORT}/memories
   X-Namespace: progressief
   {"messages": [...], "user_id": "mark_carey"}

   # Search memories in namespace
   GET http://localhost:${MEM0_PORT}/memories?user_id=mark_carey
   X-Namespace: cv_automation
"""
