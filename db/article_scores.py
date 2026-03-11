import json
from datetime import datetime, timezone

import pandas as pd
from psycopg2.extras import execute_values

from db.connection import get_db_connection


ESG_FIELDS = [
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
    "tax_transparency_accounting",
]


def fetch_articles_to_score(limit: int | None = None) -> pd.DataFrame:
    query = """
        SELECT
            a.id AS article_id,
            a.company_name,
            a.source,
            a.title,
            a.introduction,
            a.published_at,
            a.url
        FROM public.articles a
        LEFT JOIN public.article_scores s
            ON a.id = s.article_id
        WHERE s.article_id IS NULL
        ORDER BY a.published_at DESC NULLS LAST, a.id DESC
    """

    if limit is not None:
        query += f" LIMIT {int(limit)}"

    conn = get_db_connection()
    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()


def build_score_record(
    row: pd.Series,
    scores: dict,
    llm_provider: str,
    llm_model: str,
    prompt_version: str,
) -> tuple:
    esg_scores = {field: 0 for field in ESG_FIELDS}

    for key, value in scores.items():
        if key in esg_scores:
            esg_scores[key] = value

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

    scored_at = datetime.now(timezone.utc)

    raw_response = json.dumps(scores)

    return (
        int(row["article_id"]),
        llm_provider,
        llm_model,
        prompt_version,
        environmental,
        esg_scores["climate_transition"],
        esg_scores["energy_resource"],
        esg_scores["biodiversity"],
        esg_scores["water_use"],
        esg_scores["waste_pollution"],
        social,
        esg_scores["labour_relations"],
        esg_scores["health_safety"],
        esg_scores["human_rights_community"],
        governance,
        esg_scores["board_management"],
        esg_scores["shareholder_rights"],
        esg_scores["conduct_anti_corruption"],
        esg_scores["tax_transparency_accounting"],
        raw_response,
        scored_at,
    )


def upsert_article_scores(records: list[tuple]) -> int:
    if not records:
        print("No article score records to upsert.")
        return 0

    query = """
        INSERT INTO public.article_scores (
            article_id,
            llm_provider,
            llm_model,
            prompt_version,
            environmental,
            climate_transition,
            energy_resource,
            biodiversity,
            water_use,
            waste_pollution,
            social,
            labour_relations,
            health_safety,
            human_rights_community,
            governance,
            board_management,
            shareholder_rights,
            conduct_anti_corruption,
            tax_transparency_accounting,
            raw_response,
            scored_at
        )
        VALUES %s
        ON CONFLICT (article_id, llm_model, prompt_version)
        DO UPDATE SET
            llm_provider = EXCLUDED.llm_provider,
            environmental = EXCLUDED.environmental,
            climate_transition = EXCLUDED.climate_transition,
            energy_resource = EXCLUDED.energy_resource,
            biodiversity = EXCLUDED.biodiversity,
            water_use = EXCLUDED.water_use,
            waste_pollution = EXCLUDED.waste_pollution,
            social = EXCLUDED.social,
            labour_relations = EXCLUDED.labour_relations,
            health_safety = EXCLUDED.health_safety,
            human_rights_community = EXCLUDED.human_rights_community,
            governance = EXCLUDED.governance,
            board_management = EXCLUDED.board_management,
            shareholder_rights = EXCLUDED.shareholder_rights,
            conduct_anti_corruption = EXCLUDED.conduct_anti_corruption,
            tax_transparency_accounting = EXCLUDED.tax_transparency_accounting,
            raw_response = EXCLUDED.raw_response,
            scored_at = EXCLUDED.scored_at,
            updated_at = now()
    """

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, query, records, page_size=200)
        print(f"Upserted {len(records)} rows into article_scores")
        return len(records)
    finally:
        conn.close()