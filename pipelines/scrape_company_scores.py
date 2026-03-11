import asyncio

from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.async_api import async_playwright

from db.esg_scores import upsert_esg_scores

load_dotenv()


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs" / "company_scores"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "esg_scores.csv"


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
NAME_MAP = {
    "Adidas": "Adidas AG",
    "Nike": "Nike Inc",
    "Puma": "Puma SE",
    "Lululemon": "Lululemon Athletica Inc",
    "H & M": "H & M Hennes & Mauritz AB",
    "JD Sports": "JD Sports Fashion PLC",
    "Gap": "Gap Inc",
    "Burberry": "Burberry Group PLC",
    "Columbia": "Columbia Sportswear Co",
    "Boohoo": "Boohoo Group PLC",
    "Under Armour": "Under Armour Inc",
}


BASE_SITE = "https://www.lseg.com/en/data-analytics/sustainable-finance/sustainability-ratings-and-data"


# -----------------------------------------------------------------------------
# Scraping helpers
# -----------------------------------------------------------------------------
async def get_html(
    url: str,
    selector: str | None = None,
    wait: bool = False,
    timeout: int = 20000,
    verbose: bool = True,
) -> BeautifulSoup:
    browser = None
    try:
        if verbose:
            print(f"[scrape] Loading: {url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            await page.wait_for_timeout(5000)

            if wait and selector:
                await page.wait_for_selector(selector, timeout=timeout)

            html = await page.content()
            return BeautifulSoup(html, "html.parser")

    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass


async def build_esg_data(esg_data: dict, company_name: str) -> dict:
    encoded_name = quote_plus(NAME_MAP[company_name])
    full_site_link = f"{BASE_SITE}?esg={encoded_name}"
    print(full_site_link)

    soup = await get_html(
        full_site_link,
        selector="div.EsgRatings.EsgRatings--rating",
        wait=True,
        timeout=20000,
    )

    esg_container = soup.select_one("div.EsgRatings.EsgRatings--rating")
    if esg_container is None:
        raise RuntimeError(f"No ESG container found for {company_name}")

    industry_div = soup.select_one("div.EsgRatings.EsgRatings--rank p")
    if industry_div is None:
        raise RuntimeError(f"No industry found for {company_name}")

    industry = (
        industry_div.get_text(strip=True)
        .replace("Out of ", "")
        .replace(" Companies.", "")
        .strip()
    )

    categories = esg_container.find_all("div", class_="EsgRatings EsgRatings--category")

    esg_data[company_name] = {"industry": industry}

    for category in categories:
        h5 = category.find("h5")
        if not h5:
            continue

        cat_name = h5.get_text(strip=True)
        esg_data[company_name][cat_name] = {}

        sub_cats = category.find_all("div", class_="EsgRatings EsgRatings--item")

        for sub_cat in sub_cats:
            text = sub_cat.get_text(" ", strip=True)
            parts = text.rsplit(" ", 1)

            if len(parts) != 2:
                continue

            sub_cat_name, score = parts
            esg_data[company_name][cat_name][sub_cat_name] = score

    return esg_data


def build_dataframe(esg_data: dict) -> pd.DataFrame:
    rows = []

    for company, categories in esg_data.items():
        industry = categories.get("industry")

        if "error" in categories:
            rows.append(
                {
                    "company": company,
                    "industry": None,
                    "category": None,
                    "metric": None,
                    "score": None,
                    "error": categories["error"],
                }
            )
            continue

        for category, metrics in categories.items():
            if category == "industry":
                continue

            for metric, score in metrics.items():
                rows.append(
                    {
                        "company": company,
                        "industry": industry,
                        "category": category,
                        "metric": metric,
                        "score": score,
                        "error": None,
                    }
                )

    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Pipeline
# -----------------------------------------------------------------------------
async def scrape_round(companies, esg_data, delay_between_companies=2):
    failed = []

    for company in companies:
        try:
            esg_data = await build_esg_data(esg_data, company)
            print(f"[ok] {company}")
        except Exception as e:
            print(f"[fail] {company}: {e}")
            failed.append(company)

        await asyncio.sleep(delay_between_companies)

    return esg_data, failed


async def main():
    esg_data = {}

    print("\n=== ROUND 1 ===")
    esg_data, failed = await scrape_round(NAME_MAP.keys(), esg_data, delay_between_companies=2)

    if failed:
        print(f"\nSleeping before retry round 2... ({len(failed)} failures)")
        await asyncio.sleep(15)

        print("\n=== ROUND 2 ===")
        esg_data, failed_round_2 = await scrape_round(failed, esg_data, delay_between_companies=4)
    else:
        failed_round_2 = []

    if failed_round_2:
        print(f"\nSleeping before retry round 3... ({len(failed_round_2)} failures)")
        await asyncio.sleep(30)

        print("\n=== ROUND 3 ===")
        esg_data, final_failed = await scrape_round(failed_round_2, esg_data, delay_between_companies=6)
    else:
        final_failed = []

    for company in final_failed:
        esg_data[company] = {"error": "Failed after all retry rounds"}

    df = build_dataframe(esg_data)
    print(df)

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to {OUTPUT_FILE}")

    upsert_esg_scores(df)
    print("\nUpserted ESG data to database")

    if final_failed:
        print("\nStill failed:")
        for company in final_failed:
            print(f"- {company}")


if __name__ == "__main__":
    asyncio.run(main())