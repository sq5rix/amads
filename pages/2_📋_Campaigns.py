import streamlit as st
import pandas as pd
from ads.api import has_credentials, list_campaigns, get_campaign_keywords, get_search_terms
from db.database import insert_df, upsert_keywords, query

st.set_page_config(page_title="Campaigns", page_icon="📋", layout="wide")
st.title("📋 Campaigns")

if not has_credentials():
    st.info("Demo mode — showing sample data. Configure credentials in `config/config.yaml` for live data.", icon="🧪")

# ── Load campaigns ────────────────────────────────────────────────────────────
st.subheader("Your Campaigns")

if st.button("🔄 Load / Refresh campaigns from API", type="primary"):
    with st.spinner("Fetching campaigns…"):
        df, is_real = list_campaigns()
        if not df.empty:
            insert_df("campaigns", df[["campaign_id", "name", "market"]] if "market" in df.columns
                      else df.assign(market="US")[["campaign_id", "name", "market"]], if_exists="replace")
            st.success(f"Loaded {len(df)} campaigns ({'live' if is_real else 'demo'} data).")
        else:
            st.warning("No campaigns returned.")

campaigns_df = query("SELECT * FROM campaigns ORDER BY name")

if campaigns_df.empty:
    st.info("No campaigns loaded yet. Click **Load campaigns** above.")
else:
    st.dataframe(
        campaigns_df[["campaign_id", "name", "market", "state", "daily_budget"]].rename(
            columns={
                "campaign_id": "ID",
                "name": "Campaign Name",
                "market": "Market",
                "state": "Status",
                "daily_budget": "Daily Budget ($)",
            }
        ),
        use_container_width=True,
    )

st.divider()

# ── Import keyword data ───────────────────────────────────────────────────────
st.subheader("Import Keyword Performance Data")

tab_api, tab_csv = st.tabs(["From Amazon Ads API", "Upload CSV Report"])

with tab_api:
    st.markdown(
        "Imports keyword-level performance data for all campaigns into the local database."
    )
    campaign_options = ["All campaigns"]
    if not campaigns_df.empty:
        campaign_options += campaigns_df["name"].tolist()

    selected = st.selectbox("Select campaign", campaign_options, key="kw_campaign_select")

    if st.button("Import keywords", type="primary", key="import_kw_btn"):
        campaign_id = None
        if selected != "All campaigns" and not campaigns_df.empty:
            row = campaigns_df[campaigns_df["name"] == selected]
            if not row.empty:
                campaign_id = row.iloc[0]["campaign_id"]

        with st.spinner("Importing keyword data…"):
            df_kw, is_real = get_campaign_keywords(campaign_id)
            if not df_kw.empty:
                n = upsert_keywords(df_kw)
                st.success(f"Imported {len(df_kw)} keywords ({n} new rows added). {'Live' if is_real else 'Demo'} data.")
                st.dataframe(df_kw.head(20), use_container_width=True)
            else:
                st.warning("No keyword data returned.")

    st.markdown("---")
    st.markdown("**Import search term report** (what customers actually searched for)")

    if st.button("Import search terms", key="import_st_btn"):
        with st.spinner("Importing search terms…"):
            df_st, is_real = get_search_terms()
            if not df_st.empty:
                n = insert_df("search_terms", df_st)
                st.success(f"Imported {len(df_st)} search terms. {'Live' if is_real else 'Demo'} data.")
                st.dataframe(df_st.head(20), use_container_width=True)

with tab_csv:
    st.markdown(
        """
        Upload an **Amazon Ads Search Term Report** CSV.
        Download from: *Amazon Ads → Reports → Search Term Report → Download*.

        Expected columns (flexible — extra columns are ignored):
        `Customer Search Term`, `Campaign Name`, `Impressions`, `Clicks`, `Spend`, `7 Day Total Sales ($)`, `7 Day Total Orders (#)`
        """
    )

    uploaded = st.file_uploader("Choose CSV file", type=["csv"], key="csv_uploader")

    if uploaded:
        try:
            raw = pd.read_csv(uploaded)
            st.write(f"Detected {len(raw)} rows, {len(raw.columns)} columns.")
            st.dataframe(raw.head(5), use_container_width=True)

            # Flexible column mapping
            col_map = {
                "Customer Search Term": "term",
                "Search Term": "term",
                "Keyword": "term",
                "keyword": "term",
                "Campaign Name": "campaign_name",
                "Impressions": "impressions",
                "Clicks": "clicks",
                "Spend": "cost",
                "7 Day Total Sales ($)": "sales",
                "Total Sales ($)": "sales",
                "7 Day Total Orders (#)": "orders",
                "Total Orders (#)": "orders",
            }
            df_mapped = raw.rename(columns={k: v for k, v in col_map.items() if k in raw.columns})

            required = ["term"]
            if all(c in df_mapped.columns for c in required):
                if st.button("Save to database", type="primary", key="csv_save_btn"):
                    keep = [c for c in ["term", "campaign_name", "clicks", "impressions", "cost", "sales", "orders"]
                            if c in df_mapped.columns]
                    df_save = df_mapped[keep]
                    n = insert_df("search_terms", df_save)
                    st.success(f"Saved {n} rows to search_terms table.")
            else:
                st.error("Could not find a search term / keyword column in this CSV.")

        except Exception as e:
            st.error(f"Failed to read CSV: {e}")

st.divider()

# ── Current DB summary ────────────────────────────────────────────────────────
st.subheader("Database Summary")

col1, col2, col3 = st.columns(3)
kw_count = query("SELECT COUNT(*) as n FROM keywords").iloc[0]["n"] if not query("SELECT COUNT(*) as n FROM keywords").empty else 0
st_count = query("SELECT COUNT(*) as n FROM search_terms").iloc[0]["n"] if not query("SELECT COUNT(*) as n FROM search_terms").empty else 0
camp_count = query("SELECT COUNT(*) as n FROM campaigns").iloc[0]["n"] if not query("SELECT COUNT(*) as n FROM campaigns").empty else 0
col1.metric("Campaigns", int(camp_count))
col2.metric("Keywords", int(kw_count))
col3.metric("Search Terms", int(st_count))
