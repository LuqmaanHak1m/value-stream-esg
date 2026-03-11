# Value Stream ESG Pipeline

An automated pipeline that collects ESG-related news articles about major companies, stores them in a database, and classifies their ESG impact using an LLM.

The pipeline runs in Google Cloud as a scheduled **Cloud Run Job**.

---

# Overview

The system performs three main tasks:

1. **Scrape ESG news articles**
2. **Store articles in a database**
3. **Score ESG sentiment using an LLM**

The pipeline is designed to avoid duplicate work:

- Articles are only inserted if they do not already exist.
- Articles are only scored if they do not already have an LLM score.

---

# Architecture

```
Cloud Scheduler
      │
      ▼
Cloud Run Job
      │
      ▼
run_pipeline.py
      │
      ├── Scrape ESG news articles
      │       └── Insert into database
      │
      └── Score unclassified articles
              └── Save ESG scores
```

---

# Project Structure

```
value-stream-esg/
│
├── db/
│   ├── connection.py
│   ├── articles.py
│   ├── article_scores.py
│   └── esg_scores.py
│
├── pipelines/
│   ├── scrape_articles.py
│   └── batch_scorer.py
│
├── scrapers/
│   └── article_scraper/
│       └── news_scrapers.py
│       └── base_scraper.py
│       └── browser.py
│       └── logging_utils.py
│       └── parsing.py
│       
├── llm/
│   └── score_articles.py
│
├── run_pipeline.py
│
├── requirements.txt
└── README.md
```

---

# Pipeline Steps

## 1. Article Scraping

The scraper collects articles from several ESG news sources.

Sources currently implemented:

- ESG News
- ESG Dive
- ESG Today

Articles are scraped for a list of companies and stored in the `articles` table.

Each article includes:

- company name
- title
- introduction
- publication date
- source
- URL

Duplicates are prevented using a unique constraint on the article URL.

---

## 2. Article Scoring (LLM)

Articles are classified using an LLM via **OpenRouter**.

The model assigns sentiment scores for ESG categories.

Environmental categories:

- climate_transition
- energy_resource
- biodiversity
- water_use
- waste_pollution

Social categories:

- labour_relations
- health_safety
- human_rights_community

Governance categories:

- board_management
- shareholder_rights
- conduct_anti_corruption
- tax_transparency_accounting

Each category receives a score between **-2 and +2**.

Scores are stored in the `article_scores` table.

---

# Database

The pipeline writes to a PostgreSQL database.

Main tables:

### `articles`

Stores scraped articles.

Columns include:

- article_id
- company_name
- source
- title
- introduction
- published_at
- url

---

### `article_scores`

Stores ESG classifications produced by the LLM.

Columns include:

- article_id
- environmental
- social
- governance
- individual ESG category scores
- llm_provider
- llm_model
- prompt_version

---

### `esg_scores`

Stores ESG ratings scraped from company disclosures (e.g. LSEG).

---

# Running Locally

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

run
```bash
playwright install
```

Set environment variables:

```
DATABASE_URL=postgres://...
OPENROUTER_API_KEY=...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

Run the full pipeline:

```bash
python run_pipeline.py
```

---

# Deployment

The pipeline runs in **Google Cloud Run Jobs**.

Steps:

1. Build container

```bash
gcloud builds submit --tag gcr.io/<PROJECT_ID>/value-stream-esg
```

2. Create job

```bash
gcloud run jobs create esg-pipeline \
  --image gcr.io/<PROJECT_ID>/value-stream-esg \
  --region europe-west3
```

3. Execute manually

```bash
gcloud run jobs execute esg-pipeline --region europe-west3
```

4. Schedule execution using **Cloud Scheduler**.

Example cron schedule:

```
0 3 1 * *
```

Runs 1st day of month at 03:00

---

# Environment Variables

The job requires the following environment variables:

```
DATABASE_URL
OPENROUTER_API_KEY
OPENROUTER_BASE_URL
```

These should be configured in **Cloud Run Job → Variables & Secrets**.

---

# Future Improvements

Possible improvements include:

- parallel scraping
- article deduplication via text similarity
