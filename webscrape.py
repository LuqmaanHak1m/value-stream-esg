import asyncio
import argparse
from playwright.async_api import async_playwright

async def scrape(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        html = await page.content()
        await browser.close()

        with open("page.html", "w", encoding="utf-8") as f:
            f.write(html)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()

    asyncio.run(scrape(args.url))