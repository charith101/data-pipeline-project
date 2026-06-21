# Wikipedia Trending Topics Pipeline

An automated ELT pipeline that tracks daily top Wikipedia articles and surfaces
trending topics, built end-to-end with the same kind of stack used in
production data teams.

## Architecture

\`\`\`mermaid
flowchart LR
    A[Wikipedia Pageviews API] --> B[Python Extractor]
    B --> C[(BigQuery: raw_pipeline)]
    C --> D[dbt staging models]
    D --> E[dbt mart models]
    E --> F[(BigQuery: analytics_pipeline)]
    F --> G[Looker Studio Dashboard]
    H[GitHub Actions — daily cron] -.triggers.-> B
    H -.triggers.-> D
\`\`\`

## Tech stack
| Layer | Tool |
|---|---|
| Extraction | Python (`requests`) |
| Storage / warehouse | Google BigQuery (Sandbox, free tier) |
| Transformation | dbt Core |
| Data quality | dbt schema + custom singular tests |
| Orchestration | GitHub Actions (daily cron + manual trigger) |
| Visualization | Looker Studio |

## What it does
Every day, the pipeline pulls the ~1,000 most-viewed English Wikipedia
articles from the official Wikimedia API, loads them into BigQuery, and
runs dbt models that calculate each article's view count against its own
7-day rolling baseline — surfacing which topics are currently trending up
or down versus their normal traffic.

## Setup
1. Clone the repo, create a venv, `pip install -r requirements.txt`
2. Create a GCP project with BigQuery Sandbox enabled, plus `raw_pipeline`
   and `analytics_pipeline` datasets
3. Create a service account with `BigQuery Data Editor` + `BigQuery Job User`,
   and add its key + your project ID as GitHub Actions secrets
   (`GCP_SA_KEY`, `GCP_PROJECT_ID`)
4. Push to `main` — the GitHub Actions workflow runs automatically every day,
   or trigger it manually from the Actions tab

## Dashboard
https://datastudio.google.com/reporting/904e9528-ae98-439c-b912-6d4c34906e69

## How I'd scale this in production
- Swap the BigQuery Sandbox for a billed BigQuery project to remove the
  60-day table expiry and DML restrictions, enabling true incremental
  dbt models instead of full-refresh
- Replace the long-lived service account JSON key with Workload Identity
  Federation, so GitHub Actions authenticates without a stored credential
- Move orchestration to Airflow or Dagster for retries, backfills, and
  dependency-aware scheduling across multiple pipelines
- Add alerting (Slack/email) on pipeline or test failures
- Host `dbt docs` for a browsable data catalog and lineage graph
- Add CI that runs `dbt test` on every pull request before merging to main