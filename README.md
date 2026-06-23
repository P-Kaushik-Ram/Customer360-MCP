# Customer360 AI Data Platform

> End-to-end AI-powered data platform built on **AWS Bedrock**, **Snowflake**, **PostgreSQL**, and **GitHub Actions** — featuring autonomous schema discovery, PII detection, data masking, metadata-driven pipelines, and a native MCP server.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│           FLOW A — Jira → AI → Snowflake (Query Engine)             │
│                                                                      │
│  Jira Issue → API Gateway → AWS Bedrock Agent → Lambda              │
│       → Snowflake Cortex Analyst → Answer posted to Jira            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│           FLOW B — Native Snowflake MCP Server                       │
│                                                                      │
│  ask.ps1 (snow CLI) → CREATE MCP SERVER (Snowflake-native)          │
│       → Semantic View CUSTOMER360_SV → Cortex Analyst               │
│       Deployed via: GitHub Actions → snow sql -f deploy.sql         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│           FLOW C — Claude Code Autonomous Pipeline                   │
│                                                                      │
│  Claude Code reads customer360_metadata.yaml                         │
│       → Runs Bronze → Silver → Gold pipeline                         │
│       → Data quality checks → PIPELINE_AUDIT table in Snowflake     │
│       → Generates assessment_report.md with real findings           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│           FLOW D — PostgreSQL Schema Discovery Pipeline              │
│                                                                      │
│  Jira Issue (PG host + credentials in description)                  │
│       → Lambda connects to PostgreSQL                               │
│       → Discovers all tables + samples data                         │
│       → Bedrock Agent detects PII + recommends quality rules        │
│       → Stores metadata in DynamoDB                                 │
│       → Creates Jira approval issue                                 │
│       → Manager comments PGAPPROVE <SOURCE_ID>                      │
│       → AWS Glue reads PostgreSQL → applies masking → S3 Parquet   │
│       → Glue Data Catalog updated                                   │
│       → DynamoDB: GLUE_COMPLETED                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Agent | AWS Bedrock (Claude Sonnet), Claude Code |
| Data Warehouse | Snowflake (Data Vault 2.0) |
| Source Database | AWS RDS PostgreSQL 18 |
| NL→SQL | Snowflake Cortex Analyst |
| MCP Server | Snowflake-native `CREATE MCP SERVER` |
| Semantic Layer | Snowflake Semantic View (`CUSTOMER360_SV`) |
| ETL | AWS Glue 5.1 (Spark, PySpark) |
| Data Lake | S3 + Apache Parquet (Iceberg-ready) |
| Metadata Store | AWS DynamoDB |
| Data Catalog | AWS Glue Data Catalog |
| Trigger | Jira Webhook → AWS API Gateway / Lambda Function URL |
| Serverless | AWS Lambda (Python 3.12) |
| CLI Client | Snowflake CLI (`snow`) |
| CI/CD | GitHub Actions |
| IaC | SQL-as-code (`deploy.sql`) |

---

## Flow D — PostgreSQL Schema Discovery (New)

### What it does
When a team member needs to onboard a new PostgreSQL database as a data source, they create a Jira issue with the connection details. The platform automatically:

1. Connects to the PostgreSQL database
2. Discovers all tables and columns
3. Samples data and sends to Bedrock Agent for PII detection
4. Recommends data quality rules
5. Creates an approval ticket in Jira
6. On manager approval, runs Glue ETL with masking applied
7. Lands masked data in S3 data lake

### PII Detection & Masking Rules

| Column Type | Detection | Masking Example |
|---|---|---|
| Email | `pii_type: EMAIL` | `arjun.sharma@gmail.com` → `a***@gmail.com` |
| Phone | `pii_type: PHONE` | `+91-9876543210` → `+XX-XXXX-XX-1234` |
| Credit Card | `pii_type: CREDIT_CARD` | `4111-1111-1111-1234` → `XXXX-XXXX-XXXX-1234` |
| SSN | `pii_type: SSN` | `123-45-6789` → `XXX-XX-6789` |
| CVV | `pii_type: CVV` | `123` → `***` |
| Bank Account | `pii_type: BANK_ACCOUNT` | `HDFC00004521` → `XXXX4521` |
| Address | `pii_type: ADDRESS` | `12 MG Road` → `XXXX` |
| Date of Birth | `pii_type: DOB` | `1990-03-15` → `XXXX-XX-XX` |

### Demo walkthrough

**Step 1 — Create Jira issue:**
```
Summary: PG Discovery Request

host: your-rds-endpoint.amazonaws.com
port: 5432
database: customer360
username: postgres
password: xxxxxxxx
destination: S3 Iceberg → customer360_lake
```

**Step 2 — Automatic analysis (no human action needed):**
```
Lambda triggered → connects to PostgreSQL
→ discovers 4 tables, 30+ columns
→ Bedrock Agent detects 10 PII columns
→ recommends 4 quality rules
→ creates Jira KAN-8 with full schema + masking plan
```

**Step 3 — Manager approves:**
```
Comment on Jira: PGAPPROVE 2618AD94
```

**Step 4 — Pipeline runs automatically:**
```
Glue job starts → reads all 4 PostgreSQL tables
→ applies masking transformations
→ writes masked Parquet files to S3
→ DynamoDB updated: GLUE_COMPLETED
Total time: ~90 seconds
```

**S3 output:**
```
s3://customer360-source-uploads-137451611241/lake/batch/
├── customers/     part-00000-*.snappy.parquet   (8 rows, masked)
├── employees/     part-00000-*.snappy.parquet   (4 rows, masked)
├── payment_cards/ part-00000-*.snappy.parquet   (8 rows, masked)
└── transactions/  part-00000-*.snappy.parquet   (9 rows, masked)
```

---

## Snowflake Data Architecture

```
Source Systems (6)
    CRM · ERP · LOCAL · CONTRACT_MGMT · FINANCE · INTERACTIONS
         ↓
    BRONZE LAYER (Raw landing — 6 tables)
         ↓
    SILVER LAYER — Data Vault 2.0 (28 tables)
    ├── Cleansed:   SILVER_CRM, SILVER_ERP, SILVER_LOCAL...
    ├── Hub:        HUB_CUSTOMER (220 unique customers)
    ├── Satellites: SAT_CRM_CUSTOMER, SAT_ERP_CUSTOMER...
    ├── Links:      LINK_CUSTOMER_CONTRACT, LINK_CUSTOMER_REVENUE...
    ├── KPIs:       CUSTOMER_CHURN_RISK, CUSTOMER_HEALTH_SCORE...
    └── Audit:      PIPELINE_AUDIT (pipeline run history)
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

**Key business metrics:**
- 220 unique customers across 3 source systems
- $155.3M total revenue tracked
- Health, Churn Risk, and Renewal scores per customer
- 46 unresolved cross-source conflicts flagged by AI agent

---

## Flow A — Jira → Answer (Query Engine)

Create a Jira issue with a business question. Within 30 seconds, a comment appears with the answer pulled from live Snowflake data by an AWS Bedrock agent.

```
Jira: "How many customers have a churn risk score above 60?"
→ Comment: "There are 57 customers with a churn risk score above 60."
```

---

## Flow B — Natural Language Query via snow CLI

```powershell
$env:SNOWFLAKE_PAT = "your_pat_token"
.\ask.ps1 -Question "Show me the top 5 customers by revenue"
```
→ Calls native Snowflake MCP server → Cortex Analyst generates SQL → `snow` executes → real results.

---

## Flow C — Autonomous Pipeline Assessment

```
claude> Read customer360_metadata.yaml and run the full pipeline assessment
```

Claude Code autonomously:
- Runs 8 Bronze→Silver→Gold pipeline stages
- Executes 5 data quality checks
- Populates `PIPELINE_AUDIT` table in Snowflake
- Generates `assessment_report.md`

**Real findings surfaced:**
- `COMPLETENESS_SCORE` bug — flat value of 6 for all 220 customers
- `SILVER_ERP` schema drift — metadata YAML mismatches live table
- 46 unresolved cross-source conflicts (20 phone, 13 city, 13 pincode)
- Churned customers show hardcoded churn score of 100

---

## CI/CD Pipeline

On every push to `main` that touches `deploy.sql`:

```yaml
GitHub Push → Install Snowflake CLI → snow sql -f deploy.sql
           → Smoke test semantic view
           → Smoke test MCP server
           → Done
```

---

## Repository Structure

```
Customer360-MCP/
├── deploy.sql                     # Semantic view + MCP server DDL
├── customer360_metadata.yaml      # Metadata-driven pipeline config
├── assessment_report.md           # Latest pipeline assessment output
├── ask.ps1                        # snow CLI query client
├── server.py                      # Custom MCP server
├── Dockerfile                     # Container definition
├── requirements.txt               # Python dependencies
├── cli.py                         # MCP CLI client
├── voice_cli.py                   # Voice-enabled MCP client
└── .github/
    └── workflows/
        ├── docker-build.yml       # Docker image CI/CD
        └── snowflake-deploy.yml   # Snowflake objects CI/CD
```

**AWS Lambda functions (deployed separately):**
- `snowflake_query_action` — orchestrator (Jira → Bedrock → Snowflake → Jira)
- `customer360-schema-discovery` — CSV/S3 source schema discovery
- `customer360-pg-discovery` — PostgreSQL schema discovery + PII detection

**AWS Glue:**
- `customer360-pg-to-iceberg` — PostgreSQL → masked Parquet → S3

---

## Key Findings from Autonomous Assessment

Claude Code discovered these issues automatically during pipeline execution:

1. **`COMPLETENESS_SCORE` bug** — flat value of 6 for all 220 customers
2. **Schema drift** — `SILVER_ERP` metadata YAML describes order-grained schema but live table is customer-grained
3. **46 cross-source conflicts** — 20 phone, 13 city, 13 pincode disagreements in the golden record
4. **Churn score clamping** — all churned customers show exactly 100.00 churn score

---

## Setup

### Prerequisites
- AWS account (us-east-1) with Bedrock access
- Snowflake account (any region)
- Snowflake CLI (`snow`) installed
- GitHub account
- Jira project

### Deploy Snowflake Objects
```bash
# Add secrets to GitHub Actions, then:
git push  # triggers snowflake-deploy.yml automatically
```

### Query Snowflake via CLI
```powershell
$env:SNOWFLAKE_PAT = "your_pat_token"
.\ask.ps1 -Question "How many customers are at high churn risk?"
```

### Run Full Pipeline Assessment
```bash
claude  # inside project directory
> Read customer360_metadata.yaml and run the full pipeline and assessment
```

### Trigger PostgreSQL Discovery
Create a Jira issue with summary containing "PG Discovery" and connection details in the description. The platform handles everything else automatically.

---

## Architecture Patterns Demonstrated

- Data Vault 2.0 (Hub/Link/Satellite)
- Model Context Protocol (MCP) — custom and Snowflake-native
- Metadata-driven pipeline orchestration
- Agentic AI for autonomous data engineering
- PII detection and partial data masking
- Tool-agnostic ingestion (Glue adapter pattern)
- SQL-as-code with CI/CD
- Human-in-the-loop approval workflow (Jira)
- S3 Data Lake with Parquet/Iceberg

---

*Built by Badri Kaushik P — VIT Vellore, B.Tech + M.Tech CS (2028)*
*Corporate Internship Project — Customer360 AI Data Platform*
