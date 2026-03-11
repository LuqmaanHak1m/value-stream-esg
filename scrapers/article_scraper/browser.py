import time
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright


class BrowserMixin:
    async def start(self):
        self.log("Starting Playwright...")
        start = time.perf_counter()

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)

        elapsed = time.perf_counter() - start
        self.log(f"Browser started in {elapsed:.2f}s")

    async def close(self):
        self.log("Closing browser...")
        start = time.perf_counter()

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        elapsed = time.perf_counter() - start
        self.log(f"Browser closed in {elapsed:.2f}s")

    async def get_html(self, url, selector=None, wait=False):
        self.request_count += 1
        request_id = self.request_count

        self.log(f"[REQ {request_id}] Fetching: {url}")
        start = time.perf_counter()

        page = await self.browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded")

            if wait and selector:
                self.log(f"[REQ {request_id}] Waiting for selector: {selector}")
                await page.wait_for_selector(selector, timeout=15000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            elapsed = time.perf_counter() - start
            self.log(f"[REQ {request_id}] Done in {elapsed:.2f}s")
            return soup

        finally:
            await page.close()