# Book Ads Intelligence System

A Streamlit web app for Amazon KDP authors to discover profitable keywords, analyse campaign performance, and build optimised ad campaigns — without paying for Helium10 or Publisher Rocket.

Built for the book *Corporate Communication DNA: Lessons From a 35-Year Career* but designed to work with any book on any marketplace.

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.32+-red)
![License](https://img.shields.io/badge/license-MIT-green)

---

## The Problem This Solves

150,000 ad impressions. 56 clicks. 0 sales.

That's a keyword mismatch problem — your ads are reaching the wrong audience. This tool helps you:

1. **Find** keywords that your actual buyers search for (using Amazon's own autocomplete)
2. **Test** them in campaigns and track what converts
3. **Kill** wasted spend (pause after 20 clicks, 0 sales)
4. **Scale** winners (increase bids on converting keywords)
5. **Move** proven keywords into your KDP metadata for free organic traffic

---

## Features

### 📊 Dashboard
- KPI overview: spend, sales, ACoS, CTR
- **Keyword Demand Map** — interactive bubble chart showing every keyword by CTR (visibility), conversion rate (buying intent), and impressions (search volume)
- Sales and ACoS breakdown by campaign
- Keyword status distribution

### 📋 Campaigns
- Load campaigns from Amazon Ads API or demo mode
- Import keyword performance data (API or CSV upload)
- Flexible CSV column mapping for Amazon's search term report format

### 🔑 Keywords
- Full performance table with scoring, CTR, ACoS, CPC
- **Optimisation tab**: auto-identifies pause candidates and bid-increase candidates
- One-click export of winning keywords for KDP backend metadata

### 🔍 Research
- **Autocomplete scraper** — queries Amazon's suggestion API in real time
- **Alphabet Crawler** — appends a–z and 0–9 to a seed, generating 500–1000+ keyword ideas (same method as Publisher Rocket)
- **Competitor book analyser** — searches Amazon, extracts keyword signals from competitor titles
- **Keyword expander** — generates suffix/prefix/audience variations offline
- Persistent research database — everything you discover is saved

### 🚀 Campaign Builder
- **AI keyword clustering** using TF-IDF (fast, offline) or semantic embeddings (sentence-transformers)
- Auto-names clusters from the most common meaningful words
- Per-cluster bid, budget, and match type configuration
- Export to per-campaign `.txt` files or a single CSV
- One-click campaign launch via Amazon Ads API (when credentials are configured)
- Built-in keyword templates for 5 proven niches

---

## Quickstart

```bash
git clone https://github.com/sq5rix/amads.git
cd amads
pip install -r requirements.txt
streamlit run app.py
```

The app runs in **demo mode** by default — no Amazon credentials needed to explore the UI.

---

## Amazon Ads API Setup (optional)

To connect live data, edit `config/config.yaml`:

```yaml
credentials:
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  refresh_token: "your_refresh_token"
  profile_id: "your_profile_id"
```

Get credentials at [advertising.amazon.com](https://advertising.amazon.com) → Tools → API access.

---

## Keyword Optimisation Rules

| Condition | Action |
|-----------|--------|
| clicks ≥ 20 AND sales = 0 | Pause keyword |
| sales ≥ 2 | Increase bid by 20% |
| impressions > 200 AND CTR < 0.2% | Flag as low visibility |
| Target ACoS | 45% |

---

## Architecture

```
app.py                    # Streamlit entry point + home
pages/
  1_📊_Dashboard.py       # KPI charts and demand map
  2_📋_Campaigns.py       # Campaign management + CSV import
  3_🔑_Keywords.py        # Keyword analysis + optimisation
  4_🔍_Research.py        # Autocomplete, alphabet crawler, competitor scraper
  5_🚀_Campaign_Builder.py  # AI clustering + campaign creation
ads/
  api.py                  # Amazon Ads API wrapper (falls back to mock)
  mock_ads_api.py         # Realistic demo data
analysis/
  keyword_score.py        # Composite scoring + categorisation
  keyword_cluster.py      # TF-IDF and semantic clustering
  keyword_expansion.py    # Suffix/prefix/audience expansion
scrapers/
  amazon_autocomplete.py  # Autocomplete + alphabet crawler
  amazon_search.py        # Competitor book discovery
db/
  database.py             # SQLite operations
  schema.sql              # Table definitions
config/
  config.yaml             # Credentials + optimisation thresholds
```

---

## Weekly Workflow

```
Mon: Import search term report → review optimization recommendations
     Pause keywords with 20+ clicks and 0 sales

Wed: Run alphabet crawler on best-performing seed keywords
     Save results to research database

Fri: Cluster research keywords → build new campaigns
     Export or launch via API
```

After 2–3 months you accumulate a database of 1,000–5,000 tested keywords — the same data advantage large KDP publishers have.

---

## Requirements

- Python 3.10+
- Internet connection for autocomplete and competitor scrapers
- Amazon Ads API credentials (optional — demo mode works without them)

Optional for semantic clustering:
```bash
pip install sentence-transformers
```

---

## License

MIT
