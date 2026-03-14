"""
Realistic mock Amazon Ads data for development / demo.
Reflects Tom's actual book situation with 5 campaigns.
"""
import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

MOCK_CAMPAIGNS = [
    {"campaign_id": "c001", "name": "Communication Skills", "market": "US", "state": "enabled", "daily_budget": 5.0},
    {"campaign_id": "c002", "name": "Engineers Soft Skills", "market": "US", "state": "enabled", "daily_budget": 5.0},
    {"campaign_id": "c003", "name": "Corporate Survival", "market": "US", "state": "enabled", "daily_budget": 5.0},
    {"campaign_id": "c004", "name": "Office Politics", "market": "US", "state": "enabled", "daily_budget": 5.0},
    {"campaign_id": "c005", "name": "Career Development", "market": "US", "state": "paused", "daily_budget": 3.0},
]

MOCK_KEYWORDS = {
    "c001": [
        ("workplace communication skills", 22, 480, 7.20, 0, 0),
        ("communication skills at work", 18, 390, 5.40, 1, 1),
        ("business communication skills", 31, 720, 11.20, 0, 0),
        ("professional communication guide", 9, 210, 3.15, 0, 0),
        ("how to communicate at work", 14, 300, 4.90, 1, 1),
        ("effective workplace communication", 7, 180, 2.45, 0, 0),
        ("corporate communication book", 12, 260, 4.20, 0, 0),
        ("communication skills book", 45, 1100, 15.75, 0, 0),
    ],
    "c002": [
        ("communication for engineers", 8, 160, 2.80, 2, 2),
        ("soft skills for engineers", 11, 230, 3.85, 1, 1),
        ("engineers moving into management", 5, 90, 1.75, 1, 1),
        ("technical professionals communication", 4, 80, 1.40, 0, 0),
        ("engineering leadership communication", 3, 70, 1.05, 0, 0),
        ("career skills for engineers", 7, 150, 2.45, 1, 1),
    ],
    "c003": [
        ("corporate survival guide", 6, 140, 2.10, 0, 0),
        ("how to survive corporate politics", 3, 70, 1.05, 0, 0),
        ("corporate career strategy", 9, 200, 3.15, 0, 0),
        ("navigating office politics", 15, 330, 5.25, 0, 0),
        ("workplace politics guide", 22, 490, 7.70, 0, 0),
        ("corporate culture navigation", 4, 90, 1.40, 0, 0),
    ],
    "c004": [
        ("office politics book", 26, 580, 9.10, 0, 0),
        ("dealing with office politics", 14, 310, 4.90, 0, 0),
        ("workplace power dynamics", 7, 160, 2.45, 0, 0),
        ("corporate politics survival", 5, 110, 1.75, 0, 0),
        ("managing up at work", 12, 270, 4.20, 1, 1),
    ],
    "c005": [
        ("career development book", 33, 750, 11.55, 0, 0),
        ("professional growth guide", 19, 430, 6.65, 0, 0),
        ("personal branding at work", 8, 180, 2.80, 0, 0),
        ("building personal brand professionals", 5, 110, 1.75, 1, 1),
    ],
}

MOCK_SEARCH_TERMS = [
    ("communication skills for engineers", "c002", 7, 140, 2.45, 1, 1),
    ("soft skills engineer leadership", "c002", 4, 80, 1.40, 0, 0),
    ("workplace communication for technical people", "c001", 3, 60, 1.05, 1, 1),
    ("business communication book amazon", "c001", 12, 280, 4.20, 0, 0),
    ("office politics navigation", "c004", 8, 175, 2.80, 0, 0),
    ("corporate communication dna", "c001", 2, 35, 0.70, 2, 2),
    ("communication", "c001", 35, 9200, 12.25, 0, 0),
    ("leadership", "c004", 42, 12000, 14.70, 0, 0),
    ("business book", "c001", 28, 7800, 9.80, 0, 0),
    ("how to communicate better at work", "c001", 6, 120, 2.10, 1, 1),
    ("personality types workplace", "c001", 5, 100, 1.75, 0, 0),
    ("negotiation skills workplace", "c003", 9, 190, 3.15, 1, 1),
]


def list_campaigns() -> pd.DataFrame:
    return pd.DataFrame(MOCK_CAMPAIGNS)


def get_campaign_keywords(campaign_id: str = None) -> pd.DataFrame:
    rows = []
    campaigns = [campaign_id] if campaign_id else list(MOCK_KEYWORDS.keys())
    for cid in campaigns:
        if cid in MOCK_KEYWORDS:
            for kw, clicks, impr, cost, sales, orders in MOCK_KEYWORDS[cid]:
                rows.append(
                    {
                        "keyword": kw,
                        "campaign_id": cid,
                        "campaign_name": next(
                            c["name"] for c in MOCK_CAMPAIGNS if c["campaign_id"] == cid
                        ),
                        "match_type": "broad",
                        "bid": round(random.uniform(0.28, 0.45), 2),
                        "clicks": clicks,
                        "impressions": impr,
                        "cost": cost,
                        "sales": sales,
                        "orders": orders,
                        "date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                    }
                )
    return pd.DataFrame(rows)


def get_search_terms() -> pd.DataFrame:
    rows = []
    for term, cid, clicks, impr, cost, sales, orders in MOCK_SEARCH_TERMS:
        rows.append(
            {
                "term": term,
                "campaign_id": cid,
                "campaign_name": next(
                    c["name"] for c in MOCK_CAMPAIGNS if c["campaign_id"] == cid
                ),
                "clicks": clicks,
                "impressions": impr,
                "cost": cost,
                "sales": sales,
                "orders": orders,
                "date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            }
        )
    return pd.DataFrame(rows)
