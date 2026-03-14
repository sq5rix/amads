import streamlit as st
import pandas as pd
import plotly.express as px
from db.database import query, execute, upsert_research_keywords
from analysis.keyword_score import enrich_dataframe, get_winners, get_pause_candidates, get_low_visibility

st.set_page_config(page_title="Keywords", page_icon="🔑", layout="wide")
st.title("🔑 Keywords")

df_raw = query("SELECT * FROM keywords")

if df_raw.empty:
    st.warning("No keyword data. Go to **Campaigns** and import keyword data first.", icon="📋")
    st.stop()

df = enrich_dataframe(df_raw)

tab_all, tab_opt, tab_st, tab_winners = st.tabs(
    ["All Keywords", "Optimise", "Search Terms", "Winners"]
)

# ── All Keywords ──────────────────────────────────────────────────────────────
with tab_all:
    st.subheader(f"All Keywords ({len(df)} total)")

    # Filters
    col1, col2, col3 = st.columns(3)
    campaigns = ["All"] + sorted(df["campaign_name"].dropna().unique().tolist())
    sel_camp = col1.selectbox("Campaign", campaigns, key="all_camp")
    statuses = ["All"] + sorted(df["status"].unique().tolist())
    sel_status = col2.selectbox("Status", statuses, key="all_status")
    search = col3.text_input("Search keyword", key="all_search")

    filtered = df.copy()
    if sel_camp != "All":
        filtered = filtered[filtered["campaign_name"] == sel_camp]
    if sel_status != "All":
        filtered = filtered[filtered["status"] == sel_status]
    if search:
        filtered = filtered[filtered["keyword"].str.contains(search, case=False, na=False)]

    display_cols = [
        "keyword", "campaign_name", "clicks", "impressions",
        "cost", "sales", "orders", "ctr", "acos", "cpc", "score", "status",
    ]
    available = [c for c in display_cols if c in filtered.columns]

    st.dataframe(
        filtered[available].sort_values("score", ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=500,
        column_config={
            "ctr": st.column_config.NumberColumn("CTR", format="%.3f"),
            "acos": st.column_config.NumberColumn("ACoS", format="%.2f"),
            "cpc": st.column_config.NumberColumn("CPC", format="%.2f"),
            "cost": st.column_config.NumberColumn("Spend ($)", format="%.2f"),
            "sales": st.column_config.NumberColumn("Sales ($)", format="%.2f"),
            "score": st.column_config.NumberColumn("Score", format="%.3f"),
        },
    )

    if st.button("Export filtered to CSV", key="export_all"):
        csv = filtered[available].to_csv(index=False)
        st.download_button("Download CSV", csv, "keywords_export.csv", "text/csv")

# ── Optimise ──────────────────────────────────────────────────────────────────
with tab_opt:
    st.subheader("Optimisation Recommendations")

    winners = get_winners(df)
    pause_cands = get_pause_candidates(df)
    low_vis = get_low_visibility(df)

    col_w, col_p, col_l = st.columns(3)
    col_w.metric("Winners (bid ↑)", len(winners), delta_color="normal")
    col_p.metric("Pause candidates", len(pause_cands), delta_color="inverse")
    col_l.metric("Low visibility", len(low_vis))

    st.markdown("---")

    # Pause candidates
    st.markdown("#### 🔴 Pause Candidates")
    st.caption("These keywords have 20+ clicks with zero sales — wasting budget.")
    if pause_cands.empty:
        st.success("No pause candidates — great!")
    else:
        pause_display = [c for c in ["keyword", "campaign_name", "clicks", "impressions", "cost", "sales"] if c in pause_cands.columns]
        st.dataframe(pause_cands[pause_display].reset_index(drop=True), use_container_width=True)

        col_a, col_b = st.columns(2)
        if col_a.button("Save pause list to Research DB (as negative)", key="save_pause"):
            kws = pause_cands["keyword"].tolist()
            n = upsert_research_keywords(kws, source="pause_candidate")
            st.success(f"Saved {n} keywords to research database.")

        if col_b.button("Export pause candidates", key="exp_pause"):
            csv = pause_cands[pause_display].to_csv(index=False)
            st.download_button("Download", csv, "pause_candidates.csv", "text/csv")

    st.markdown("---")

    # Winners — bid increase
    st.markdown("#### 🟢 Winners — Increase Bid")
    st.caption("These keywords are converting. Increase bids to get more traffic.")
    if winners.empty:
        st.info("No winners yet. Keep collecting data.")
    else:
        win_display = [c for c in ["keyword", "campaign_name", "clicks", "sales", "orders", "acos", "cpc"] if c in winners.columns]
        st.dataframe(winners[win_display].reset_index(drop=True), use_container_width=True)

        if st.button("Save winners to Research DB", key="save_winners"):
            kws = winners["keyword"].tolist()
            n = upsert_research_keywords(kws, source="winner")
            st.success(f"Saved {n} winning keywords to research database.")

        if st.button("Export winners to CSV", key="exp_winners"):
            csv = winners[win_display].to_csv(index=False)
            st.download_button("Download", csv, "winners.csv", "text/csv")

    st.markdown("---")

    # Low visibility
    st.markdown("#### 🟡 Low Visibility (Low CTR)")
    st.caption("High impressions, almost no clicks — keywords showing for wrong searches or too competitive.")
    if low_vis.empty:
        st.success("No low visibility keywords detected.")
    else:
        low_display = [c for c in ["keyword", "campaign_name", "impressions", "clicks", "ctr", "cost"] if c in low_vis.columns]
        st.dataframe(low_vis[low_display].reset_index(drop=True), use_container_width=True)

    st.markdown("---")

    # Optimization log
    with st.expander("Optimisation log"):
        log_df = query("SELECT * FROM optimization_log ORDER BY acted_at DESC LIMIT 100")
        if log_df.empty:
            st.info("No optimisation actions recorded yet.")
        else:
            st.dataframe(log_df, use_container_width=True)

# ── Search Terms ──────────────────────────────────────────────────────────────
with tab_st:
    st.subheader("Search Term Report")
    st.caption("What customers actually typed before seeing your ad.")

    df_st = query("SELECT * FROM search_terms")
    if df_st.empty:
        st.info("No search term data. Import from **Campaigns** page.")
    else:
        df_st = enrich_dataframe(df_st.rename(columns={"term": "keyword"}))
        df_st["keyword"] = df_st["keyword"]

        col1, col2 = st.columns(2)
        st_search = col1.text_input("Filter search terms", key="st_search")
        st_min_clicks = col2.number_input("Min clicks", 0, 1000, 0, key="st_min_clicks")

        filtered_st = df_st.copy()
        if st_search:
            filtered_st = filtered_st[filtered_st["keyword"].str.contains(st_search, case=False, na=False)]
        if st_min_clicks > 0:
            filtered_st = filtered_st[filtered_st["clicks"] >= st_min_clicks]

        st_display = [c for c in ["keyword", "campaign_name", "clicks", "impressions", "cost", "sales", "orders", "ctr", "acos", "status"] if c in filtered_st.columns]
        st.dataframe(filtered_st[st_display].sort_values("clicks", ascending=False).reset_index(drop=True), use_container_width=True, height=400)

        if st.button("Save all search terms to Research DB", key="save_st_research"):
            kws = df_st["keyword"].dropna().unique().tolist()
            n = upsert_research_keywords(kws, source="search_term_report")
            st.success(f"Saved {n} search terms to research database.")

        if st.button("Export search terms", key="exp_st"):
            csv = filtered_st[st_display].to_csv(index=False)
            st.download_button("Download", csv, "search_terms.csv", "text/csv")

# ── Winners deep dive ─────────────────────────────────────────────────────────
with tab_winners:
    st.subheader("Winner Deep Dive")

    if winners.empty:
        st.info("No winners yet — keep running your campaigns and collect more data.")
        st.markdown("""
        **When will winners appear?**
        Amazon recommends ~10 clicks per sale as the average.
        A keyword needs ≥2 sales to be flagged as a winner here.

        **Tip:** Your strongest niche is likely *engineers / technical professionals*.
        Keywords like `communication for engineers` and `soft skills for engineers`
        are underserved on Amazon and match your book perfectly.
        """)
    else:
        for _, row in winners.iterrows():
            with st.container():
                w1, w2, w3, w4 = st.columns(4)
                w1.markdown(f"**{row['keyword']}**")
                w2.metric("Sales", f"${row.get('sales', 0):.2f}")
                w3.metric("ACoS", f"{row.get('acos', 0):.0%}" if row.get("acos") else "—")
                w4.metric("Clicks → Orders", f"{int(row.get('clicks', 0))} → {int(row.get('orders', 0))}")
            st.divider()
