from datetime import datetime
from pathlib import Path

import pandas as pd

from db.article_scores import (
    build_score_record,
    fetch_articles_to_score,
    upsert_article_scores,
)
from llm.score_articles import score_article


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs" / "article_scores"
LOG_DIR = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


LLM_PROVIDER = "openrouter"
LLM_MODEL = "google/gemini-3-flash-preview"
PROMPT_VERSION = "v1"


def score_articles_from_database(
    limit: int | None = None,
    output_csv: Path | None = None,
) -> pd.DataFrame:
    df = fetch_articles_to_score(
        llm_model=LLM_MODEL,
        prompt_version=PROMPT_VERSION,
        limit=limit,
    )

    if df.empty:
        print("No unscored articles found.")
        return pd.DataFrame()

    results = []
    records = []
    errors = []

    for _, row in df.iterrows():
        try:
            scores = score_article(
                company=row["company_name"],
                title=row["title"],
                paragraph=row["introduction"],
            )

            record = build_score_record(
                row=row,
                scores=scores,
                llm_provider=LLM_PROVIDER,
                llm_model=LLM_MODEL,
                prompt_version=PROMPT_VERSION,
            )
            records.append(record)

            result_row = {
                "article_id": row["article_id"],
                "company_name": row["company_name"],
                "source": row["source"],
                "title": row["title"],
                "introduction": row["introduction"],
                "published_at": row["published_at"],
                "url": row["url"],
                **scores,
            }
            results.append(result_row)

            print(f"[ok] Scored article_id={row['article_id']}")

        except Exception as e:
            errors.append(
                {
                    "article_id": row["article_id"],
                    "company_name": row["company_name"],
                    "url": row["url"],
                    "error": str(e),
                }
            )
            print(f"[fail] article_id={row['article_id']}: {e}")

    rows_upserted = upsert_article_scores(records)

    output_df = pd.DataFrame(results)

    if output_csv is not None and not output_df.empty:
        output_df.to_csv(output_csv, index=False)

    if errors:
        error_df = pd.DataFrame(errors)
        error_csv = output_csv.with_name(output_csv.stem + "_errors.csv") if output_csv else None
        if error_csv is not None:
            error_df.to_csv(error_csv, index=False)

    print(f"Rows scored: {len(results)}")
    print(f"Rows upserted: {rows_upserted}")

    return output_df


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = OUTPUT_DIR / f"articles_scored_{timestamp}.csv"

    df = score_articles_from_database(
        limit=None,
        output_csv=output_csv,
    )

    if not df.empty:
        print(df.head())
        print(f"Saved scored snapshot to: {output_csv}")