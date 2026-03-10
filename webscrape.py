import asyncio
import argparse
from playwright.async_api import async_playwright


async def scrape(url, selector=None, wait=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        if wait and selector:
            await page.wait_for_selector(selector, timeout=15000)
        html = await page.content()
        await browser.close()
        with open("page.html", "w", encoding="utf-8") as f:
            f.write(html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--url", required=True)
    parser.add_argument("--selector", default=None)
    parser.add_argument("--wait", action="store_true")

    args = parser.parse_args()

    asyncio.run(scrape(args.url, selector=args.selector, wait=args.wait))