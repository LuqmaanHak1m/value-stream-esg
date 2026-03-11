from datetime import datetime, timezone
from psycopg2.extras import execute_values
import pandas as pd

from db.connection import get_db_connection


SOURCE_NAME = "LSEG"

def df_to_records(df: pd.DataFrame) -> list[tuple]:
    scraped_at = datetime.now(timezone.utc)
    records = []

    for _, row in df.iterrows():
        if pd.notna(row.get("error")):
            continue

        company = None if pd.isna(row.get("company")) else row.get("company")
        industry = None if pd.isna(row.get("industry")) else row.get("industry")
        category = None if pd.isna(row.get("category")) else row.get("category")
        metric = None if pd.isna(row.get("metric")) else row.get("metric")

        score = row.get("score")
        if pd.isna(score):
            score = None
        else:
            score = float(score)

        records.append(
            (
                company,
                industry,
                category,
                metric,
                score,
                SOURCE_NAME,
                scraped_at,
            )
        )

    return records


def upsert_esg_scores(df: pd.DataFrame) -> None:
    records = df_to_records(df)

    if not records:
        print("No valid ESG records to upsert.")
        return

    query = """
        INSERT INTO public.esg_scores
            (company, industry, category, metric, score, source, scraped_at)
        VALUES %s
        ON CONFLICT (company, category, metric, source)
        DO UPDATE SET
            industry = EXCLUDED.industry,
            score = EXCLUDED.score,
            scraped_at = EXCLUDED.scraped_at,
            updated_at = now()
    """

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, query, records, page_size=500)
        print(f"Upserted {len(records)} rows into esg_scores")
    finally:
        conn.close()