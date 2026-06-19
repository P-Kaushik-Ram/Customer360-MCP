# Customer360 AI Data Pipeline

> End-to-end AI-powered data platform built on **AWS Bedrock**, **Snowflake**, and **GitHub Actions** — featuring a native MCP server, metadata-driven pipelines, and an autonomous AI data agent.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLOW A — Automated Trigger               │
│                                                                  │
│  Jira Issue → API Gateway → AWS Bedrock Agent → Lambda          │
│       → Snowflake Cortex Analyst → Answer posted to Jira        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   FLOW B — Native MCP Server                     │
│                                                                  │
│  ask.ps1 (snow CLI) → CREATE MCP SERVER (Snowflake-native)      │
│       → Semantic View (CUSTOMER360_SV) → Cortex Analyst         │
│       Deployed via: GitHub Actions → snow sql -f deploy.sql     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  FLOW C — AI Data Agent                          │
│                                                                  │
│  Claude Code reads customer360_metadata.yaml                     │
│       → Runs Bronze → Silver → Gold pipeline                     │
│       → Data quality checks → PIPELINE_AUDIT table              │
│       → Generates assessment_report.md                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Agent | AWS Bedrock (Claude 3 Sonnet), Claude Code |
| Data Warehouse | Snowflake (Data Vault 2.0) |
| NL→SQL | Snowflake Cortex Analyst |
| MCP Server | Snowflake-native `CREATE MCP SERVER` |
| Semantic Layer | Snowflake Semantic View (`CUSTOMER360_SV`) |
| Trigger | Jira Webhook → AWS API Gateway |
| Serverless | AWS Lambda (Python) |
| CLI Client | Snowflake CLI (`snow`) |
| CI/CD | GitHub Actions |
| IaC | SQL-as-code (`deploy.sql`) |

---

## Data Architecture — Snowflake

```
Source Systems (6)
    CRM · ERP · LOCAL · CONTRACT_MGMT · FINANCE · INTERACTIONS
         ↓
    BRONZE LAYER (Raw landing — 6 tables)
         ↓
    SILVER LAYER — Data Vault 2.0 (28 tables)
    ├── Cleansed:  SILVER_CRM, SILVER_ERP, SILVER_LOCAL...
    ├── Hub:       HUB_CUSTOMER (220 unique customers)
    ├── Satellites: SAT_CRM_CUSTOMER, SAT_ERP_CUSTOMER...
    ├── Links:     LINK_CUSTOMER_CONTRACT, LINK_CUSTOMER_REVENUE...
    ├── KPIs:      CUSTOMER_CHURN_RISK, CUSTOMER_HEALTH_SCORE...
    └── Audit:     PIPELINE_AUDIT (pipeline run history)
         ↓
    GOLD LAYER
    └── GOLDEN_CUSTOMER → CUSTOMER360_VIEW (220 customers, 27 cols)
         ↓
    SEMANTIC LAYER
    └── CUSTOMER360_SV (Snowflake Semantic View)
         ↓
    NATIVE MCP SERVER
    └── CUSTOMER360_MCP (Cortex Analyst tool)
```

**Key metrics:**
- 220 unique customers across 3 source systems
- 8 survivorship rules for golden record resolution
- ₹155.3M total revenue tracked
- Health, Churn Risk, and Renewal scores per customer

---

## What This Demo Shows

### 1. Jira → Answer (Flow A)
Create a Jira issue with a business question in the description. Within 30 seconds, a comment appears with the answer — pulled from live Snowflake data by an AWS Bedrock agent.

```
Jira: "How many customers have a churn risk score above 60?"
→ Comment: "There are 57 customers with a churn risk score above 60."
```

### 2. Natural Language Query via snow CLI (Flow B)
```powershell
.\ask.ps1 -Question "Show me the top 5 customers by revenue with health level"
```
→ Calls native Snowflake MCP server → Cortex Analyst generates SQL → `snow` executes it → real results.

### 3. Autonomous Pipeline + Assessment (Flow C)
```
claude> Read customer360_metadata.yaml and run the full pipeline assessment
```
→ Claude Code reads the YAML → runs 8 pipeline stages → 5 DQ checks → populates `PIPELINE_AUDIT` in Snowflake → writes `assessment_report.md` with real findings including bugs it discovered autonomously.

---

## CI/CD Pipeline

On every push to `main` that touches `deploy.sql`:

```yaml
GitHub Push → Install Snowflake CLI → snow sql -f deploy.sql
           → Smoke test semantic view (TOTAL_REVENUE = $155.3M)
           → Smoke test MCP server exists
           → Done
```

Secrets managed in GitHub Actions — no credentials in code.

---

## Repository Structure

```
Customer360-MCP/
├── server.py                    # Custom MCP server (Docker)
├── Dockerfile                   # Container definition
├── requirements.txt             # Python dependencies
├── deploy.sql                   # Semantic view + MCP server DDL
├── customer360_metadata.yaml    # Metadata-driven pipeline config
├── assessment_report.md         # Latest pipeline assessment output
├── ask.ps1                      # snow CLI query client
├── cli.py                       # MCP CLI client
├── voice_cli.py                 # Voice-enabled MCP client
├── index.html                   # Web UI
└── .github/
    └── workflows/
        ├── docker-build.yml     # Docker image CI/CD
        └── snowflake-deploy.yml # Snowflake objects CI/CD
```

---

## Key Findings from Assessment

Claude Code autonomously discovered these issues during the pipeline run:

1. **`COMPLETENESS_SCORE` bug** — flat value of 6 for all 220 customers, indicating broken per-row calculation in `CUSTOMER360_VIEW`
2. **Schema drift** — `SILVER_ERP` metadata YAML describes order-grained schema but live table is customer-grained
3. **46 unresolved cross-source conflicts** — 20 phone, 13 city, 13 pincode disagreements in the golden record
4. **Churn score clamping** — all churned customers show exactly 100.00, suggesting hardcoded logic rather than dynamic calculation

---

## Setup

### Prerequisites
- AWS account with Bedrock access (us-east-1)
- Snowflake account (Singapore/any region)
- Snowflake CLI (`snow`) installed
- GitHub account

### Deploy Snowflake Objects
```bash
# Add secrets to GitHub Actions, then:
git push  # triggers snowflake-deploy.yml automatically
```

### Run a Query
```powershell
.\ask.ps1 -Question "How many customers are at high churn risk?"
```

### Run Full Pipeline Assessment
```bash
claude  # inside project directory
> Read customer360_metadata.yaml and run the full pipeline and assessment
```

---

## About

Built as a demonstration of end-to-end AI data engineering on AWS + Snowflake.

**Architecture patterns demonstrated:**
- Data Vault 2.0 (Hub/Link/Satellite)
- Model Context Protocol (MCP) — both custom and Snowflake-native
- Metadata-driven pipeline orchestration
- Agentic AI for autonomous data engineering
- SQL-as-code with CI/CD

---

*Built by Badri Kaushik P — VIT Vellore, B.Tech + M.Tech CS (2028)*
