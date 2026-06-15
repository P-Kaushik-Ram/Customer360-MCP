-- ============================================================
-- Customer360 Semantic View + Native MCP Server
-- Deployed via GitHub Actions using snow CLI
-- ============================================================

CREATE OR REPLACE SEMANTIC VIEW CUSTOMER_360.SILVER.CUSTOMER360_SV
  TABLES (
    CUST AS CUSTOMER_360.SILVER.CUSTOMER360_VIEW
      PRIMARY KEY (CUSTOMER_ID)
      WITH SYNONYMS ('customers', 'customer 360', 'customer base')
      COMMENT = 'Golden customer record with KPI scores, contract, and conflict flags'
  )
  DIMENSIONS (
    CUST.CUSTOMER_ID AS CUSTOMER_ID WITH SYNONYMS ('customer id') COMMENT = 'Unique customer identifier',
    CUST.FULL_NAME AS FULL_NAME COMMENT = 'Customer full name',
    CUST.FIRST_NAME AS FIRST_NAME COMMENT = 'Customer first name',
    CUST.LAST_NAME AS LAST_NAME COMMENT = 'Customer last name',
    CUST.EMAIL AS EMAIL COMMENT = 'Customer email address',
    CUST.PHONE AS PHONE COMMENT = 'Customer phone number',
    CUST.CITY AS CITY WITH SYNONYMS ('location') COMMENT = 'Customer city',
    CUST.COUNTRY AS COUNTRY COMMENT = 'Customer country',
    CUST.PINCODE AS PINCODE COMMENT = 'Customer postal code',
    CUST.PRIMARY_SOURCE AS PRIMARY_SOURCE COMMENT = 'Source system that won survivorship for this field set',
    CUST.LOAD_TIMESTAMP AS LOAD_TIMESTAMP COMMENT = 'Timestamp the record was loaded',
    CUST.COMPLETENESS_SCORE AS COMPLETENESS_SCORE COMMENT = 'Data completeness score',
    CUST.CONTRACT_STATUS AS CONTRACT_STATUS WITH SYNONYMS ('contract state') COMMENT = 'ACTIVE, RENEWED, EXPIRING_SOON, or CHURNED',
    CUST.NEXT_RENEWAL_DATE AS NEXT_RENEWAL_DATE COMMENT = 'Next contract renewal date',
    CUST.DAYS_TO_RENEWAL AS DAYS_TO_RENEWAL COMMENT = 'Days remaining until next renewal',
    CUST.HEALTH_SCORE AS HEALTH_SCORE COMMENT = 'Customer health score 0-100',
    CUST.HEALTH_LEVEL AS HEALTH_LEVEL WITH SYNONYMS ('health status') COMMENT = 'Healthy, Moderate, or At Risk',
    CUST.CHURN_RISK_SCORE AS CHURN_RISK_SCORE COMMENT = 'Churn risk score 0-100',
    CUST.CHURN_RISK_LEVEL AS CHURN_RISK_LEVEL WITH SYNONYMS ('churn risk') COMMENT = 'Low Risk, Medium Risk, High Risk, or Churned',
    CUST.RENEWAL_LIKELIHOOD_SCORE AS RENEWAL_LIKELIHOOD_SCORE COMMENT = 'Renewal likelihood score 0-100',
    CUST.RENEWAL_LIKELIHOOD_BAND AS RENEWAL_LIKELIHOOD_BAND COMMENT = 'High, Medium, or Not Applicable',
    CUST.PHONE_CONFLICT AS PHONE_CONFLICT COMMENT = 'Flag: phone disagrees across source systems',
    CUST.CITY_CONFLICT AS CITY_CONFLICT COMMENT = 'Flag: city disagrees across source systems',
    CUST.EMAIL_CONFLICT AS EMAIL_CONFLICT COMMENT = 'Flag: email disagrees across source systems',
    CUST.PINCODE_CONFLICT AS PINCODE_CONFLICT COMMENT = 'Flag: pincode disagrees across source systems'
  )
  METRICS (
    CUST.ACV AS SUM(CUST.ACV) COMMENT = 'Total annual contract value',
    CUST.TOTAL_REVENUE AS SUM(CUST.TOTAL_REVENUE) COMMENT = 'Total lifetime revenue'
  );

CREATE OR REPLACE MCP SERVER CUSTOMER_360.SILVER.CUSTOMER360_MCP FROM SPECIFICATION $$
tools:
  - name: "ask_customer360"
    type: "CORTEX_ANALYST_MESSAGE"
    identifier: "CUSTOMER_360.SILVER.CUSTOMER360_SV"
    description: "Answer natural language questions about Customer360 data - customers, revenue, contracts, churn risk, health scores, and renewal likelihood."
    title: "Customer360 Analyst"
$$;