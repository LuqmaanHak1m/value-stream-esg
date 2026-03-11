from datetime import datetime, timezone
from typing import Any

import pandas as pd
from psycopg2.extras import execute_values

from db.connection import get_db_connection


def normalise_article_records(df: pd.DataFrame) -> list[tuple[Any, ...]]:
    scraped_at = datetime.now(timezone.utc)
    records: list[tuple[Any, ...]] = []

    for _, row in df.iterrows():
        company_name = None if pd.isna(row.get("company_name")) else row.get("company_name")
        source = None if pd.isna(row.get("source")) else row.get("source")
        title = None if pd.isna(row.get("title")) else row.get("title")
        introduction = None if pd.isna(row.get("introduction")) else row.get("introduction")
        url = None if pd.isna(row.get("url")) else row.get("url")

        published_at = row.get("date")
        if pd.isna(published_at):
            published_at = None
        else:
            published_at = pd.to_datetime(published_at, errors="coerce")
            if pd.isna(published_at):
                published_at = None
            else:
                published_at = published_at.to_pydatetime()

        if not url or not title or not source or not company_name:
            continue

        records.append(
            (
                company_name,
                source,
                title,
                introduction,
                published_at,
                url,
                scraped_at,
            )
        )

    return records


def upsert_articles(df: pd.DataFrame) -> int:
    records = normalise_article_records(df)

    if not records:
        print("No valid article records to upsert.")
        return 0

    query = """
        INSERT INTO public.articles
            (company_name, source, title, introduction, published_at, url, scraped_at)
        VALUES %s
        ON CONFLICT (url)
        DO UPDATE SET
            company_name = EXCLUDED.company_name,
            source = EXCLUDED.source,
            title = EXCLUDED.title,
            introduction = EXCLUDED.introduction,
            published_at = EXCLUDED.published_at,
            scraped_at = EXCLUDED.scraped_at,
            updated_at = now()
    """

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, query, records, page_size=500)
        print(f"Upserted {len(records)} rows into articles")
        return len(records)
    finally:
        conn.close()