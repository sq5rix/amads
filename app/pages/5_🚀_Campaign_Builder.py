import streamlit as st
import pandas as pd
import plotly.express as px
from analysis.keyword_cluster import cluster_keywords_tfidf, cluster_keywords_semantic, auto_name_clusters
from db.database import query, execute, upsert_research_keywords
from ads.api import has_credentials, create_campaign, add_keywords_to_campaign

st.set_page_config(page_title="Campaign Builder", page_icon="🚀", layout="wide")
st.title("🚀 Campaign Builder")
st.caption("Cluster keywords with AI, preview campaigns, and launch or export.")

tab_build, tab_launch, tab_templates = st.tabs(
    ["Build Campaigns", "Launch / Export", "Keyword Templates"]
)

# ── Build Campaigns ───────────────────────────────────────────────────────────
with tab_build:
    st.subheader("Step 1 — Select keywords")

    source_tab = st.radio(
        "Keyword source",
        ["From Research DB", "Paste custom list"],
        horizontal=True,
        key="builder_source",
    )

    keywords_to_cluster: list[str] = []

    if source_tab == "From Research DB":
        df_research = query("SELECT * FROM keyword_research ORDER BY keyword")

        if df_research.empty:
            st.warning("Research DB is empty. Use the **Research** page to discover keywords first.")
        else:
            # Filters
            col1, col2 = st.columns(2)
            src_opts = ["All"] + sorted(df_research["source"].dropna().unique().tolist())
            sel_src = col1.selectbox("Filter by source", src_opts, key="build_src")
            kw_filter = col2.text_input("Search keywords", key="build_search")

            filtered = df_research.copy()
            if sel_src != "All":
                filtered = filtered[filtered["source"] == sel_src]
            if kw_filter:
                filtered = filtered[filtered["keyword"].str.contains(kw_filter, case=False, na=False)]

            st.dataframe(
                filtered[["keyword", "source", "seed"]].reset_index(drop=True),
                use_container_width=True,
                height=300,
            )
            st.caption(f"{len(filtered)} keywords available.")
            keywords_to_cluster = filtered["keyword"].tolist()

    else:  # Paste custom list
        pasted = st.text_area(
            "Paste keywords (one per line)",
            height=200,
            placeholder="communication skills for engineers\nsoft skills engineers\nworkplace communication...",
            key="builder_paste",
        )
        keywords_to_cluster = [k.strip() for k in pasted.strip().split("\n") if k.strip()]
        st.caption(f"{len(keywords_to_cluster)} keywords entered.")

    st.divider()

    # ── Step 2 — Cluster ─────────────────────────────────────────────────────
    st.subheader("Step 2 — Cluster into campaigns")

    if not keywords_to_cluster:
        st.info("Add keywords above to continue.")
        st.stop()

    col1, col2, col3 = st.columns(3)
    n_clusters = col1.slider(
        "Number of campaigns (clusters)",
        min_value=2,
        max_value=min(10, len(keywords_to_cluster)),
        value=min(5, len(keywords_to_cluster)),
        key="n_clusters",
    )
    cluster_method = col2.selectbox(
        "Clustering method",
        ["TF-IDF (fast)", "Semantic AI (accurate, requires sentence-transformers)"],
        key="cluster_method",
    )
    keywords_per_campaign = col3.number_input(
        "Max keywords per campaign",
        min_value=5,
        max_value=100,
        value=25,
        key="kw_per_camp",
    )

    if st.button("Cluster keywords", type="primary", key="cluster_btn"):
        with st.spinner("Clustering…"):
            if "Semantic" in cluster_method:
                raw_clusters = cluster_keywords_semantic(keywords_to_cluster, n_clusters=n_clusters)
            else:
                raw_clusters = cluster_keywords_tfidf(keywords_to_cluster, n_clusters=n_clusters)

            named_clusters = auto_name_clusters(raw_clusters)

        st.session_state["clusters"] = named_clusters
        st.success(f"Created {len(named_clusters)} clusters.")

    if "clusters" not in st.session_state or not st.session_state["clusters"]:
        st.info("Click **Cluster keywords** to generate campaign groups.")
        st.stop()

    clusters = st.session_state["clusters"]

    st.divider()
    st.subheader("Step 3 — Review and name campaigns")

    cluster_configs = {}
    cluster_names = list(clusters.keys())

    # Summary chart
    summary_data = [
        {"Cluster": name, "Keywords": len(kws[:keywords_per_campaign])}
        for name, kws in clusters.items()
    ]
    fig = px.bar(
        pd.DataFrame(summary_data),
        x="Cluster",
        y="Keywords",
        color="Keywords",
        color_continuous_scale="Blues",
        height=250,
    )
    fig.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    for i, (cluster_name, cluster_kws) in enumerate(clusters.items()):
        trimmed_kws = cluster_kws[:keywords_per_campaign]
        with st.expander(f"Campaign {i+1}: {cluster_name} ({len(trimmed_kws)} keywords)", expanded=(i == 0)):
            col_name, col_bid, col_budget = st.columns(3)
            camp_name = col_name.text_input(
                "Campaign name",
                value=cluster_name,
                key=f"camp_name_{i}",
            )
            bid = col_bid.number_input("Default bid ($)", 0.10, 5.0, 0.35, step=0.05, key=f"bid_{i}")
            budget = col_budget.number_input("Daily budget ($)", 1.0, 100.0, 5.0, step=1.0, key=f"budget_{i}")

            match_type = st.selectbox(
                "Match type",
                ["broad", "phrase", "exact"],
                key=f"match_{i}",
            )

            df_kws = pd.DataFrame({"keyword": trimmed_kws})
            st.dataframe(df_kws, use_container_width=True, height=200)

            cluster_configs[i] = {
                "name": camp_name,
                "keywords": trimmed_kws,
                "bid": bid,
                "budget": budget,
                "match_type": match_type,
            }

    st.session_state["cluster_configs"] = cluster_configs

# ── Launch / Export ───────────────────────────────────────────────────────────
with tab_launch:
    st.subheader("Launch or Export Campaigns")

    if "cluster_configs" not in st.session_state or not st.session_state["cluster_configs"]:
        st.info("Build your campaigns in the **Build Campaigns** tab first.")
        st.stop()

    configs = st.session_state["cluster_configs"]

    st.markdown(f"**{len(configs)} campaigns ready:**")
    for i, cfg in configs.items():
        st.markdown(f"- **{cfg['name']}** — {len(cfg['keywords'])} keywords, bid ${cfg['bid']:.2f}, budget ${cfg['budget']:.0f}/day")

    st.divider()

    col_launch, col_export = st.columns(2)

    with col_export:
        st.markdown("#### Export to files")
        st.caption("Download keyword files for manual campaign creation in Amazon Ads console.")

        if st.button("Generate exports", key="export_btn"):
            for i, cfg in configs.items():
                kw_text = "\n".join(cfg["keywords"])
                filename = cfg["name"].lower().replace(" ", "_").replace("/", "_") + ".txt"
                st.download_button(
                    f"⬇️ {cfg['name']} ({len(cfg['keywords'])} keywords)",
                    kw_text,
                    filename,
                    "text/plain",
                    key=f"dl_btn_{i}",
                )

        # Export all as CSV
        if st.button("Export all as single CSV", key="export_all_btn"):
            rows = []
            for cfg in configs.values():
                for kw in cfg["keywords"]:
                    rows.append({"campaign": cfg["name"], "keyword": kw, "bid": cfg["bid"], "match_type": cfg["match_type"]})
            df_all = pd.DataFrame(rows)
            st.download_button(
                "⬇️ Download all_campaigns.csv",
                df_all.to_csv(index=False),
                "all_campaigns.csv",
                "text/csv",
                key="dl_all_csv",
            )

    with col_launch:
        st.markdown("#### Launch via Amazon Ads API")
        if not has_credentials():
            st.warning(
                "Amazon Ads API credentials not configured.\n\n"
                "Add credentials to `config/config.yaml` to enable live launch.",
                icon="🔐",
            )
        else:
            st.success("API credentials detected — ready to launch.", icon="✅")

            if st.button("Launch all campaigns", type="primary", key="launch_btn"):
                results = []
                for i, cfg in configs.items():
                    with st.spinner(f"Creating campaign: {cfg['name']}…"):
                        campaign_id, success = create_campaign(
                            name=cfg["name"],
                            daily_budget=cfg["budget"],
                            targeting_type="manual",
                        )
                        if success and campaign_id:
                            kw_success = add_keywords_to_campaign(
                                campaign_id=campaign_id,
                                ad_group_id="",  # created inside create_campaign
                                keywords=cfg["keywords"],
                                bid=cfg["bid"],
                                match_type=cfg["match_type"],
                            )
                            results.append({"campaign": cfg["name"], "status": "✅ Created", "id": campaign_id})
                        else:
                            results.append({"campaign": cfg["name"], "status": "❌ Failed", "id": "—"})

                st.dataframe(pd.DataFrame(results), use_container_width=True)

# ── Templates ─────────────────────────────────────────────────────────────────
with tab_templates:
    st.subheader("Keyword Templates for Your Book")
    st.caption("Pre-built keyword sets based on the analysis in plan.md — ready to use as starting points.")

    templates = {
        "Workplace Communication": [
            "workplace communication skills",
            "communication skills at work",
            "business communication skills",
            "how to communicate at work",
            "effective workplace communication",
            "professional communication guide",
            "corporate communication book",
            "communication skills book",
            "workplace communication guide",
            "career communication skills",
        ],
        "Engineers / Technical Professionals": [
            "communication for engineers",
            "soft skills for engineers",
            "engineers moving into management",
            "technical professionals communication",
            "engineering leadership communication",
            "career skills for engineers",
            "technical professional soft skills",
            "communication skills engineers",
            "engineer leadership skills",
            "soft skills technical career",
        ],
        "Corporate Survival / Office Politics": [
            "corporate survival guide",
            "how to survive corporate politics",
            "navigating office politics",
            "workplace politics guide",
            "office politics book",
            "corporate career strategy",
            "dealing with office politics",
            "corporate culture navigation",
            "workplace power dynamics",
            "managing up at work",
        ],
        "Personal Brand / Career Development": [
            "personal branding for professionals",
            "building personal brand at work",
            "career growth strategy",
            "professional reputation building",
            "how to stand out at work",
            "career development book",
            "professional growth guide",
            "personal branding at work",
            "building personal brand professionals",
            "career advancement strategies",
        ],
        "Communication Psychology": [
            "understanding personality types at work",
            "communication psychology workplace",
            "how to communicate with different personalities",
            "personality types workplace",
            "DISC communication at work",
            "emotional intelligence workplace",
            "active listening communication",
            "interpersonal skills workplace",
            "workplace relationships communication",
            "difficult conversations workplace",
        ],
    }

    for template_name, kws in templates.items():
        with st.expander(f"📂 {template_name} ({len(kws)} keywords)"):
            st.dataframe(pd.DataFrame({"keyword": kws}), use_container_width=True, height=220)
            col_a, col_b = st.columns(2)
            if col_a.button(f"Load into Campaign Builder", key=f"load_{template_name}"):
                st.session_state["builder_source"] = "Paste custom list"
                # Pre-fill via session state workaround
                st.session_state["builder_paste"] = "\n".join(kws)
                st.success(f"Switch to **Build Campaigns** tab — keywords are pre-loaded.")
            if col_b.button(f"Save to Research DB", key=f"save_tmpl_{template_name}"):
                from db.database import upsert_research_keywords
                n = upsert_research_keywords(kws, source="template", seed=template_name)
                st.success(f"Saved {n} new keywords.")
