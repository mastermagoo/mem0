#!/usr/bin/env python3
"""
Mem0 DR Operations with Wingman Approval Gates
All destructive operations require Wingman approval before execution.
"""
import sys
import os
import subprocess
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from wingman_approval_client import WingmanApprovalClient
except ImportError:
    print("❌ ERROR: wingman_approval_client.py not found")
    print("   Copy it from wingman-system/wingman/wingman_approval_client.py")
    sys.exit(1)


def stop_containers(env="test"):
    """Stop mem0 containers (requires Wingman approval)"""
    
    client = WingmanApprovalClient()
    
    instruction = f"""
DELIVERABLES:
- Stop all mem0 {env.upper()} containers
- Graceful shutdown of mem0 service
- No data loss

SUCCESS_CRITERIA:
- All containers in {env.upper()} environment stopped
- No errors during shutdown
- Containers can be restarted

BOUNDARIES:
- Stop containers only (do NOT remove)
- Do NOT touch PRD if env is TEST
- Do NOT remove volumes

DEPENDENCIES:
- Docker Compose file exists
- Wingman API accessible

MITIGATION:
- If stop fails: check container logs
- Rollback: Restart with docker-compose up -d

TEST_PROCESS:
1. docker compose -f docker-compose.{env}.yml ps
2. docker compose -f docker-compose.{env}.yml down
3. Verify containers stopped

TEST_RESULTS_FORMAT:
JSON: {{containers_stopped: int, errors: []}}

RESOURCE_REQUIREMENTS:
- CPU: minimal
- Memory: minimal
- Network: localhost only

RISK_ASSESSMENT:
- Risk Level: MEDIUM
- Risk Type: Service interruption
- Impact: Mem0 unavailable until restart

QUALITY_METRICS:
- All containers stopped: PASS
    """
    
    approved = client.request_approval(
        worker_id="mem0-dr-script",
        task_name=f"Stop Mem0 {env.upper()}",
        instruction=instruction,
        deployment_env=env,
    )
    
    if not approved:
        print("❌ Operation cancelled - approval denied/timeout")
        return False
    
    print(f"🔧 Stopping {env.upper()} containers...")
    
    base_dir = Path(__file__).parent.parent
    compose_file = base_dir / f"docker-compose.{env}.yml"
    
    if not compose_file.exists():
        print(f"❌ Compose file not found: {compose_file}")
        return False
    
    result = subprocess.run([
        "docker", "compose",
        "-f", str(compose_file),
        "down"
    ], cwd=base_dir)
    
    if result.returncode != 0:
        print(f"❌ Failed to stop: {result.returncode}")
        return False
    
    print(f"✅ {env.upper()} containers stopped")
    return True


def rebuild_containers(env="test"):
    """Rebuild mem0 containers (requires Wingman approval)"""
    
    client = WingmanApprovalClient()
    
    instruction = f"""
DELIVERABLES:
- Rebuild mem0 {env.upper()} containers
- Start mem0 service
- Verify health

SUCCESS_CRITERIA:
- Container built and running
- Health check passing
- Service accessible

BOUNDARIES:
- Rebuild from existing compose file
- Do NOT remove volumes
- Do NOT touch PRD if env is TEST

DEPENDENCIES:
- Docker Compose file exists
- Wingman approval

MITIGATION:
- If build fails: check Docker logs
- If unhealthy: check service logs
- Rollback: Stop and investigate

TEST_PROCESS:
1. docker compose up -d --build
2. Wait for health check
3. Verify service running

TEST_RESULTS_FORMAT:
JSON: {{container_running: bool, healthy: bool, errors: []}}

RESOURCE_REQUIREMENTS:
- CPU: High during build
- Memory: High during build
- Network: External (for pulls)

RISK_ASSESSMENT:
- Risk Level: MEDIUM
- Risk Type: Extended downtime during rebuild
- Impact: Mem0 unavailable during build

QUALITY_METRICS:
- Container running: PASS
- Health check passing: PASS
    """
    
    approved = client.request_approval(
        worker_id="mem0-dr-script",
        task_name=f"Rebuild Mem0 {env.upper()}",
        instruction=instruction,
        deployment_env=env,
    )
    
    if not approved:
        print("❌ Operation cancelled - approval denied/timeout")
        return False
    
    print(f"🔧 Rebuilding {env.upper()} containers...")
    
    base_dir = Path(__file__).parent.parent
    compose_file = base_dir / f"docker-compose.{env}.yml"
    
    if not compose_file.exists():
        print(f"❌ Compose file not found: {compose_file}")
        return False
    
    result = subprocess.run([
        "docker", "compose",
        "-f", str(compose_file),
        "up", "-d", "--build"
    ], cwd=base_dir)
    
    if result.returncode != 0:
        print(f"❌ Failed to rebuild: {result.returncode}")
        return False
    
    print(f"✅ {env.upper()} containers rebuilt and started")
    return True


def main():
    """Main DR workflow with approval gates"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mem0 DR with Wingman approval")
    parser.add_argument("env", choices=["test", "prd"], help="Environment")
    parser.add_argument("--stop-only", action="store_true", help="Only stop containers")
    parser.add_argument("--rebuild-only", action="store_true", help="Only rebuild containers")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"MEM0 DR OPERATION - {args.env.upper()}")
    print("=" * 60)
    print("")
    print("⚠️  ALL operations require Wingman approval")
    print("📱 Check Telegram for approval requests")
    print("")
    
    if args.stop_only:
        success = stop_containers(args.env)
    elif args.rebuild_only:
        success = rebuild_containers(args.env)
    else:
        # Full DR: Stop → Rebuild
        print("Stage A: Stop containers")
        if not stop_containers(args.env):
            sys.exit(1)
        
        print("")
        print("Stage B: Rebuild containers")
        if not rebuild_containers(args.env):
            sys.exit(1)
        
        success = True
    
    if success:
        print("")
        print("=" * 60)
        print("✅ DR OPERATION COMPLETE")
        print("=" * 60)
    else:
        print("")
        print("=" * 60)
        print("❌ DR OPERATION FAILED")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
