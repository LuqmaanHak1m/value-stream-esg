from .base_scraper import BaseScraper


class ESGNewsScraper(BaseScraper):
    source = "ESG News"
    site_url = "https://esgnews.com"

    results_article_selector = "div.tw-max-w-sm.md\\:tw-max-w-prose"
    title_selector = "h2 a"
    link_selector = "h2 a"

    next_page_selector = "a.next.page-numbers"

    def build_search_url(self, company_name, search_keywords):
        query = f"{company_name} {search_keywords}".strip().replace(" ", "+")
        return f"{self.site_url}/?s={query}&orderby=newest&order=DESC"

class ESGDiveScraper(BaseScraper):
    source = "ESG Dive"
    site_url = "https://www.esgdive.com"

    results_article_selector = "div.columns"
    title_selector = "h3.feed__title a"
    link_selector = "h3.feed__title a"
    date_selector = "span.secondary-label"
    next_page_selector = "div.pagination a.button.button--soft"
 

    def build_search_url(self, company_name, search_keywords):
        query = f"{company_name} {search_keywords}".strip().replace(" ", "+")
        return (
            f"{self.site_url}/search/"
            f"?page=1&q={query}"
            f"&selected_facets=section_exact%3Anews"
            f"&topics=&sortby=on"
        )
    
class ESGTodayScraper(BaseScraper):
    source = "ESG Today"
    site_url = "https://www.esgtoday.com"

    results_article_selector = "div#loops-wrapper article.post"
    title_selector = "h2.post-title a"
    link_selector = "h2.post-title a"
    date_selector = "time.post-date"

    #ESG today does not allow sorting by date
    use_date_cutoff = False

    def build_search_url(self, company_name, search_keywords):
        query = f"{company_name} {search_keywords}".strip().replace(" ", "+")
        return f"{self.site_url}/?s={query}"

    # There is no next button, just page numbers
    def get_next_page_url(self, soup, current_url):
        current_page = soup.select_one("div.pagenav span.number.current")
        if not current_page:
            return None

        try:
            current_num = int(current_page.get_text(strip=True))
        except ValueError:
            return None

        for link in soup.select("div.pagenav a.number"):
            try:
                page_num = int(link.get_text(strip=True))
            except ValueError:
                continue

            if page_num == current_num + 1:
                return link.get("href")

        return None