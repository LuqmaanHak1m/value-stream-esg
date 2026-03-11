import asyncio
import argparse
import time
import sys
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def scrape(
    url,
    selector=None,
    wait=False,
    verbose=False,
    retries=4,
    timeout=10000,
    retry_delay=2
):
    last_error = None

    for attempt in range(1, retries + 1):
        browser = None
        try:
            if verbose:
                print(f"[webscrape] Attempt {attempt}/{retries}: {url}", file=sys.stderr)

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

                # give JS a moment even after domcontentloaded
                await page.wait_for_timeout(3000)

                if wait and selector:
                    await page.wait_for_selector(selector, timeout=timeout)

                html = await page.content()

                # extra validation: did the ESG block really appear?
                if selector and selector not in html:
                    raise RuntimeError("Page loaded but target selector content not found in HTML")

                with open("page.html", "w", encoding="utf-8") as f:
                    f.write(html)

                return

        except Exception as e:
            last_error = e
            print(f"[webscrape] Attempt {attempt} failed: {e}", file=sys.stderr)

        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass

        if attempt < retries:
            await asyncio.sleep(retry_delay)

    raise RuntimeError(f"Failed after {retries} attempts for {url}. Last error: {last_error}")