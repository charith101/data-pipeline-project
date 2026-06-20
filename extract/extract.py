import os
import sys
import logging
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

WIKI_PROJECT = "en.wikipedia"
ACCESS = "all-access"
# Wikimedia rejects requests with no/generic User-Agent — put your real contact info in here
HEADERS = {"User-Agent": "data-pipeline-project/1.0 (contact: wijesinghecharith33@gmail.com)"}

# Pageview counts aren't finalized for ~24-48h, so we always pull 2 days back
RUN_DATE = datetime.now(timezone.utc) - timedelta(days=2)


def fetch_top_pageviews(date: datetime) -> list[dict]:
    """Call the Wikimedia 'top articles' endpoint for a single day."""
    year, month, day = date.strftime("%Y"), date.strftime("%m"), date.strftime("%d")

    # TODO 1: build the request URL using an f-string.
    # Pattern: https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{WIKI_PROJECT}/{ACCESS}/{year}/{month}/{day}
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{WIKI_PROJECT}/{ACCESS}/{year}/{month}/{day}"

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()  # crash loudly on 4xx/5xx instead of silently continuing

    data = response.json()
    return data["items"][0]["articles"]  # API nests the article list one level down


def transform(articles: list[dict], date: datetime) -> list[dict]:
    """Reshape raw API records into the rows we want in BigQuery."""
    loaded_at = datetime.now(timezone.utc).isoformat()
    rows = []

    for article in articles:
        # TODO 2: build one row dict per article (dict literal, like {"key": value, ...}).
        # Required keys -> values:
        #   "article"        -> article["article"]
        #   "views"          -> article["views"]
        #   "rank"            -> article["rank"]
        #   "pageview_date"  -> date.strftime("%Y-%m-%d")
        #   "loaded_at"      -> loaded_at (the variable defined above)
        row = {"article": article["article"], "views": article["views"], "rank": article["rank"], "pageview_date": date.strftime("%Y-%m-%d"), "loaded_at": loaded_at}
        rows.append(row)

    return rows


def load_to_bigquery(rows: list[dict], project_id: str) -> None:
    """Batch-load rows into raw_pipeline.wiki_top_pageviews (sandbox-safe — no streaming)."""
    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.raw_pipeline.wiki_top_pageviews"

    schema = [
        bigquery.SchemaField("article", "STRING"),
        bigquery.SchemaField("views", "INTEGER"),
        bigquery.SchemaField("rank", "INTEGER"),
        bigquery.SchemaField("pageview_date", "DATE"),
        bigquery.SchemaField("loaded_at", "TIMESTAMP"),
        # TODO 3: add the 3 remaining fields the same way as the lines above.
        # Names and types: rank -> INTEGER, pageview_date -> DATE, loaded_at -> TIMESTAMP
    ]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        # TODO 4: pick the write disposition that ADDS new rows instead of wiping the table.
        # Look at the bigquery.WriteDisposition class — it has 3 options, you want the "append" one.
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()  # blocks until the load finishes, raises if it fails
    logger.info(f"Loaded {len(rows)} rows into {table_id}")


def main():
    project_id = os.environ["GCP_PROJECT_ID"]
    logger.info(f"Fetching top pageviews for {RUN_DATE.strftime('%Y-%m-%d')}")

    articles = fetch_top_pageviews(RUN_DATE)
    rows = transform(articles, RUN_DATE)
    load_to_bigquery(rows, project_id)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Pipeline run failed")
        sys.exit(1)