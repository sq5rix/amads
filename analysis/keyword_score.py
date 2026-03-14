"""
Keyword scoring and categorisation for Amazon Ads optimisation.
"""
import pandas as pd


def score_keyword(row: dict | pd.Series) -> float:
    """
    Composite score:  (sales × 3) + (CTR × 10) − ACoS
    Higher = better. Negative = actively losing money.
    """
    impressions = row.get("impressions", 0) or 0
    clicks = row.get("clicks", 0) or 0
    sales = row.get("sales", 0) or 0
    cost = row.get("cost", 0) or 0

    ctr = clicks / impressions if impressions > 0 else 0
    acos = (cost / sales) if sales > 0 else 999

    return round((sales * 3) + (ctr * 10) - acos, 4)


def categorise_keyword(
    row: dict | pd.Series,
    pause_clicks: int = 20,
    bid_up_sales: int = 2,
    ctr_low: float = 0.002,
) -> str:
    """
    Returns one of: 'winner', 'pause', 'low_visibility', 'watch', 'new'
    """
    clicks = row.get("clicks", 0) or 0
    sales = row.get("sales", 0) or 0
    impressions = row.get("impressions", 0) or 0
    ctr = clicks / impressions if impressions > 0 else 0

    if sales >= bid_up_sales:
        return "winner"
    if clicks >= pause_clicks and sales == 0:
        return "pause"
    if impressions > 200 and ctr < ctr_low:
        return "low_visibility"
    if clicks > 0:
        return "watch"
    return "new"


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add score, category, CTR, ACoS, conversion_rate columns to a keywords dataframe."""
    if df.empty:
        return df

    df = df.copy()

    df["impressions"] = pd.to_numeric(df.get("impressions", 0), errors="coerce").fillna(0)
    df["clicks"] = pd.to_numeric(df.get("clicks", 0), errors="coerce").fillna(0)
    df["sales"] = pd.to_numeric(df.get("sales", 0), errors="coerce").fillna(0)
    df["cost"] = pd.to_numeric(df.get("cost", 0), errors="coerce").fillna(0)
    df["orders"] = pd.to_numeric(df.get("orders", 0), errors="coerce").fillna(0)

    df["ctr"] = (df["clicks"] / df["impressions"].replace(0, float("nan"))).round(4)
    df["conversion_rate"] = (df["orders"] / df["clicks"].replace(0, float("nan"))).round(4)
    df["acos"] = (df["cost"] / df["sales"].replace(0, float("nan"))).round(4)
    df["cpc"] = (df["cost"] / df["clicks"].replace(0, float("nan"))).round(4)
    df["score"] = df.apply(score_keyword, axis=1)
    df["status"] = df.apply(categorise_keyword, axis=1)

    return df


def get_winners(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] == "winner"].sort_values("sales", ascending=False)


def get_pause_candidates(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] == "pause"].sort_values("clicks", ascending=False)


def get_low_visibility(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] == "low_visibility"].sort_values("impressions", ascending=False)
