import asyncio
import argparse
import time
import sys
from playwright.async_api import async_playwright


async def scrape(url, selector=None, wait=False, verbose=False):
    start = time.time()

    if verbose:
        print(f"[webscrape] Starting browser for: {url}", file=sys.stderr)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        if verbose:
            print(f"[webscrape] Browser launched", file=sys.stderr)

        page = await browser.new_page()

        if verbose:
            print(f"[webscrape] Navigating to: {url}", file=sys.stderr)

        await page.goto(url, wait_until="domcontentloaded")

        if wait and selector:
            if verbose:
                print(f"[webscrape] Waiting for selector: {selector}", file=sys.stderr)
            await page.wait_for_selector(selector, timeout=15000)

        html = await page.content()

        if verbose:
            print(f"[webscrape] Writing page.html", file=sys.stderr)

        with open("page.html", "w", encoding="utf-8") as f:
            f.write(html)

        await browser.close()

    elapsed = time.time() - start
    if verbose:
        print(f"[webscrape] Finished in {elapsed:.2f}s", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--selector", default=None)
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    asyncio.run(
        scrape(
            args.url,
            selector=args.selector,
            wait=args.wait,
            verbose=args.verbose
        )
    )