# Customer360 Pipeline & Assessment Report
Generated: 2026-06-19 11:22 (local)
Run ID: RUN_20260619_112254

---

## Pipeline Execution Summary

- **Total stages run:** 7 (8 audit rows — `refresh_kpis` has 4 targets, audited individually)
- **All stages status:** SUCCESS

| Stage | Source | Target | Rows | Status |
|---|---|---|---|---|
| bronze_to_silver_crm | BRONZE.CRM_RAW | SILVER.SILVER_CRM | 100 | SUCCESS |
| bronze_to_silver_erp | BRONZE.ERP_RAW | SILVER.SILVER_ERP | 100 | SUCCESS |
| silver_to_gold_hub | SILVER.SILVER_CRM | SILVER.HUB_CUSTOMER | 220 | SUCCESS |
| refresh_kpis | — | SILVER.CUSTOMER_CHURN_RISK | 220 | SUCCESS |
| refresh_kpis | — | SILVER.CUSTOMER_HEALTH_SCORE | 220 | SUCCESS |
| refresh_kpis | — | SILVER.CUSTOMER_RENEWAL_SCORE | 220 | SUCCESS |
| refresh_kpis | — | SILVER.CUSTOMER_REVENUE_METRICS | 220 | SUCCESS |
| refresh_golden_layer | — | SILVER.GOLDEN_CUSTOMER | 220 | SUCCESS |

> Note: this audit records row counts observed in source/target tables at execution time — it does not re-run the actual ELT transformations defined in the YAML (e.g. the `UPPER()`/`INITCAP()`/`MD5()` transforms), since those would require executing the pipeline code itself, not just auditing it.

---

## Data Quality Results

- **Total checks:** 5
- **Passed:** 3 | **Failed:** 2

| Check | Table | Result | Status |
|---|---|---|---|
| no_null_customer_id | SILVER_CRM | 0 nulls (expected 0) | PASS |
| no_duplicate_customer_id | SILVER_CRM | 0 duplicates (expected 0) | PASS |
| valid_email_format | SILVER_CRM | 0 invalid emails (expected 0) | PASS |
| no_null_order_id | SILVER_ERP | SQL compilation error: `invalid identifier 'ORDER_ID'` | **FAIL** |
| positive_amounts | SILVER_ERP | SQL compilation error: `invalid identifier 'AMOUNT'` | **FAIL** |

**Root cause of the 2 failures:** the YAML's `data_quality.rules` for `SILVER_ERP` assume columns `ORDER_ID` and `AMOUNT` exist. The live `SILVER_ERP` table actually has: `CUSTOMER_ID, FIRST_NAME, LAST_NAME, FULL_NAME, EMAIL, PHONE, CITY, PINCODE, COUNTRY, SOURCE_FILE, LOAD_TIMESTAMP, SOURCE_SYSTEM`. The YAML's `bronze_to_silver_erp` stage transformations (which reference `ORDER_ID`, `PRODUCT`, `AMOUNT`, `PAYMENT_STATUS`) also don't match this customer-attribute schema — **the metadata YAML appears to describe an order/transaction-grained ERP model that doesn't match the actual customer-grained ERP table currently deployed.** This is a metadata/schema drift issue, not a transient query bug.

---

## Business KPI Summary

| Health Level | Churn Risk Level | Customers | Revenue | Avg Health | Avg Churn |
|---|---|---|---|---|---|
| Healthy | Low Risk | 111 | $99,628,210.25 | 88.19 | 13.71 |
| Healthy | Medium Risk | 22 | $25,363,039.50 | 84.14 | 36.55 |
| At Risk | Churned | 34 | $10,097,702.50 | 13.68 | 100.00 |
| Moderate | Medium Risk | 14 | $8,259,549.25 | 53.43 | 40.93 |
| Moderate | Low Risk | 14 | $7,101,853.75 | 56.43 | 22.43 |
| Moderate | Churned | 22 | $4,132,335.50 | 50.09 | 100.00 |
| Moderate | High Risk | 1 | $676,117.50 | 65.00 | 65.00 |
| At Risk | Medium Risk | 2 | $0.00 | 35.50 | 35.00 |

**Total customers:** 220 | **Total revenue across all segments:** $155,258,808.25

Notable: the 2 "At Risk / Medium Risk" customers contribute **$0 revenue** — worth checking whether these are net-new/unbilled accounts or a data gap in `TOTAL_REVENUE`. Also, every "Churned" segment shows `avg_churn = 100.00` exactly, suggesting churned customers are hard-coded to a max churn score rather than independently calculated.

---

## Data Conflict Analysis

The YAML's `conflict_query` uses `CASE WHEN PHONE_CONFLICT THEN 1 ELSE 0 END`, which assumes these are BOOLEAN columns. Running it as-written fails:

```
SQL compilation error: Can not convert parameter 'CUSTOMER360_VIEW.PHONE_CONFLICT'
of type [VARCHAR(16777216)] into expected type [BOOLEAN]
```

`PHONE_CONFLICT`, `CITY_CONFLICT`, and `EMAIL_CONFLICT` are actually `VARCHAR` columns in `CUSTOMER360_VIEW` (holding conflict descriptions, not flags). Re-running with a VARCHAR-safe equivalent (`NOT NULL AND NOT IN ('None','')`) gives:

| Phone Conflicts | City Conflicts | Email Conflicts |
|---|---|---|
| 20 | 13 | 0 |

Email conflicts are 0 — consistent with email likely being the deterministic match key used to merge CRM/ERP/LOCAL records into the golden customer.

---

## Schema Inventory

| Schema | Table | Type | Row Count |
|---|---|---|---|
| BRONZE | CONTRACT_RAW | BASE TABLE | 1 |
| BRONZE | CRM_RAW | BASE TABLE | 1 |
| BRONZE | ERP_RAW | BASE TABLE | 1 |
| BRONZE | INTERACTION_RAW | BASE TABLE | 1 |
| BRONZE | LOCAL_RAW | BASE TABLE | 1 |
| BRONZE | REVENUE_RAW | BASE TABLE | 1 |
| SILVER | CONVERSATION_HISTORY | BASE TABLE | 0 |
| SILVER | CUSTOMER360_VIEW | VIEW | — |
| SILVER | CUSTOMER_CHURN_RISK | BASE TABLE | 220 |
| SILVER | CUSTOMER_HEALTH_SCORE | BASE TABLE | 220 |
| SILVER | CUSTOMER_RENEWAL_SCORE | BASE TABLE | 220 |
| SILVER | CUSTOMER_REVENUE_METRICS | BASE TABLE | 220 |
| SILVER | GOLDEN_CUSTOMER | BASE TABLE | 220 |
| SILVER | HUB_CUSTOMER | BASE TABLE | 220 |
| SILVER | LINK_CUSTOMER_CONTRACT | BASE TABLE | 220 |
| SILVER | LINK_CUSTOMER_INTERACTION | BASE TABLE | 875 |
| SILVER | LINK_CUSTOMER_REVENUE | BASE TABLE | 608 |
| SILVER | LSAT_CUSTOMER_CONTRACT | BASE TABLE | 220 |
| SILVER | LSAT_CUSTOMER_INTERACTION | BASE TABLE | 875 |
| SILVER | LSAT_CUSTOMER_REVENUE | BASE TABLE | 608 |
| SILVER | PIPELINE_AUDIT | BASE TABLE | 13 |
| SILVER | SAT_CONTRACTS | BASE TABLE | 220 |
| SILVER | SAT_CRM_CUSTOMER | BASE TABLE | 100 |
| SILVER | SAT_ERP_CUSTOMER | BASE TABLE | 100 |
| SILVER | SAT_INTERACTIONS | BASE TABLE | 875 |
| SILVER | SAT_LOCAL_CUSTOMER | BASE TABLE | 40 |
| SILVER | SAT_REVENUE | BASE TABLE | 608 |
| SILVER | SILVER_CONTRACTS | BASE TABLE | 220 |
| SILVER | SILVER_CRM | BASE TABLE | 100 |
| SILVER | SILVER_ERP | BASE TABLE | 100 |
| SILVER | SILVER_INTERACTIONS | BASE TABLE | 875 |
| SILVER | SILVER_LOCAL | BASE TABLE | 40 |
| SILVER | SILVER_REVENUE | BASE TABLE | 608 |
| SILVER | VOICE_QUERY_RESULTS | BASE TABLE | 0 |

(`PIPELINE_AUDIT` now shows 13 rows — this run's 8 pipeline-stage records plus 5 DQ-check records, all newly created.)

---

## Findings & Recommendations

1. **`SILVER_ERP` schema drift from pipeline metadata.** The YAML's `bronze_to_silver_erp` stage and its `data_quality` rules describe an order/transaction-grained ERP table (`ORDER_ID`, `PRODUCT`, `AMOUNT`, `PAYMENT_STATUS`), but the live `SILVER_ERP` table is customer-attribute-grained (`CUSTOMER_ID`, `EMAIL`, `PHONE`, etc.) with no such columns. This caused 2 of 5 DQ checks to fail with SQL compilation errors, not data-quality violations. **Action:** reconcile the YAML metadata with the actual deployed schema, or vice versa — right now the config is not executable against this table.

2. **`COMPLETENESS_SCORE` bug (carried over from prior assessment).** Every one of the 220 rows in `CUSTOMER360_VIEW` has an identical `COMPLETENESS_SCORE` of 6 (min = max = 6). This is almost certainly a broken per-row calculation in the view definition (e.g., a constant or mis-scoped aggregate) and should be fixed before this field is used in any reporting.

3. **Conflict query type mismatch.** The YAML's `conflict_query` assumes `PHONE_CONFLICT`/`CITY_CONFLICT`/`EMAIL_CONFLICT` are BOOLEAN, but they're VARCHAR in the live view, causing the query to fail outright. The corrected query shows 20 phone conflicts, 13 city conflicts, 0 email conflicts — these golden-record disagreements should be reviewed for survivorship-rule correctness.

4. **Churned customers show a hard 100.00 average churn score with no variance**, and 2 "At Risk/Medium Risk" customers report $0 revenue. Both patterns suggest scoring logic that clamps/defaults rather than computing dynamically — worth validating against the underlying `CUSTOMER_CHURN_RISK` and `CUSTOMER_REVENUE_METRICS` source logic.

5. **BRONZE tables show 1 row each** regardless of source file size (CRM, ERP, Interaction, Revenue, Contract, Local raw) — consistent with a variant/raw-payload landing pattern rather than one row per source record. This is expected for this architecture but worth confirming intentional.

---

## Audit Trail

`CUSTOMER_360.SILVER.PIPELINE_AUDIT` — all 13 rows from Run `RUN_20260619_112254`, most recent first:

| RUN_ID | STAGE_NAME | SOURCE_TABLE | TARGET_TABLE | ROWS_PROCESSED | STATUS | STARTED_AT |
|---|---|---|---|---|---|---|
| RUN_20260619_112254 | dq_positive_amounts | SILVER.SILVER_ERP | None | None | FAIL | 2026-06-18 23:00:48.144 |
| RUN_20260619_112254 | dq_no_null_order_id | SILVER.SILVER_ERP | None | None | FAIL | 2026-06-18 23:00:33.198 |
| RUN_20260619_112254 | dq_valid_email_format | SILVER.SILVER_CRM | None | 0 | PASS | 2026-06-18 23:00:18.595 |
| RUN_20260619_112254 | dq_no_duplicate_customer_id | SILVER.SILVER_CRM | None | 0 | PASS | 2026-06-18 23:00:03.682 |
| RUN_20260619_112254 | dq_no_null_customer_id | SILVER.SILVER_CRM | None | 0 | PASS | 2026-06-18 22:59:48.807 |
| RUN_20260619_112254 | refresh_golden_layer | None | SILVER.GOLDEN_CUSTOMER | 220 | SUCCESS | 2026-06-18 22:58:04.003 |
| RUN_20260619_112254 | refresh_kpis | None | SILVER.CUSTOMER_REVENUE_METRICS | 220 | SUCCESS | 2026-06-18 22:57:49.276 |
| RUN_20260619_112254 | refresh_kpis | None | SILVER.CUSTOMER_RENEWAL_SCORE | 220 | SUCCESS | 2026-06-18 22:57:34.608 |
| RUN_20260619_112254 | refresh_kpis | None | SILVER.CUSTOMER_HEALTH_SCORE | 220 | SUCCESS | 2026-06-18 22:57:20.000 |
| RUN_20260619_112254 | refresh_kpis | None | SILVER.CUSTOMER_CHURN_RISK | 220 | SUCCESS | 2026-06-18 22:57:05.173 |
| RUN_20260619_112254 | silver_to_gold_hub | SILVER.SILVER_CRM | SILVER.HUB_CUSTOMER | 220 | SUCCESS | 2026-06-18 22:56:38.315 |
| RUN_20260619_112254 | bronze_to_silver_erp | BRONZE.ERP_RAW | SILVER.SILVER_ERP | 100 | SUCCESS | 2026-06-18 22:56:23.667 |
| RUN_20260619_112254 | bronze_to_silver_crm | BRONZE.CRM_RAW | SILVER.SILVER_CRM | 100 | SUCCESS | 2026-06-18 22:56:08.629 |

(Timestamps shown in UTC as stored by `CURRENT_TIMESTAMP()`; local system clock was 2026-06-19 ~11:22 AM at run time.)
