import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("OPENROUTER_API_KEY")
endpoint = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

if not api_key:
    raise RuntimeError("OPENROUTER_API_KEY not found in environment")

chat_client = OpenAI(
    api_key=api_key,
    base_url=endpoint,
)

MODEL_NAME = "google/gemini-3-flash-preview"

tools = [
    {
        "type": "function",
        "function": {
            "name": "submit_esg_scores",
            "description": "Submit ESG sentiment scores for a news article.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "climate_transition": {"type": "number"},
                    "energy_resource": {"type": "number"},
                    "biodiversity": {"type": "number"},
                    "water_use": {"type": "number"},
                    "waste_pollution": {"type": "number"},
                    "labour_relations": {"type": "number"},
                    "health_safety": {"type": "number"},
                    "human_rights_community": {"type": "number"},
                    "board_management": {"type": "number"},
                    "shareholder_rights": {"type": "number"},
                    "conduct_anti_corruption": {"type": "number"},
                    "tax_transparency_accounting": {"type": "number"},
                },
                "required": [
                    "company",
                    "title",
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
                ],
            },
        },
    }
]


def submit_esg_scores(**kwargs):
    return kwargs


def score_article(
    company,
    title,
    paragraph,
    market_cap="unknown",
    employees="unknown",
    countries="unknown",
    max_retries=3,
):
    system_prompt = f"""
You are an ESG analyst scoring the impact of news articles.

Company Context:
{company} is a large global corporation.

Market Cap: {market_cap}
Employees: {employees}
Countries of operation: {countries}

SCORING PRINCIPLES
Scores range from -2.0 to +2.0

Severity scale (for large companies):
0.1-0.5 → minor impact
0.6-1.0 → moderate impact
1.1-2.0 → major impact

RULES
• Score ONLY categories mentioned in the article
• Score ONLY categories that have changed
• Avoid extreme scores unless the impact affects the whole corporation
• You MUST call the tool submit_esg_scores
• Do not explain reasoning

When calling the tool:
• Return ONLY valid JSON arguments
• Do NOT include XML tags or extra text
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"""
Company: {company}

Article Title:
{title}

First Paragraph:
{paragraph}
""",
        },
    ]

    for attempt in range(max_retries):
        response = chat_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="required",
            temperature=0,
        )

        try:
            tool_call = response.choices[0].message.tool_calls[0]
            raw_args = tool_call.function.arguments
            args = json.loads(raw_args)
            return submit_esg_scores(**args)

        except json.JSONDecodeError:
            print(f"⚠️ JSON parse failed. Retrying... ({attempt + 1}/{max_retries})")
            time.sleep(1)

    raise ValueError("LLM returned invalid JSON after all retries.")