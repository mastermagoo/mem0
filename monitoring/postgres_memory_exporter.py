#!/usr/bin/env python3
"""
PostgreSQL Memory Count Exporter for Prometheus
Exposes mem0 memory count metrics for monitoring and alerting
"""
import os
import time
import psycopg
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration from environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "mem0_user_prd")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mem0_prd")
EXPORTER_PORT = int(os.getenv("EXPORTER_PORT", "9094"))

# Required secrets
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
if not POSTGRES_PASSWORD:
    raise RuntimeError("POSTGRES_PASSWORD is required (do not hardcode secrets in code)")

# Thresholds for alerts
CRITICAL_THRESHOLD = 0  # Alert if memory count = 0
WARNING_THRESHOLD_DROP = 0.5  # Alert if count drops by >50%

# Store previous count for drop detection
previous_count = None


def get_memory_metrics():
    """Query PostgreSQL for memory metrics"""
    global previous_count

    try:
        conn = psycopg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            dbname=POSTGRES_DB,
            password=POSTGRES_PASSWORD,
            connect_timeout=5
        )

        with conn.cursor() as cur:
            # Total memory count
            cur.execute("SELECT COUNT(*) FROM memories")
            total_count = cur.fetchone()[0]

            # Memory counts by namespace (user_id)
            cur.execute("""
                SELECT
                    payload->>'user_id' as namespace,
                    COUNT(*) as count
                FROM memories
                GROUP BY namespace
                ORDER BY count DESC
            """)
            namespace_counts = cur.fetchall()

        conn.close()

        # Calculate drop percentage
        drop_percentage = 0.0
        if previous_count is not None and previous_count > 0:
            drop_percentage = (previous_count - total_count) / previous_count

        previous_count = total_count

        return {
            "total": total_count,
            "namespaces": namespace_counts,
            "drop_percentage": drop_percentage,
            "status": "up"
        }

    except Exception as e:
        return {
            "total": -1,
            "namespaces": [],
            "drop_percentage": 0.0,
            "status": "down",
            "error": str(e)
        }


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for /metrics endpoint"""

    def do_GET(self):
        if self.path == "/metrics":
            metrics = get_memory_metrics()

            # Build Prometheus format response
            response = []

            # Help text
            response.append("# HELP mem0_memory_total Total number of memories stored")
            response.append("# TYPE mem0_memory_total gauge")
            response.append(f"mem0_memory_total {metrics['total']}")
            response.append("")

            # Memory count by namespace
            response.append("# HELP mem0_memory_count Memory count by namespace")
            response.append("# TYPE mem0_memory_count gauge")
            for namespace, count in metrics['namespaces']:
                # Sanitize namespace for Prometheus label
                safe_namespace = namespace.replace("/", "_").replace("-", "_")
                response.append(f'mem0_memory_count{{namespace="{safe_namespace}"}} {count}')
            response.append("")

            # Drop percentage (for detecting sudden decreases)
            response.append("# HELP mem0_memory_drop_percentage Percentage drop from previous count")
            response.append("# TYPE mem0_memory_drop_percentage gauge")
            response.append(f"mem0_memory_drop_percentage {metrics['drop_percentage']}")
            response.append("")

            # Database status
            response.append("# HELP mem0_database_up Database connectivity status (1=up, 0=down)")
            response.append("# TYPE mem0_database_up gauge")
            status_value = 1 if metrics['status'] == 'up' else 0
            response.append(f"mem0_database_up {status_value}")
            response.append("")

            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("\n".join(response).encode("utf-8"))

        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def main():
    """Start the exporter HTTP server"""
    print(f"Starting PostgreSQL Memory Exporter on port {EXPORTER_PORT}")
    print(f"Database: {POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print(f"Metrics endpoint: http://localhost:{EXPORTER_PORT}/metrics")

    server = HTTPServer(("0.0.0.0", EXPORTER_PORT), MetricsHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down exporter...")
        server.shutdown()


if __name__ == "__main__":
    main()
