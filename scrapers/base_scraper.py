import datetime
import time
import pandas as pd

from .browser import BrowserMixin
from .parsing import ParsingMixin
from .logging_utils import LoggerMixin


class BaseScraper(LoggerMixin, BrowserMixin, ParsingMixin):
    source = "Unknown"
    site_url = ""
    sorting = ""

    title_selector = "a"
    date_selector = "time"
    date_format = "%B %d, %Y"
    link_selector = "a"

    results_article_selector = "article"
    intro_article_selector = "article"
    intro_paragraph_selector = "p"

    next_page_selector = "a.next.page-numbers"

    use_date_cutoff = True

    def __init__(self, verbose=True):
        self.playwright = None
        self.browser = None
        self.verbose = verbose
        self.request_count = 0

    def build_search_url(self, company_name, search_keywords):
        raise NotImplementedError

    async def parse_article(self, article, company_name, article_num=None, total_articles=None):
        if article_num is not None and total_articles is not None:
            self.log(f"Parsing article {article_num}/{total_articles}")

        title = self.get_title(article)
        if title:
            self.log(f"Title: {title}")

        try:
            date = self.get_date(article)
        except Exception as e:
            self.log(f"Could not parse date: {e}")
            date = None

        try:
            url = self.get_article_link(article)
        except Exception as e:
            self.log(f"Could not parse article link: {e}")
            url = None

        try:
            introduction = await self.get_introduction_from_url(url)
        except Exception as e:
            self.log(f"Could not fetch introduction: {e}")
            introduction = None

        return {
            "company_name": company_name,
            "source": self.source,
            "title": title,
            "introduction": introduction,
            "date": date,
            "url": url,
        }

    def should_stop_pagination(self, row_date, min_year):
        if row_date is None:
            return False
        return row_date.year < min_year

    async def scrape_news(self, company_name, search_keywords="", past_x_years=3):
        min_year = datetime.datetime.today().year - past_x_years
        full_url = self.build_search_url(company_name, search_keywords)

        rows = []
        page_num = 1
        total_start = time.perf_counter()

        self.log(f"Starting scrape for company='{company_name}', search_keywords='{search_keywords}', past_x_years={past_x_years}")
        self.log(f"Minimum year allowed: {min_year}")
        self.log(f"Initial URL: {full_url}")

        await self.start()
        try:
            while full_url:
                self.log(f"--- Results page {page_num} ---")
                soup = await self.get_html(full_url)
                articles = self.get_articles(soup)
                self.log(f"Found {len(articles)} articles on page {page_num}")

                stop_pagination = False

                for i, article in enumerate(articles, start=1):
                    try:
                        row = await self.parse_article(
                            article,
                            company_name,
                            article_num=i,
                            total_articles=len(articles),
                        )

                        if row["date"] is None:
                            self.log("Skipping article because date is missing")
                            continue

                        if self.use_date_cutoff and self.should_stop_pagination(row["date"], min_year):
                            self.log(
                                f"Stopping pagination because article date {row['date'].date()} is older than minimum year {min_year}"
                            )
                            stop_pagination = True
                            break

                        rows.append(row)
                        self.log(f"Saved article {i}/{len(articles)}; total saved so far: {len(rows)}")

                    except Exception as e:
                        self.log(f"Error parsing article {i}: {e}")
                        continue

                if stop_pagination:
                    break

                next_url = self.get_next_page_url(soup, full_url)
                if next_url:
                    self.log(f"Next page found: {next_url}")
                else:
                    self.log("No next page found")

                full_url = next_url
                page_num += 1

        finally:
            await self.close()

        elapsed = time.perf_counter() - total_start
        self.log(f"Finished scrape. Total rows: {len(rows)}. Total time: {elapsed:.2f}s")

        return pd.DataFrame(rows)