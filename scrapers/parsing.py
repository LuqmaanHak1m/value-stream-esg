import datetime
from urllib.parse import urljoin


class ParsingMixin:
    def get_articles(self, soup):
        return soup.select(self.results_article_selector)

    def get_title(self, article):
        title_el = article.select_one(self.title_selector)
        if not title_el:
            return None
        return title_el.get_text(" ", strip=True)

    def clean_date_text(self, date_text):
        prefixes = ["Posted:", "Published:", "Updated:"]
        for prefix in prefixes:
            date_text = date_text.replace(prefix, "")
        return date_text.strip()
    
    def parse_date(self, date_text):
        date_formats = [
            "%B %d, %Y",   # March 5, 2026
            "%b. %d, %Y",  # Feb. 25, 2026
            "%b %d, %Y",   # Feb 25, 2026
        ]

        for fmt in date_formats:
            try:
                return datetime.datetime.strptime(date_text, fmt)
            except ValueError:
                continue

        return None
    
    def get_date(self, article):
        date_elements = article.select(self.date_selector)
        if not date_elements:
            return None

        for date_el in date_elements:
            date_text = date_el.get_text(" ", strip=True)
            date_text = self.clean_date_text(date_text)
            parsed_date = self.parse_date(date_text)

            if parsed_date is not None:
                return parsed_date

        return None
    

    def get_article_link(self, article):
        link_el = article.select_one(self.link_selector)
        if not link_el:
            return None

        href = link_el.get("href")
        if not href:
            return None

        return urljoin(self.site_url, href)

    def get_introduction_from_page_soup(self, page_soup):
        article = page_soup.select_one(self.intro_article_selector)
        if not article:
            return None

        for p in article.select(self.intro_paragraph_selector):
            text = p.get_text(" ", strip=True)
            if text:
                return text

        return None

    async def get_introduction_from_url(self, url):
        if not url:
            return None

        try:
            page_soup = await self.get_html(url)
            return self.get_introduction_from_page_soup(page_soup)
        except Exception as e:
            self.log(f"Failed to fetch introduction from {url}: {e}")
            return None

    def get_next_page_url(self, soup, current_url):
        links = soup.select(self.next_page_selector)
        if not links:
            return None

        for link in links:
            text = link.get_text(" ", strip=True)

            if "Next" in text:
                href = link.get("href")
                if href:
                    return urljoin(current_url, href)

        return None