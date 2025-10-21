# Mem0 Platform

Self-contained Mem0 deployment with Neo4j Graph Data Science support.

## Overview

Standalone mem0 platform deployment with:
- **PostgreSQL** with pgvector extension
- **Neo4j** with Graph Data Science (GDS) plugin
- **Mem0 API** with local LLM routing
- **Grafana** monitoring
- **Telegram Bot** for personal memory access

## Quick Start

```bash
# Navigate to project
cd /Volumes/Data/ai_projects/mem0-platform

# Start services
cd docker
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f mem0_prd
```

## Architecture

```
mem0-platform/
├── docker/              # Docker compose configurations
│   ├── docker-compose.yml       # Main production config
│   ├── docker-compose.prd.yml   # PRD environment
│   ├── docker-compose.test.yml  # TEST environment
│   └── docker-compose.dev.yml   # DEV environment
├── scripts/             # Utility scripts
│   ├── telegram_bot/    # Telegram bot integration
│   └── *.py            # Python utilities
├── docs/                # Documentation
├── data/                # Persistent data (gitignored)
└── logs/                # Application logs (gitignored)
```

## Configuration

### Environment Files

- `.env` - Default configuration
- `.env.prd` - Production environment
- `.env.test` - Test environment template
- `.env.dev.example` - Development environment template

### Data Storage

All persistent data stored in: `/Volumes/Data/ai_projects/mem0-platform/data/`

- `data/postgres/` - PostgreSQL data
- `data/neo4j/` - Neo4j graph database
- `data/grafana/` - Grafana dashboards
- `data/` - Mem0 application data

## Services

| Service | Port | Description |
|---------|------|-------------|
| mem0_prd | 8888 | Mem0 API server |
| postgres | 5433 | PostgreSQL with pgvector |
| neo4j | 7475 (HTTP), 7688 (Bolt) | Neo4j with GDS plugin |
| grafana | 3001 | Monitoring dashboard |
| telegram_bot | - | Telegram integration |

## Network Configuration

### Internal Network

All services connected via `mem0_internal` bridge network.

### External Connections

Projects can connect to mem0 services via Docker network:

```yaml
# In other project's docker-compose.yml
networks:
  mem0_network:
    external: true
    name: mem0_internal
```

## Documentation

See `/docs/` directory for:
- API_REFERENCE.md - API documentation
- DEPLOYMENT_GUIDE.md - Deployment instructions
- OPERATIONS.md - Operations manual
- TROUBLESHOOTING.md - Common issues and solutions
- USER_GUIDE.md - End-user documentation

## Integration with CV-Automation

CV-automation project connects to mem0 via shared Docker network. No code changes needed - services discover each other via container names.

## Development

### Local Development

Use `docker-compose.dev.yml` for local development with hot-reload.

### Testing

Use `docker-compose.test.yml` for integration testing.

## Monitoring

Grafana dashboard available at: http://localhost:3001

Default credentials: See `.env.prd` (gitignored)

## Security

- All credentials stored in `.env` files (gitignored)
- No hardcoded passwords in source code
- Services isolated in internal Docker network
- External access only via defined ports

## License

Private project for Mark Carey / intel-system

## Repository

https://github.com/mastermagoo/mem0-platform
