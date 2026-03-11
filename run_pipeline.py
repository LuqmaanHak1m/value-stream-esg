import asyncio

from pipelines.scrape_articles import main as scrape_articles_main
from pipelines.batch_scorer import score_articles_from_database


async def main():
    print("Starting article scrape...")
    await scrape_articles_main()

    print("Starting article scoring...")
    score_articles_from_database()

    print("Pipeline complete.")


if __name__ == "__main__":
    asyncio.run(main())