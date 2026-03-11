import asyncio
from datetime import datetime
from pathlib import Path

import pandas as pd

from db.articles import upsert_articles
from scrapers.article_scraper.news_scrapers import (
    ESGDiveScraper,
    ESGNewsScraper,
    ESGTodayScraper,
)


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs" / "articles"
LOG_DIR = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


COMPANY_NAMES = [
    "nike",
    "adidas",
    "puma",
    "lululemon",
    "jd sports",
    "burberry",
    "columbia",
    "boohoo",
    "under armour",
]


async def scrape_all(
    companies: list[str],
    past_x_years: int = 3,
    search_keywords: str = "",
    verbose: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scrapers = [
        ESGNewsScraper(verbose=verbose),
        ESGDiveScraper(verbose=verbose),
        ESGTodayScraper(verbose=verbose),
    ]

    all_dfs = []
    summary_rows = []
    errors = []

    for company_name in companies:
        print(f"\n=== Scraping company: {company_name} ===")

        for scraper in scrapers:
            print(f"--- Source: {scraper.source} ---")

            try:
                df = await scraper.scrape_news(
                    company_name=company_name,
                    search_keywords=search_keywords,
                    past_x_years=past_x_years,
                )

                row_count = len(df) if df is not None else 0

                summary_rows.append(
                    {
                        "company_name": company_name,
                        "source": scraper.source,
                        "rows_returned": row_count,
                        "status": "ok",
                    }
                )

                if df is not None and not df.empty:
                    all_dfs.append(df)
                    print(f"Collected {row_count} rows from {scraper.source} for {company_name}")
                else:
                    print(f"No rows found for {company_name} on {scraper.source}")

            except Exception as e:
                error_message = str(e)

                summary_rows.append(
                    {
                        "company_name": company_name,
                        "source": scraper.source,
                        "rows_returned": 0,
                        "status": "failed",
                    }
                )

                errors.append(
                    {
                        "company_name": company_name,
                        "source": scraper.source,
                        "error": error_message,
                    }
                )

                print(f"Failed for {company_name} on {scraper.source}: {error_message}")

    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True).drop_duplicates(subset=["url"])
    else:
        combined_df = pd.DataFrame(
            columns=["company_name", "source", "title", "introduction", "date", "url"]
        )

    summary_df = pd.DataFrame(summary_rows)
    errors_df = pd.DataFrame(errors)

    return combined_df, summary_df, errors_df


def write_run_log(
    log_path: Path,
    companies: list[str],
    summary_df: pd.DataFrame,
    errors_df: pd.DataFrame,
    combined_df: pd.DataFrame,
    output_csv_path: Path,
    summary_csv_path: Path,
    error_csv_path: Path | None,
    started_at: datetime,
    finished_at: datetime,
    past_x_years: int,
    search_keywords: str,
    db_rows_upserted: int,
) -> None:
    total_runtime = finished_at - started_at

    lines = [
        f"Run started: {started_at.isoformat()}",
        f"Run finished: {finished_at.isoformat()}",
        f"Duration: {total_runtime}",
        "",
        f"Companies scraped: {', '.join(companies)}",
        f"Search keywords: {search_keywords!r}",
        f"Past X years: {past_x_years}",
        "",
        f"Combined CSV output: {output_csv_path}",
        f"Summary CSV output: {summary_csv_path}",
        f"Error CSV output: {error_csv_path if error_csv_path else 'None'}",
        f"Total rows in combined dataframe: {len(combined_df)}",
        f"Rows upserted to database: {db_rows_upserted}",
        "",
        "Results by company and source:",
    ]

    if summary_df.empty:
        lines.append("  No scraper results recorded.")
    else:
        for _, row in summary_df.iterrows():
            lines.append(
                f"  - company={row['company_name']}, "
                f"source={row['source']}, "
                f"rows={row['rows_returned']}, "
                f"status={row['status']}"
            )

    lines.extend(["", "Totals by source:"])
    if summary_df.empty:
        lines.append("  No totals available.")
    else:
        source_totals = (
            summary_df.groupby("source", as_index=False)["rows_returned"]
            .sum()
            .sort_values("source")
        )
        for _, row in source_totals.iterrows():
            lines.append(f"  - {row['source']}: {row['rows_returned']} rows")

    lines.extend(["", "Totals by company:"])
    if summary_df.empty:
        lines.append("  No totals available.")
    else:
        company_totals = (
            summary_df.groupby("company_name", as_index=False)["rows_returned"]
            .sum()
            .sort_values("company_name")
        )
        for _, row in company_totals.iterrows():
            lines.append(f"  - {row['company_name']}: {row['rows_returned']} rows")

    lines.extend(["", "Errors:"])
    if errors_df.empty:
        lines.append("  None")
    else:
        for _, row in errors_df.iterrows():
            lines.append(
                f"  - company={row['company_name']}, "
                f"source={row['source']}, "
                f"error={row['error']}"
            )

    log_path.write_text("\n".join(lines), encoding="utf-8")


async def main() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_csv_path = OUTPUT_DIR / f"all_esg_articles_{timestamp}.csv"
    summary_csv_path = OUTPUT_DIR / f"scrape_summary_{timestamp}.csv"
    error_csv_path = OUTPUT_DIR / f"scrape_errors_{timestamp}.csv"
    log_path = LOG_DIR / f"scrape_run_{timestamp}.log"

    past_x_years = 3
    search_keywords = ""

    started_at = datetime.now()

    combined_df, summary_df, errors_df = await scrape_all(
        companies=COMPANY_NAMES,
        past_x_years=past_x_years,
        search_keywords=search_keywords,
        verbose=True,
    )

    finished_at = datetime.now()

    combined_df.to_csv(output_csv_path, index=False)
    summary_df.to_csv(summary_csv_path, index=False)

    saved_error_csv_path = None
    if not errors_df.empty:
        errors_df.to_csv(error_csv_path, index=False)
        saved_error_csv_path = error_csv_path

    db_rows_upserted = upsert_articles(combined_df)

    write_run_log(
        log_path=log_path,
        companies=COMPANY_NAMES,
        summary_df=summary_df,
        errors_df=errors_df,
        combined_df=combined_df,
        output_csv_path=output_csv_path,
        summary_csv_path=summary_csv_path,
        error_csv_path=saved_error_csv_path,
        started_at=started_at,
        finished_at=finished_at,
        past_x_years=past_x_years,
        search_keywords=search_keywords,
        db_rows_upserted=db_rows_upserted,
    )

    print("\n=== Combined DataFrame Preview ===")
    print(combined_df.head())

    print(f"\nSaved combined CSV to: {output_csv_path}")
    print(f"Saved summary CSV to: {summary_csv_path}")
    if saved_error_csv_path is not None:
        print(f"Saved error CSV to: {saved_error_csv_path}")
    print(f"Saved run log to: {log_path}")
    print(f"Total rows: {len(combined_df)}")
    print(f"Rows upserted to database: {db_rows_upserted}")


if __name__ == "__main__":
    asyncio.run(main())