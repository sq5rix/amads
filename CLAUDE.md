# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project builds a CLI toolkit and dashboard to automate Amazon Advertising (Sponsored Products) for a KDP self-published book: *Corporate Communication DNA: Lessons From a 35-year Career* by Tom Wawer. The goal is to discover converting keywords, optimize bids, and feed winning keywords back into KDP metadata.

The project specification lives entirely in `plan.md`.

## Planned Architecture

```
amazon-ads-cli/
├─ bin/                  # Bash entry points
│   ├─ ads-report        # Download search term reports from Amazon Ads API
│   ├─ ads-keywords      # Extract and score keywords from reports → SQLite DB
│   ├─ ads-campaign      # Create manual campaigns from keyword files
│   └─ ads-optimize      # Pause bad keywords / increase bids on winners
├─ lib/
│   ├─ config.sh         # Exports AMAZON_CLIENT_ID/SECRET/REFRESH_TOKEN/PROFILE_ID
│   ├─ api.py            # Amazon Ads API wrapper (ad_api library)
│   └─ report_parser.py  # Parse downloaded CSV/GZIP_JSON reports
├─ data/
│   ├─ reports/          # Raw downloaded reports
│   └─ keywords.db       # SQLite keyword performance database
├─ campaigns/            # Per-theme keyword lists (.txt, one keyword per line)
│   ├─ communication.txt
│   ├─ engineers.txt
│   ├─ corporate_survival.txt
│   └─ negotiation.txt
└─ requirements.txt
```

A Streamlit dashboard (`app.py`) is planned as a second deliverable with pages for KPI visualization, report upload, keyword research, and campaign builder.

## Technology Stack

- **Language**: Python 3, Bash
- **Amazon Ads API**: `ad_api` library (PyPI package `amazon-ads-api`)
- **CLI framework**: `click`
- **Data processing**: `pandas`, `sqlite-utils`
- **Dashboard**: `streamlit`
- **Keyword clustering**: `scikit-learn`

## Setup

```bash
pip install amazon-ads-api pandas click sqlite-utils streamlit scikit-learn requests beautifulsoup4
source lib/config.sh   # load API credentials into env
```

Credentials required in `lib/config.sh`:
```bash
export AMAZON_CLIENT_ID="..."
export AMAZON_CLIENT_SECRET="..."
export AMAZON_REFRESH_TOKEN="..."
export AMAZON_PROFILE_ID="..."
```

## Intended CLI Usage

```bash
bin/ads-report                                              # download last 30 days search term report
bin/ads-keywords --min_clicks 5                            # extract keywords, save to keywords.db
bin/ads-campaign --campaign_name "Engineers" \
                 --keywords_file campaigns/engineers.txt \
                 --daily_budget 5                           # create manual campaign
bin/ads-optimize                                           # pause (clicks≥20, sales=0); raise bid (sales≥2)
streamlit run app.py                                       # launch dashboard
```

## Optimization Logic

The core automation rule set (from plan.md):
- **Pause** a keyword when: `clicks >= 20 AND sales == 0`
- **Increase bid +20%** when: `sales >= 2`
- **Monitor** (no action yet) when: `clicks < 20 AND sales == 0`

## Domain Context

Two separate keyword systems on Amazon that must not be confused:
- **KDP metadata keywords** — 7 fields × 50 chars in the book listing; affect organic ranking; edited manually in KDP dashboard (no API).
- **Amazon Ads keywords** — campaign-level; used for paid ads; fully automatable via the Advertising API.

Workflow: test keywords via ads → find converters → move winning keywords into KDP backend fields.

Target keyword clusters for this book: Workplace Communication, Engineers/Technical Professionals, Corporate Survival/Office Politics, Personal Brand/Career Development, Communication Psychology.
