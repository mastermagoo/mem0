# mem0 Production Deployment System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

**Version**: 2.0
**Status**: ✅ Production Ready
**Architecture**: Self-Contained, Zero Dependencies

## 🎯 Overview

mem0 is a personal AI memory system providing persistent, graph-based knowledge storage with vector search capabilities. This repository contains the complete production deployment system with:

- **Multi-Tenant Namespace Isolation** - Complete data separation per user/project
- **Ollama-Only LLM Routing** - Local LLM processing, no external API dependencies
- **Neo4j Graph Storage** - Knowledge graphs with Graph Data Science (GDS) plugin
- **Vector Search** - PostgreSQL with pgvector for semantic search
- **Telegram Bot Interface** - Easy memory management via Telegram
- **Production Monitoring** - Grafana dashboards for system health
- **Automated Deployment** - One-command production deployment

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  mem0 Production Environment                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ mem0_server │  │   neo4j     │  │  postgresql │        │
│  │ :8888       │  │   :7688     │  │   :5433     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  grafana    │  │telegram_bot │  │  exporters  │        │
│  │  :3001      │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
│              mem0_internal_prd Network                      │
│                  192.168.97.0/24                           │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker** 20.10+ with Docker Compose 2.0+
- **RAM**: 4GB+ available
- **Storage**: 10GB+ free space
- **Ports**: 3001, 5433, 7475, 7688, 8888 available
- **Ollama**: Local Ollama installation (for LLM processing)

### Installation

```bash
# Clone repository
git clone https://github.com/mastermagoo/mem0-production.git
cd mem0-production

# Create environment file from example
cp .env.example .env

# Edit .env with your configuration
nano .env

# Deploy to production
./deploy_prd.sh up
```

### Verify Deployment

```bash
# Check all containers are running
./deploy_prd.sh status

# Run validation tests
./deploy_prd.sh validate

# View logs
./deploy_prd.sh logs
```

## 📚 Documentation

- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[API Reference](docs/API_REFERENCE.md)** - API endpoints and usage
- **[Namespace Architecture](docs/NAMESPACE_ARCHITECTURE.md)** - Multi-tenant isolation design
- **[Operations Guide](docs/OPERATIONS.md)** - Day-to-day operations
- **[Production Rules](docs/PRODUCTION_DEPLOYMENT_RULES.md)** - Deployment best practices
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Common commands

## 🔑 Key Features

### 1. Multi-Tenant Namespace Isolation

Complete data separation per namespace (user/project):
- Isolated memory storage
- Independent vector embeddings
- Separate graph structures
- Namespace-specific API keys

See [Namespace Architecture](docs/NAMESPACE_ARCHITECTURE.md) for details.

### 2. Ollama-Only LLM Routing

All LLM processing routes to local Ollama:
- Zero external API dependencies
- Complete data privacy
- No API costs
- Configurable models per namespace

Enforcement: `enforce_ollama_only.py` ensures no OpenAI/external calls.

### 3. Neo4j with GDS Plugin

Graph-based knowledge storage with:
- Relationship mapping
- Community detection
- Similarity search
- Centrality analysis

GDS patch: `mem0_gds_patch_v2.py` ensures production compatibility.

### 4. Telegram Bot Interface

Personal memory assistant via Telegram:
- Store/retrieve memories
- Search by semantic similarity
- Manage namespaces
- System health monitoring

Location: `telegram_bot/`

### 5. Production Monitoring

Grafana dashboards for:
- Memory usage trends
- API request rates
- Database performance
- Error rates

Access: http://localhost:3001 (default: admin/admin)

## 🔧 Configuration

### Environment Variables

Create `.env` from `.env.example` and configure:

```bash
# Deployment Environment
DEPLOYMENT_ENV=prd

# Database Credentials
POSTGRES_PASSWORD=your_secure_password
NEO4J_PASSWORD=your_secure_password

# Ollama Configuration
OLLAMA_URL=http://host.docker.internal:11434

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Namespace Configuration

Each namespace requires:
- Unique API key
- LLM model selection
- Optional metadata

Managed via `namespace_api.py` endpoints.

## 🛠️ Operations

### Daily Operations

```bash
# Check system health
./deploy_prd.sh status

# View recent logs
./deploy_prd.sh logs

# Restart services
./deploy_prd.sh restart
```

### Common Tasks

```bash
# Add new namespace
curl -X POST http://localhost:8888/api/v1/namespaces \
  -H "Content-Type: application/json" \
  -d '{"name": "project_x", "api_key": "key_123"}'

# Store memory
curl -X POST http://localhost:8888/api/v1/memories \
  -H "X-Namespace: project_x" \
  -d '{"text": "Important fact", "metadata": {}}'

# Search memories
curl -X GET "http://localhost:8888/api/v1/memories/search?query=fact" \
  -H "X-Namespace: project_x"
```

See [Operations Guide](docs/OPERATIONS.md) for complete details.

## 🔐 Security

- **No Hardcoded Credentials** - All from `.env`
- **Namespace Isolation** - Complete data separation
- **Local Processing** - Ollama-only, no external APIs
- **Network Isolation** - Dedicated Docker network
- **TLS Support** - Optional for external access

See [Production Rules](docs/PRODUCTION_DEPLOYMENT_RULES.md).

## 📊 Monitoring

### Access Points

- **API Documentation**: http://localhost:8888/docs
- **Grafana Dashboard**: http://localhost:3001
- **Neo4j Browser**: http://localhost:7475
- **PostgreSQL**: localhost:5433

### Health Checks

```bash
# Overall health
curl http://localhost:8888/health

# Database connections
curl http://localhost:8888/health/db

# Neo4j GDS plugin
curl http://localhost:8888/health/neo4j
```

## 🧪 Testing

```bash
# Run integration tests
python test_integration.py

# Test namespace isolation
python test_namespace_isolation.py

# Test LLM routing (Ollama-only)
python test_llm_routing.py

# Test Ollama enforcement
python test_ollama_enforcement.py
```

## 📦 Repository Structure

```
mem0-production/
├── README.md                      # This file
├── .env.example                   # Environment template
├── .gitignore                     # Git exclusions
├── LICENSE                        # MIT License
│
├── deploy_prd.sh                  # Production deployment wrapper
├── docker-compose.prd.yml         # Production compose file
├── Dockerfile.mem0                # mem0 server image
│
├── namespace_api.py               # Namespace management API
├── namespace_manager.py           # Namespace isolation logic
├── llm_router.py                  # Ollama-only routing
├── enforce_ollama_only.py         # LLM enforcement
├── mem0_gds_patch_v2.py          # Neo4j GDS compatibility
│
├── telegram_bot/                  # Telegram interface
│   ├── bot.py                    # Main bot logic
│   ├── config.py                 # Bot configuration
│   ├── mem0_client.py            # mem0 API client
│   └── handlers/                 # Command handlers
│
├── monitoring/                    # Monitoring configs
│   └── prometheus.yml            # Prometheus configuration
│
├── docs/                         # Documentation
│   ├── API_REFERENCE.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── NAMESPACE_ARCHITECTURE.md
│   ├── OPERATIONS.md
│   ├── PRODUCTION_DEPLOYMENT_RULES.md
│   ├── TROUBLESHOOTING.md
│   ├── QUICK_REFERENCE.md
│   └── archive/                  # Historical docs
│
└── tests/                        # Test scripts
    ├── test_integration.py
    ├── test_namespace_isolation.py
    ├── test_llm_routing.py
    └── test_ollama_enforcement.py
```

## 🤝 Contributing

This is a production deployment system extracted from a larger intelligence platform. Contributions welcome for:

- Bug fixes
- Documentation improvements
- Feature enhancements
- Test coverage

Please ensure all changes maintain backward compatibility with existing deployments.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [mem0ai/mem0](https://github.com/mem0ai/mem0) - Core mem0 library
- [ollama/ollama](https://github.com/ollama/ollama) - Local LLM runtime
- [neo4j/neo4j](https://github.com/neo4j/neo4j) - Graph database

## 📞 Support

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **API Docs**: http://localhost:8888/docs (when running)

## 🎯 Project Goals

1. **Privacy-First**: All processing local, no external APIs
2. **Production-Grade**: Battle-tested in production environments
3. **Multi-Tenant**: Complete isolation between namespaces
4. **Self-Contained**: Zero dependencies on external systems
5. **Well-Documented**: Comprehensive documentation and examples

## 🏆 Production Status

- ✅ Deployed and operational since October 2025
- ✅ Multi-tenant namespace isolation validated
- ✅ Ollama-only routing enforced
- ✅ Neo4j GDS plugin production-compatible
- ✅ Telegram bot interface operational
- ✅ Monitoring dashboards active
- ✅ Backup and recovery procedures tested

---

**Source**: Extracted from intel-system project
**Maintained**: Regular updates and security patches
**Status**: Production deployment in active use
