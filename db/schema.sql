CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    asin TEXT UNIQUE,
    market TEXT DEFAULT 'US',
    added_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT UNIQUE,
    name TEXT NOT NULL,
    market TEXT DEFAULT 'US',
    state TEXT DEFAULT 'enabled',
    daily_budget REAL DEFAULT 5.0,
    targeting_type TEXT DEFAULT 'manual',
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    campaign_id TEXT,
    campaign_name TEXT,
    ad_group_id TEXT,
    match_type TEXT DEFAULT 'broad',
    bid REAL DEFAULT 0.35,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    sales REAL DEFAULT 0.0,
    orders INTEGER DEFAULT 0,
    date TEXT,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL,
    campaign_id TEXT,
    campaign_name TEXT,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    sales REAL DEFAULT 0.0,
    orders INTEGER DEFAULT 0,
    date TEXT,
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS keyword_research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    source TEXT,
    seed TEXT,
    cluster_id INTEGER,
    cluster_name TEXT,
    score REAL DEFAULT 0.0,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword)
);

CREATE TABLE IF NOT EXISTS optimization_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    campaign_id TEXT,
    action TEXT,
    old_value REAL,
    new_value REAL,
    reason TEXT,
    acted_at TEXT DEFAULT CURRENT_TIMESTAMP
);
