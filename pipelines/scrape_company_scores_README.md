# LSEG ESG Score Scraper

This module scrapes ESG ratings for companies from the **London Stock Exchange Group (LSEG) Sustainability Ratings** page.

The scraper extracts structured ESG metrics for each company and stores them in the project database.

The data represents **company self-reported ESG performance metrics** aggregated by LSEG.

---

# Purpose

This scraper provides a **baseline ESG score dataset** that can later be compared with:

- ESG sentiment extracted from news articles
- LLM-generated ESG impact scores

This allows the project to explore potential **ESG sentiment gaps between company reporting and external media coverage**.

---

# Data Collected

For each company the scraper extracts:

- company name
- industry
- ESG category
- ESG metric
- score
- data source (LSEG)

Example metrics include categories such as:

- Environmental
- Social
- Governance

Each category contains multiple ESG indicators with numeric scores.

---

# Example Output

| company | industry | category | metric | score |
|---|---|---|---|---|
| Nike | Apparel | Environmental | Climate Transition | 7.2 |
| Nike | Apparel | Governance | Board Management | 6.4 |

Data is saved to:

```
outputs/company_scores/esg_scores.csv
```

and inserted into the database table:

```
esg_scores
```

---

# Running the Scraper

Run the scraper with:

```
python -m pipelines.scrape_company_scores
```

The script will:

1. query LSEG for each company
2. extract ESG score data
3. generate a structured dataframe
4. save a CSV snapshot
5. insert results into the database

---

# Company Configuration

Companies are defined in the `NAME_MAP` dictionary:

```python
NAME_MAP = {
    "Nike": "Nike Inc",
    "Adidas": "Adidas AG",
}
```

The key is the internal project name, while the value is the **official company name used by LSEG search**.

---

# Reliability Features

The scraper includes several safeguards:

- retry logic for failed companies
- multiple scrape rounds with increasing delays
- structured error tracking
- graceful browser shutdown

This helps handle occasional page load or rendering failures.

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

The production Docker image already contains these browsers.

---

# Scheduling

This scraper is **not currently scheduled** in the automated pipeline.

LSEG ESG scores change relatively infrequently, so the scraper is expected to run **manually or roughly once per year**.

Future improvements could include adding a **scheduled Cloud Run job** to refresh ESG scores annually.

---

# Future Improvements

Potential improvements:

- annual automated refresh via Cloud Scheduler
- historical ESG score tracking
- additional ESG rating providers
- company coverage expansion
- automated change detection between score updates

---

# License

MIT License