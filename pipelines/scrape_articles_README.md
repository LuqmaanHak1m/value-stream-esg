# ESG Article Scraper

This module scrapes ESG-related news articles about specific companies from multiple ESG news websites and stores the results in a database.

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

Articles are inserted into the database and deduplicated automatically.

---

# Features

- Async scraping using Playwright
- Modular scraper architecture
- Multiple ESG news sources supported
- Automatic database insertion
- Deduplication via URL uniqueness
- Error reporting and logging
- Extensible site-specific parsing
- Designed for scheduled cloud execution

---

# Scraper Architecture

The scraper uses a modular mixin-based architecture to separate concerns.

```
BaseScraper
 ├── LoggerMixin
 ├── BrowserMixin
 └── ParsingMixin
```

Each component handles a specific responsibility.

---

# Mixins

## BrowserMixin

Handles Playwright browser operations.

Responsibilities:

- starting the browser
- opening pages
- retrieving HTML
- closing browser sessions

Playwright runs in headless mode.

---

## ParsingMixin

Responsible for extracting structured data from HTML.

Functions include:

- finding article containers
- extracting titles
- extracting links
- parsing dates
- extracting introduction text
- pagination handling

---

## LoggerMixin

Provides structured logging during scraping.

Example output:

```
[14:07:14] Starting scrape
[14:07:15] Fetching page
[14:07:20] Found 20 articles
[14:07:21] Saved article
```

---

# Site-Specific Scrapers

Each news website is implemented as a small subclass defining selectors and search behaviour.

Example:

```
class ESGDiveScraper(BaseScraper):
```

Responsibilities:

- search URL format
- CSS selectors
- pagination logic

This makes it easy to add new sources without modifying the core framework.

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

Results are sorted by newest.

---

## ESG Dive

```
https://www.esgdive.com
```

Example search:

```
https://www.esgdive.com/search/?q=nike
```

Pagination handled via a **Next** button.

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

Run the article scraping pipeline with:

```
python -m pipelines.scrape_articles
```

The script will:

1. search all configured companies
2. scrape all supported sites
3. extract article metadata
4. insert articles into the database
5. log results

Articles already present in the database will be skipped.

---

# Configuring Companies

Edit the list in `pipelines/scrape_articles.py`:

```python
COMPANY_NAMES = [
    "nike",
    "adidas",
    "puma",
]
```

---

# Database Storage

Articles are stored in the `articles` table.

Each record contains:

- article_id
- company_name
- source
- title
- introduction
- published_at
- url

Duplicate articles are prevented using a unique constraint on the article URL.

---

# Example Article Record

| company_name | source | title | introduction | date | url |
|---|---|---|---|---|---|
| nike | ESG News | Nike appoints CSO | Nike has appointed... | 2026-03-04 | https://... |

---

# Logging

Each run produces structured logs summarising the scrape process.

Example output:

```
Starting scrape for company: nike
Source: ESG News
Found 15 articles
Inserted 12 new articles
Skipped 3 duplicates
```

---

# Requirements

Python 3.10+

Install dependencies:

```
pip install -r requirements.txt
```

For local development, install Playwright browsers:

```
playwright install
```

The production Docker container already includes these browsers.

---

# Running in the Full Pipeline

This scraper is part of the **Value Stream ESG Pipeline**.

Pipeline stages:

```
Scrape articles
      ↓
Store in database
      ↓
LLM ESG classification
```

Only unscored articles are passed to the LLM classifier.

---

# Future Improvements

Potential improvements:

- parallel scraping across sources
- smarter rate limiting
- incremental scraping windows
- duplicate detection via text similarity
- additional ESG news sources
- caching of previously scraped pages
- article full-text extraction

---

# Adding a New News Source

To add support for a new website:

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

4. register the scraper in `scrape_articles.py`

---

# License

MIT License