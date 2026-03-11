import pandas as pd
from llm_esg_scorer import score_article

def score_articles_from_csv(input_csv, output_csv):
    """
    Batch score ESG sentiment for articles in a CSV.

    The input CSV must contain:
    company_name, source, title, introduction, date, url

    The function sends company_name, title, and introduction to the LLM,
    receives ESG category scores, fills missing categories with 0, and
    writes a new CSV with all ESG columns added.
    """

    df = pd.read_csv(input_csv)

    results = []

    esg_fields = [
        "climate_transition",
        "energy_resource",
        "biodiversity",
        "water_use",
        "waste_pollution",
        "labour_relations",
        "health_safety",
        "human_rights_community",
        "board_management",
        "shareholder_rights",
        "conduct_anti_corruption",
        "tax_transparency_accounting"
    ]

    for _, row in df.iterrows():

        scores = score_article(
            company=row["company_name"],
            title=row["title"],
            paragraph=row["introduction"]
        )

        # Initialize all ESG fields to 0
        esg_scores = {field: 0 for field in esg_fields}

        # Update with LLM results
        for k, v in scores.items():
            if k in esg_scores:
                esg_scores[k] = v

        environmental = (
            esg_scores["climate_transition"]
            + esg_scores["energy_resource"]
            + esg_scores["biodiversity"]
            + esg_scores["water_use"]
            + esg_scores["waste_pollution"]
        )

        social = (
            esg_scores["labour_relations"]
            + esg_scores["health_safety"]
            + esg_scores["human_rights_community"]
        )

        governance = (
            esg_scores["board_management"]
            + esg_scores["shareholder_rights"]
            + esg_scores["conduct_anti_corruption"]
            + esg_scores["tax_transparency_accounting"]
        )

        result_row = {
            "company_name": row["company_name"],
            "source": row["source"],
            "title": row["title"],
            "introduction": row["introduction"],
            "date": row["date"],
            "url": row["url"],
            "environmental": environmental,
            **{k: esg_scores[k] for k in esg_fields[:5]},
            "social": social,
            **{k: esg_scores[k] for k in esg_fields[5:8]},
            "governance": governance,
            **{k: esg_scores[k] for k in esg_fields[8:]}
        }

        results.append(result_row)

    output_df = pd.DataFrame(results)

    output_df.to_csv(output_csv, index=False)

    return output_df


if __name__ == "__main__":

    df = score_articles_from_csv(
        input_csv="./outputs/all_esg_articles_20260310_191646.csv",
        output_csv="articles_scored.csv"
    )

    print(df.head())