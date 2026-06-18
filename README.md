# Customer360-MCP

A conversational analytics server that lets business users query enterprise customer data in plain English — no SQL required.

Built on **Snowflake Cortex Analyst** and exposed via the **Model Context Protocol (MCP)**, with a REST fallback, CLI, voice interface, and web UI. Deployed via Docker with a GitHub Actions CI/CD pipeline for Snowflake.

---

## What it does

Type a question like _"Which customers have the highest churn risk?"_ or _"Show me revenue by city"_ — the server translates it into SQL using Cortex Analyst, runs it against Snowflake, and returns a formatted answer.

**Three ways to interact:**
- **Web UI** (`index.html`) — browser-based chat interface
- **CLI** (`cli.py`) — terminal client using the MCP protocol
- **Voice CLI** (`voice_cli.py`) — speak your question, get an answer

---

## Architecture

```
User (voice / CLI / browser)
        │
        ▼
  MCP Server (server.py)
  ├── /mcp   → MCP JSON-RPC (for CLI)
  ├── /ask   → REST endpoint (for web UI)
  └── /health → health check
        │
        ▼
  Snowflake Cortex Analyst
  └── CUSTOMER_360.SILVER (semantic model YAML)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| NLP → SQL | Snowflake Cortex Analyst |
| Data warehouse | Snowflake (CUSTOMER_360 DB, SILVER schema) |
| Server | Python (stdlib `http.server`, ThreadingHTTPServer) |
| Protocol | MCP JSON-RPC 2024-11-05 |
| Containerization | Docker |
| CI/CD | GitHub Actions + Snowflake CLI |
| Frontend | HTML / JavaScript |

---

## Getting Started

### Prerequisites
- Docker
- A Snowflake account with Cortex Analyst enabled
- Semantic model YAML uploaded to your Snowflake stage

### Run locally

```bash
docker build -t customer360-mcp .
docker run -p 8000:8000 \
  -e SF_ACCOUNT=your_account \
  -e SF_USER=your_user \
  -e SF_PASSWORD=your_password \
  -e SF_ROLE=ACCOUNTADMIN \
  -e SF_WAREHOUSE=COMPUTE_WH \
  -e SF_DATABASE=CUSTOMER_360 \
  -e SF_SCHEMA=SILVER \
  -e SEMANTIC_MODEL_FILE=@CUSTOMER_360.BRONZE.CUSTOMER_STAGE/customer360_model.yaml \
  customer360-mcp
```

### Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/mcp` | POST | MCP JSON-RPC (used by CLI) |
| `/ask` | POST | REST — send `{"question": "..."}` |
| `/health` | GET | Health check |

### Example REST call

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which city has the most customers?"}'
```

---

## Repository Structure

```
├── server.py          # MCP + REST server (core)
├── cli.py             # Terminal client (MCP protocol)
├── voice_cli.py       # Voice-based query interface
├── index.html         # Browser UI
├── deploy.sql         # Snowflake schema setup
├── deploy.sh          # Deployment helper script
├── Dockerfile         # Container definition
├── requirements.txt   # Python dependencies
└── .github/workflows/ # CI/CD — Snowflake CLI deployment
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SF_ACCOUNT` | `urkdocl-wj23271` | Snowflake account identifier |
| `SF_USER` | `KAUSHIK` | Snowflake username |
| `SF_PASSWORD` | _(set via env)_ | Snowflake password — **never hardcode** |
| `SF_ROLE` | `ACCOUNTADMIN` | Snowflake role |
| `SF_WAREHOUSE` | `COMPUTE_WH` | Warehouse name |
| `SF_DATABASE` | `CUSTOMER_360` | Target database |
| `SF_SCHEMA` | `SILVER` | Target schema |
| `SEMANTIC_MODEL_FILE` | _(stage path)_ | Path to Cortex Analyst YAML |

---

## Built by

[Kaushik Ram P](https://linkedin.com/in/kaushik-ram-895b8928a) — Agentic AI Intern @ Wipro  
Integrated M.Tech Computer Science (Data Science) — VIT Vellore
