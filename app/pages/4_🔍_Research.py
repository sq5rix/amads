import time
import streamlit as st
import pandas as pd
from scrapers.amazon_autocomplete import get_suggestions, alphabet_expand
from scrapers.amazon_search import search_books, extract_title_keywords
from analysis.keyword_expansion import full_expansion
from db.database import upsert_research_keywords, query

st.set_page_config(page_title="Research", page_icon="🔍", layout="wide")
st.title("🔍 Keyword Research")

tab_auto, tab_alpha, tab_comp, tab_expand, tab_db = st.tabs(
    ["Autocomplete", "Alphabet Crawler", "Competitor Books", "Keyword Expander", "Research DB"]
)

# ── Autocomplete ──────────────────────────────────────────────────────────────
with tab_auto:
    st.subheader("Amazon Autocomplete Suggestions")
    st.caption("Queries Amazon's suggestion API — exactly what customers see when typing.")

    col1, col2 = st.columns([3, 1])
    seed_auto = col1.text_input(
        "Seed keyword",
        value="communication skills",
        key="auto_seed",
        placeholder="e.g. communication skills for engineers",
    )
    marketplace_auto = col2.selectbox("Marketplace", ["US", "UK", "DE", "FR"], key="auto_market")

    if st.button("Get suggestions", type="primary", key="auto_btn"):
        with st.spinner("Querying Amazon…"):
            suggestions = get_suggestions(seed_auto, marketplace=marketplace_auto, limit=20)
        if suggestions:
            st.success(f"Found {len(suggestions)} suggestions.")
            df_sugg = pd.DataFrame({"keyword": suggestions})
            st.dataframe(df_sugg, use_container_width=True, height=300)

            col_a, col_b = st.columns(2)
            if col_a.button("Save to Research DB", key="auto_save"):
                n = upsert_research_keywords(suggestions, source="autocomplete", seed=seed_auto)
                st.success(f"Saved {n} new keywords.")
            if col_b.button("Download CSV", key="auto_dl"):
                st.download_button("⬇️ Download", df_sugg.to_csv(index=False), "suggestions.csv", "text/csv")
        else:
            st.warning("No suggestions returned — Amazon may be rate-limiting. Try again in a moment.")

# ── Alphabet Crawler ──────────────────────────────────────────────────────────
with tab_alpha:
    st.subheader("Alphabet Crawler")
    st.markdown(
        """
        Appends **a–z** and **0–9** to your seed keyword and collects all suggestions.
        This is how tools like Publisher Rocket generate 500–1000+ keyword ideas.

        *Example: `communication skills a`, `communication skills b`, …*
        """
    )

    col1, col2, col3 = st.columns([3, 1, 1])
    seed_alpha = col1.text_input(
        "Seed keyword",
        value="communication skills",
        key="alpha_seed",
    )
    marketplace_alpha = col2.selectbox("Marketplace", ["US", "UK", "DE", "FR"], key="alpha_market")
    delay_alpha = col3.slider("Delay (s)", 0.2, 2.0, 0.5, step=0.1, key="alpha_delay",
                              help="Slow down to avoid being rate-limited by Amazon")

    if st.button("Start alphabet crawl", type="primary", key="alpha_btn"):
        progress_bar = st.progress(0, text="Starting crawl…")
        status_text = st.empty()
        results_placeholder = st.empty()

        found_keywords = []
        import string
        characters = list(string.ascii_lowercase) + list(string.digits)
        total = len(characters)

        for i, char in enumerate(characters):
            query_str = f"{seed_alpha} {char}"
            status_text.text(f"Querying: {query_str}")
            suggestions = get_suggestions(query_str, marketplace=marketplace_alpha, limit=20)
            for s in suggestions:
                if s not in found_keywords:
                    found_keywords.append(s)
            progress_bar.progress((i + 1) / total, text=f"{i+1}/{total} — {len(found_keywords)} keywords found")
            time.sleep(delay_alpha)

        progress_bar.empty()
        status_text.empty()

        if found_keywords:
            st.success(f"Crawl complete — {len(found_keywords)} unique keywords found.")
            df_alpha = pd.DataFrame({"keyword": found_keywords})
            st.dataframe(df_alpha, use_container_width=True, height=400)

            col_a, col_b = st.columns(2)
            if col_a.button("Save all to Research DB", key="alpha_save"):
                n = upsert_research_keywords(found_keywords, source="alphabet_crawl", seed=seed_alpha)
                st.success(f"Saved {n} new keywords.")
            if col_b.button("Download CSV", key="alpha_dl"):
                st.download_button("⬇️ Download", df_alpha.to_csv(index=False), "alphabet_crawl.csv", "text/csv")
        else:
            st.warning("No keywords found. Try a different seed or check your internet connection.")

# ── Competitor Books ──────────────────────────────────────────────────────────
with tab_comp:
    st.subheader("Competitor Book Analysis")
    st.markdown(
        """
        Searches Amazon for books matching your keyword, shows the top results,
        and extracts potential keywords from their titles.
        """
    )
    st.warning(
        "Amazon actively blocks scrapers. Results may be limited — if empty, try again after a few minutes.",
        icon="⚠️",
    )

    col1, col2 = st.columns([3, 1])
    comp_seed = col1.text_input(
        "Search keyword",
        value="communication skills for engineers",
        key="comp_seed",
    )
    comp_market = col2.selectbox("Marketplace", ["US", "UK"], key="comp_market")

    if st.button("Find competitor books", type="primary", key="comp_btn"):
        with st.spinner("Searching Amazon…"):
            books = search_books(comp_seed, marketplace=comp_market, max_results=10)

        if books and "error" not in books[0]:
            st.success(f"Found {len(books)} books.")

            df_books = pd.DataFrame(books)
            st.dataframe(
                df_books[["title", "author", "rating", "reviews"]],
                use_container_width=True,
            )

            # Extract keywords from titles
            titles = [b["title"] for b in books if b.get("title")]
            kw_from_titles = extract_title_keywords(titles)

            st.markdown(f"**{len(kw_from_titles)} keyword ideas extracted from titles:**")
            df_kw_comp = pd.DataFrame({"keyword": kw_from_titles})
            st.dataframe(df_kw_comp, use_container_width=True, height=300)

            col_a, col_b = st.columns(2)
            if col_a.button("Save extracted keywords to Research DB", key="comp_save"):
                n = upsert_research_keywords(kw_from_titles, source="competitor_titles", seed=comp_seed)
                st.success(f"Saved {n} new keywords.")
            if col_b.button("Download keywords", key="comp_dl"):
                st.download_button("⬇️ Download", df_kw_comp.to_csv(index=False), "competitor_keywords.csv", "text/csv")

        elif books and "error" in books[0]:
            st.error(f"Request failed: {books[0]['error']}")
        else:
            st.warning("No books found. Amazon may have blocked the request.")

# ── Keyword Expander ──────────────────────────────────────────────────────────
with tab_expand:
    st.subheader("Keyword Expander")
    st.caption(
        "Takes a list of base keywords and generates variations using suffixes, prefixes, and audience modifiers."
    )

    base_keywords_input = st.text_area(
        "Base keywords (one per line)",
        value="""communication skills
workplace communication
corporate politics
soft skills
office politics
negotiation
personal brand""",
        height=180,
        key="expand_input",
    )

    col1, col2, col3 = st.columns(3)
    use_suffix = col1.checkbox("Suffixes (book, guide, for engineers…)", value=True)
    use_prefix = col2.checkbox("Prefixes (how to, mastering…)", value=True)
    use_audience = col3.checkbox("Audience (for managers, for engineers…)", value=True)
    max_expand = st.slider("Max results", 100, 2000, 500, key="expand_max")

    if st.button("Generate expansions", type="primary", key="expand_btn"):
        base_kws = [k.strip() for k in base_keywords_input.strip().split("\n") if k.strip()]

        with st.spinner(f"Expanding {len(base_kws)} base keywords…"):
            from analysis.keyword_expansion import (
                expand_with_suffixes,
                expand_with_prefixes,
                expand_with_audience,
            )
            expanded = set(base_kws)
            if use_suffix:
                expanded.update(expand_with_suffixes(base_kws))
            if use_prefix:
                expanded.update(expand_with_prefixes(base_kws))
            if use_audience:
                expanded.update(expand_with_audience(base_kws))
            expanded = sorted(expanded)[:max_expand]

        st.success(f"Generated {len(expanded)} keywords from {len(base_kws)} base keywords.")
        df_expanded = pd.DataFrame({"keyword": expanded})
        st.dataframe(df_expanded, use_container_width=True, height=400)

        col_a, col_b = st.columns(2)
        if col_a.button("Save to Research DB", key="expand_save"):
            n = upsert_research_keywords(expanded, source="expansion")
            st.success(f"Saved {n} new keywords.")
        if col_b.button("Download CSV", key="expand_dl"):
            st.download_button("⬇️ Download", df_expanded.to_csv(index=False), "expanded_keywords.csv", "text/csv")

# ── Research DB ───────────────────────────────────────────────────────────────
with tab_db:
    st.subheader("Research Database")

    df_research = query("SELECT * FROM keyword_research ORDER BY added_at DESC")

    if df_research.empty:
        st.info("No research keywords yet. Use the tabs above to discover keywords.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total keywords", len(df_research))

        sources = df_research["source"].value_counts()
        col2.metric("Sources", len(sources))

        clustered = df_research["cluster_name"].notna().sum()
        col3.metric("Clustered", int(clustered))

        st.markdown("---")

        # Filter
        src_options = ["All"] + sorted(df_research["source"].dropna().unique().tolist())
        sel_src = st.selectbox("Filter by source", src_options, key="db_src")
        db_search = st.text_input("Search", key="db_search")

        filtered_db = df_research.copy()
        if sel_src != "All":
            filtered_db = filtered_db[filtered_db["source"] == sel_src]
        if db_search:
            filtered_db = filtered_db[filtered_db["keyword"].str.contains(db_search, case=False, na=False)]

        st.dataframe(
            filtered_db[["keyword", "source", "seed", "cluster_name", "added_at"]].reset_index(drop=True),
            use_container_width=True,
            height=450,
        )

        col_a, col_b = st.columns(2)
        if col_a.button("Export all research keywords", key="db_export"):
            csv = df_research.to_csv(index=False)
            st.download_button("⬇️ Download", csv, "research_keywords.csv", "text/csv")

        if col_b.button("Clear research DB", type="secondary", key="db_clear"):
            if st.session_state.get("confirm_clear_research"):
                from db.database import execute
                execute("DELETE FROM keyword_research")
                st.success("Research database cleared.")
                st.session_state["confirm_clear_research"] = False
                st.rerun()
            else:
                st.session_state["confirm_clear_research"] = True
                st.warning("Click again to confirm clearing ALL research keywords.")
