import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ads.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = connect()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def insert_df(table: str, df: pd.DataFrame, if_exists="append"):
    if df.empty:
        return 0
    conn = connect()
    df.to_sql(table, conn, if_exists=if_exists, index=False)
    conn.close()
    return len(df)


def query(sql: str, params=()) -> pd.DataFrame:
    conn = connect()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def execute(sql: str, params=()):
    conn = connect()
    conn.execute(sql, params)
    conn.commit()
    conn.close()


def executemany(sql: str, rows):
    conn = connect()
    conn.executemany(sql, rows)
    conn.commit()
    conn.close()


def upsert_keywords(df: pd.DataFrame):
    """Insert keywords, skip duplicates by (keyword, campaign_id, date)."""
    if df.empty:
        return 0
    conn = connect()
    inserted = 0
    for _, row in df.iterrows():
        try:
            conn.execute(
                """INSERT OR IGNORE INTO keywords
                   (keyword, campaign_id, campaign_name, match_type, bid,
                    clicks, impressions, cost, sales, orders, date)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    row.get("keyword", ""),
                    row.get("campaign_id", ""),
                    row.get("campaign_name", ""),
                    row.get("match_type", "broad"),
                    row.get("bid", 0.35),
                    int(row.get("clicks", 0)),
                    int(row.get("impressions", 0)),
                    float(row.get("cost", 0)),
                    float(row.get("sales", 0)),
                    int(row.get("orders", 0)),
                    row.get("date", ""),
                ),
            )
            inserted += conn.execute("SELECT changes()").fetchone()[0]
        except Exception:
            pass
    conn.commit()
    conn.close()
    return inserted


def upsert_research_keywords(keywords: list[str], source: str, seed: str = ""):
    """Insert research keywords, ignore duplicates."""
    conn = connect()
    inserted = 0
    for kw in keywords:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO keyword_research (keyword, source, seed) VALUES (?,?,?)",
                (kw.strip().lower(), source, seed),
            )
            inserted += conn.execute("SELECT changes()").fetchone()[0]
        except Exception:
            pass
    conn.commit()
    conn.close()
    return inserted


def get_stats() -> dict:
    conn = connect()
    stats = {}
    for key, sql in [
        ("total_campaigns", "SELECT COUNT(*) FROM campaigns"),
        ("total_keywords", "SELECT COUNT(*) FROM keywords"),
        ("total_search_terms", "SELECT COUNT(*) FROM search_terms"),
        ("total_research_kws", "SELECT COUNT(*) FROM keyword_research"),
        ("total_spend", "SELECT COALESCE(SUM(cost),0) FROM keywords"),
        ("total_sales", "SELECT COALESCE(SUM(sales),0) FROM keywords"),
        ("total_clicks", "SELECT COALESCE(SUM(clicks),0) FROM keywords"),
        ("total_impressions", "SELECT COALESCE(SUM(impressions),0) FROM keywords"),
    ]:
        try:
            stats[key] = conn.execute(sql).fetchone()[0]
        except Exception:
            stats[key] = 0
    conn.close()
    return stats
