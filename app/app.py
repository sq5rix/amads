import streamlit as st
from db.database import init_db, get_stats
from ads.api import has_credentials

st.set_page_config(
    page_title="Book Ads Intelligence",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialise database on every startup
init_db()

st.title("📚 Book Ads Intelligence System")
st.caption("Amazon Advertising keyword research, optimisation, and campaign management.")

# Credentials status
if has_credentials():
    st.success("✅ Amazon Ads API connected — live data active.", icon="🔗")
else:
    st.info(
        "Running in **demo mode** with sample data. "
        "Add your Amazon Ads API credentials to `config/config.yaml` to use live data.",
        icon="🧪",
    )

st.divider()

# Live stats
stats = get_stats()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Campaigns tracked", stats["total_campaigns"])
col2.metric("Keywords in DB", stats["total_keywords"])
col3.metric("Search terms", stats["total_search_terms"])
col4.metric("Research keywords", stats["total_research_kws"])
col5.metric("Total ad spend", f"${stats['total_spend']:.2f}")

st.divider()

st.markdown("""
### How to use this system

| Page | What it does |
|------|-------------|
| **📊 Dashboard** | KPI overview, spend vs sales, keyword performance map |
| **📋 Campaigns** | Load campaigns, import keyword data from API or CSV |
| **🔑 Keywords** | Analyse keyword performance, find winners and pause candidates |
| **🔍 Research** | Autocomplete crawler, alphabet expansion, competitor book analysis |
| **🚀 Campaign Builder** | AI keyword clustering → one-click campaign creation |

### Recommended first workflow

1. Go to **Campaigns** → click **Load campaigns** → **Import all keywords**
2. Open **Dashboard** to see your performance overview
3. Open **Keywords → Optimise** to find pause candidates and winners
4. Run **Research → Alphabet Crawler** with your best seed keywords
5. Use **Campaign Builder** to cluster research keywords into new campaigns
""")
