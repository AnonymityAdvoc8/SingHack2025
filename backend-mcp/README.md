# TravelMate AI - Backend MCP Server

Enterprise-grade Model Context Protocol (MCP) server for conversational travel insurance distribution.

## Architecture

```
backend-mcp/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Configuration management
│   ├── database.py                # Database connections & sessions
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── policy.py             # Policy data models
│   │   ├── taxonomy.py           # Taxonomy models
│   │   └── claims.py             # Claims data models
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── policy.py
│   │   ├── trip.py
│   │   └── quote.py
│   │
│   ├── mcp/                       # MCP Protocol Implementation
│   │   ├── __init__.py
│   │   ├── server.py             # MCP server core
│   │   ├── resources.py          # MCP Resources layer
│   │   ├── tools.py              # MCP Tools layer
│   │   └── prompts.py            # MCP Prompts layer
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── policy_service.py     # Policy operations
│   │   ├── comparison_service.py # Policy comparison
│   │   ├── eligibility_service.py# Eligibility checks
│   │   ├── quote_service.py      # Quote generation
│   │   ├── payment_service.py    # Payment integration
│   │   └── claims_analytics.py   # Claims intelligence
│   │
│   ├── utils/                     # Utilities
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py     # PDF text extraction
│   │   ├── taxonomy_mapper.py   # Map policies to taxonomy
│   │   ├── security.py          # OWASP security utilities
│   │   └── logger.py            # Structured logging
│   │
│   └── api/                       # REST API endpoints
│       ├── __init__.py
│       ├── health.py
│       ├── policies.py
│       └── quotes.py
│
├── scripts/                       # Data processing scripts
│   ├── extract_policies.py       # Phase 1: Extract policy data
│   ├── load_claims_data.py       # Phase 5: Load claims data
│   └── init_database.py          # Database initialization
│
├── tests/
│   ├── __init__.py
│   ├── test_services.py
│   └── test_mcp.py
│
├── alembic/                       # Database migrations
│   └── versions/
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Setup

1. **Create virtual environment:**
```bash
cd backend-mcp
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp ../.env.development .env
# Edit .env with your API keys
```

4. **Initialize database:**
```bash
python scripts/init_database.py
```

5. **Extract policy data (Phase 1):**
```bash
python scripts/extract_policies.py
```

6. **Run server:**
```bash
uvicorn app.main:app --reload --port 8080
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/policies` | GET | List all policies |
| `/api/v1/policies/{id}` | GET | Get policy details |
| `/api/v1/compare` | POST | Compare policies |
| `/api/v1/quote` | POST | Generate quote |

## MCP Protocol

### Resources
- `normalized_policies` - Structured policy data
- `original_policy_text` - Raw policy language
- `user_session` - Conversation context
- `taxonomy_schema` - Taxonomy structure

### Tools
- `compare_policies` - Multi-dimensional comparison
- `answer_policy_question` - Q&A with citations
- `check_eligibility` - Eligibility verification
- `analyze_scenario` - Coverage scenario analysis
- `get_quote` - Generate insurance quote
- `purchase_policy` - Initiate payment flow
- `check_payment_status` - Monitor payment
- `analyze_trip_risk` - Claims-based risk analysis

### Prompts
- Comparison templates
- Explanation templates
- Recommendation templates

## Security (OWASP)

- ✅ Input validation on all endpoints
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS protection
- ✅ Rate limiting
- ✅ Structured logging (no sensitive data)
- ✅ Environment variable management

## Development

```bash
# Run tests
pytest

# Code formatting
black app/
ruff check app/

# Type checking
mypy app/
```

---

**Ancileo × MSIG | SingHack 2025**

