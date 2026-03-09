import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

URL = "https://www.lseg.com/en/data-analytics/sustainable-finance/sustainability-ratings-and-data?esg=Adidas+AG"

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL, wait_until="networkidle")
        html = await page.content()
        await browser.close()

        soup = BeautifulSoup(html, "html.parser")
        print(soup.select_one("div.EsgRatings.EsgRatings--rating"))

if __name__ == "__main__":
    asyncio.run(scrape())