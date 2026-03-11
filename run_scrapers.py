import asyncio
from pathlib import Path
from datetime import datetime

import pandas as pd

from scrapers.news_scrapers import ESGNewsScraper, ESGDiveScraper, ESGTodayScraper


COMPANY_NAMES = [
    "nike",
    "adidas",
    "puma",
    "lululemon",
    "h & m",
    "jd sports",
    "gap",
    "burberry",
    "columbia",
    "boohoo",
    "under armour"
]

OUTPUT_DIR = Path("outputs")
LOG_DIR = Path("logs")


async def scrape_all(companies, past_x_years=3, search_keywords="", verbose=True):
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
                    print(f"Saved {row_count} rows from {scraper.source} for {company_name}")
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
        combined_df = pd.concat(all_dfs, ignore_index=True)
    else:
        combined_df = pd.DataFrame(
            columns=["company_name", "source", "title", "introduction", "date", "url"]
        )

    summary_df = pd.DataFrame(summary_rows)
    errors_df = pd.DataFrame(errors)

    return combined_df, summary_df, errors_df


def write_run_log(
    log_path,
    companies,
    summary_df,
    errors_df,
    combined_df,
    output_csv_path,
    started_at,
    finished_at,
    past_x_years,
    search_keywords,
):
    total_runtime = finished_at - started_at

    lines = []
    lines.append(f"Run started: {started_at.isoformat()}")
    lines.append(f"Run finished: {finished_at.isoformat()}")
    lines.append(f"Duration: {total_runtime}")
    lines.append("")
    lines.append(f"Companies scraped: {', '.join(companies)}")
    lines.append(f"Search keywords: {search_keywords!r}")
    lines.append(f"Past X years: {past_x_years}")
    lines.append("")
    lines.append(f"Combined CSV output: {output_csv_path}")
    lines.append(f"Total rows in combined dataframe: {len(combined_df)}")
    lines.append("")

    lines.append("Results by company and source:")
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

    lines.append("")
    lines.append("Totals by source:")
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

    lines.append("")
    lines.append("Totals by company:")
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

    lines.append("")
    lines.append("Errors:")
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


async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

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

    if not errors_df.empty:
        errors_df.to_csv(error_csv_path, index=False)

    write_run_log(
        log_path=log_path,
        companies=COMPANY_NAMES,
        summary_df=summary_df,
        errors_df=errors_df,
        combined_df=combined_df,
        output_csv_path=output_csv_path,
        started_at=started_at,
        finished_at=finished_at,
        past_x_years=past_x_years,
        search_keywords=search_keywords,
    )

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", None)

    print("\n=== Combined DataFrame Preview ===")
    print(combined_df.head())

    print(f"\nSaved combined CSV to: {output_csv_path}")
    print(f"Saved summary CSV to: {summary_csv_path}")
    if not errors_df.empty:
        print(f"Saved error CSV to: {error_csv_path}")
    print(f"Saved run log to: {log_path}")
    print(f"Total rows: {len(combined_df)}")


if __name__ == "__main__":
    asyncio.run(main())