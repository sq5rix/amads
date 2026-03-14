import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db.database import query, get_stats
from analysis.keyword_score import enrich_dataframe

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Dashboard")

stats = get_stats()

# ── KPI row ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
total_sales = stats["total_sales"]
total_spend = stats["total_spend"]
total_clicks = stats["total_clicks"]
total_impressions = stats["total_impressions"]

acos = (total_spend / total_sales * 100) if total_sales > 0 else None
ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else None

c1.metric("Total Spend", f"${total_spend:.2f}")
c2.metric("Total Sales", f"${total_sales:.2f}")
c3.metric("ACoS", f"{acos:.1f}%" if acos else "—", help="Advertising Cost of Sales (lower is better)")
c4.metric("Total Clicks", f"{int(total_clicks):,}")
c5.metric("Impressions", f"{int(total_impressions):,}")
c6.metric("CTR", f"{ctr:.2f}%" if ctr else "—")

st.divider()

df_kw = query("SELECT * FROM keywords")

if df_kw.empty:
    st.warning(
        "No keyword data yet. Go to **Campaigns** page and import keyword data first.",
        icon="📋",
    )
    st.stop()

df_kw = enrich_dataframe(df_kw)

# ── Row 1: Sales by campaign + ACoS by campaign ──────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Sales by Campaign")
    campaign_sales = (
        df_kw.groupby("campaign_name")[["sales", "cost"]]
        .sum()
        .reset_index()
        .sort_values("sales", ascending=False)
    )
    fig = px.bar(
        campaign_sales,
        x="campaign_name",
        y=["sales", "cost"],
        barmode="group",
        labels={"campaign_name": "Campaign", "value": "$", "variable": ""},
        color_discrete_map={"sales": "#2ecc71", "cost": "#e74c3c"},
    )
    fig.update_layout(margin=dict(t=10, b=10), height=320)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("ACoS by Campaign")
    campaign_acos = (
        df_kw.groupby("campaign_name")[["cost", "sales"]]
        .sum()
        .reset_index()
    )
    campaign_acos["acos_pct"] = (
        campaign_acos["cost"] / campaign_acos["sales"].replace(0, float("nan")) * 100
    ).round(1)
    campaign_acos = campaign_acos.dropna(subset=["acos_pct"])
    campaign_acos["color"] = campaign_acos["acos_pct"].apply(
        lambda x: "#2ecc71" if x < 45 else "#e74c3c"
    )
    fig2 = px.bar(
        campaign_acos.sort_values("acos_pct"),
        x="campaign_name",
        y="acos_pct",
        color="acos_pct",
        color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
        labels={"campaign_name": "Campaign", "acos_pct": "ACoS %"},
    )
    fig2.add_hline(y=45, line_dash="dash", line_color="gray", annotation_text="Target 45%")
    fig2.update_layout(margin=dict(t=10, b=10), height=320, coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Keyword demand map ─────────────────────────────────────────────────
st.subheader("🗺️ Keyword Demand Map")
st.caption(
    "Bubble size = impressions (search volume). "
    "X = CTR (visibility), Y = conversion rate (buying intent). "
    "Color = ACoS (green = profitable, red = costly)."
)

map_df = df_kw[df_kw["impressions"] > 0].copy()
map_df["ctr_pct"] = (map_df["ctr"] * 100).round(3)
map_df["conv_pct"] = (map_df["conversion_rate"] * 100).fillna(0).round(2)
map_df["acos_display"] = map_df["acos"].fillna(999)
map_df["bubble_size"] = (map_df["impressions"] / map_df["impressions"].max() * 40 + 5).round(1)

fig_map = px.scatter(
    map_df,
    x="ctr_pct",
    y="conv_pct",
    size="bubble_size",
    color="acos_display",
    hover_name="keyword",
    hover_data={
        "campaign_name": True,
        "clicks": True,
        "sales": True,
        "impressions": True,
        "ctr_pct": ":.2f",
        "conv_pct": ":.2f",
        "acos_display": ":.2f",
        "bubble_size": False,
    },
    color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
    range_color=[0, 200],
    labels={
        "ctr_pct": "CTR %",
        "conv_pct": "Conversion Rate %",
        "acos_display": "ACoS",
    },
    size_max=40,
    height=450,
)
fig_map.update_layout(margin=dict(t=10, b=10))
st.plotly_chart(fig_map, use_container_width=True)

# ── Row 3: Top keywords + status distribution ─────────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Top 15 Keywords by Sales")
    top_kws = df_kw[df_kw["sales"] > 0].sort_values("sales", ascending=True).tail(15)
    if top_kws.empty:
        st.info("No keywords with sales yet.")
    else:
        fig3 = px.bar(
            top_kws,
            x="sales",
            y="keyword",
            orientation="h",
            color="acos",
            color_continuous_scale=["#2ecc71", "#e74c3c"],
            labels={"sales": "Sales ($)", "keyword": ""},
            height=400,
        )
        fig3.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.subheader("Keyword Status Breakdown")
    status_counts = df_kw["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    color_map = {
        "winner": "#2ecc71",
        "watch": "#3498db",
        "new": "#95a5a6",
        "pause": "#e74c3c",
        "low_visibility": "#f39c12",
    }
    fig4 = px.pie(
        status_counts,
        values="Count",
        names="Status",
        color="Status",
        color_discrete_map=color_map,
        height=400,
    )
    fig4.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig4, use_container_width=True)

# ── Raw data expander ─────────────────────────────────────────────────────────
with st.expander("Raw keyword data"):
    display_cols = [
        "keyword", "campaign_name", "clicks", "impressions",
        "cost", "sales", "orders", "ctr", "conversion_rate", "acos", "score", "status",
    ]
    available = [c for c in display_cols if c in df_kw.columns]
    st.dataframe(df_kw[available].sort_values("score", ascending=False), use_container_width=True)
