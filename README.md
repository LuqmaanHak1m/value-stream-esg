# ESG News Scraper

This project scrapes ESG-related news articles about specific companies from multiple ESG news websites and aggregates the results into a single dataset.

Currently supported sources:

- ESG News
- ESG Dive
- ESG Today

The scraper collects:

- company name
- source
- article title
- introduction snippet
- publication date
- article URL

All results are combined into a single CSV file, and a log file summarises the run.

---

# Features

- Async scraping using Playwright
- Modular scraper architecture
- Multiple sources supported
- Per-run logging with timestamp
- CSV export of all scraped articles
- Error reporting
- Site-specific parsing rules
- Shared scraping framework for easy extension

---

# Project Structure

```
value-stream-esg/
│
├── run_scrapers.py
│
├── scrapers/
│   ├── base_scraper.py
│   ├── parsing.py
│   ├── browser.py
│   ├── logging_utils.py
│   └── news_scrapers.py
│
├── outputs/
│   └── (generated CSV files)
│
├── logs/
│   └── (run summary logs)
│
└── README.md
```

---

# Scraper Architecture

The framework uses a modular mixin-based architecture.

## BaseScraper

The main orchestration class that controls:

- browser lifecycle
- pagination
- article parsing workflow
- dataframe creation

```
BaseScraper
 ├── LoggerMixin
 ├── BrowserMixin
 └── ParsingMixin
```

---

# Mixins

## BrowserMixin

Handles Playwright browser operations.

Responsibilities:

- starting the browser
- opening pages
- retrieving HTML
- closing browser sessions

---

## ParsingMixin

Handles extraction of data from HTML.

Functions include:

- finding article containers
- extracting titles
- extracting links
- parsing dates
- extracting introduction text
- pagination handling

---

## LoggerMixin

Handles structured console logging during scraping.

Example output:

```
[14:07:14] Starting scrape
[14:07:15] Fetching page
[14:07:20] Found 20 articles
[14:07:21] Saved article
```

---

# Site-Specific Scrapers

Each website gets a small subclass defining selectors and search behaviour.

Example:

```
class ESGDiveScraper(BaseScraper):
```

Responsibilities:

- search URL format
- CSS selectors
- pagination logic if needed

---

# Supported Websites

## ESG News

```
https://esgnews.com
```

Example search:

```
https://esgnews.com/?s=nike
```

Sorted by newest.

---

## ESG Dive

```
https://www.esgdive.com
```

Example search:

```
https://www.esgdive.com/search/?q=nike
```

Pagination handled via a Next button.

---

## ESG Today

```
https://www.esgtoday.com
```

Example search:

```
https://www.esgtoday.com/?s=nike
```

Pagination handled via numbered pages.

---

# Running the Scraper

Run the scraper with:

```
python run_scrapers.py
```

The script will:

1. search all companies
2. scrape all supported sites
3. merge results
4. export CSV
5. generate run logs

---

# Configuring Companies

Edit the list in `run_scrapers.py`:

```python
COMPANY_NAMES = [
    "nike",
    "adidas",
    "puma",
]
```

---

# Output Files

Each run generates timestamped files.

Example:

```
outputs/all_esg_articles_20260310_153210.csv
outputs/scrape_summary_20260310_153210.csv
outputs/scrape_errors_20260310_153210.csv

logs/scrape_run_20260310_153210.log
```

---

# Example CSV Output

| company_name | source | title | introduction | date | url |
|---|---|---|---|---|---|
| nike | ESG News | Nike appoints CSO | Nike has appointed... | 2026-03-04 | https://... |

---

# Log File Example

```
Run started: 2026-03-10 15:32
Run finished: 2026-03-10 15:35

Companies scraped:
nike, adidas, puma

Results by company and source:
nike | ESG News | 12 rows
nike | ESG Dive | 19 rows
nike | ESG Today | 9 rows

Total rows: 87
```

---

# Requirements

Python 3.10+

Install dependencies:

```
pip install playwright pandas beautifulsoup4
```

Then install browsers:

```
playwright install
```

---

# Future Improvements

Potential improvements:

- parallel scraping across sources
- deduplication of identical articles
- better rate limiting
- additional ESG news sources
- database storage instead of CSV
- scheduling automated daily runs
- NLP analysis of ESG sentiment

---

# Adding a New News Source

To add a new site:

1. create a new scraper class

```
class NewSiteScraper(BaseScraper):
```

2. define selectors

```
results_article_selector
title_selector
link_selector
date_selector
```

3. implement `build_search_url()`

4. add it to the scraper list in `run_scrapers.py`

---

# License

MIT License