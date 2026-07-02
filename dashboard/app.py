"""Local Streamlit dashboard for GitHub Insight."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
MASTER_CSV = ROOT / "data" / "processed" / "github_repos_master.csv"
LATEST_JSON = ROOT / "docs" / "data" / "latest.json"
ARCHIVE_JSON = ROOT / "docs" / "data" / "archive_index.json"


st.set_page_config(page_title="GitHub Insight", layout="wide")
st.title("GitHub Daily Intelligence Dashboard")

if not LATEST_JSON.exists():
    st.warning("No generated dashboard data found. Run `python -m github_insight.cli run --mock` first.")
    st.stop()

payload = json.loads(LATEST_JSON.read_text(encoding="utf-8"))
projects = pd.DataFrame(payload.get("projects", []))
run = payload.get("run", {})
archive = json.loads(ARCHIVE_JSON.read_text(encoding="utf-8")) if ARCHIVE_JSON.exists() else []

st.caption(f"Generated at {run.get('generated_at')} | Mode {run.get('mode')} | Date {run.get('date')}")

with st.sidebar:
    st.header("Filters")
    date_options = sorted(projects["date"].dropna().unique().tolist()) if "date" in projects else []
    selected_dates = st.multiselect("Date", date_options, default=date_options[-1:] if date_options else [])
    audience = st.selectbox("Audience", ["all", "general_user", "data_analyst", "data_scientist"])
    min_score = st.slider("Minimum score", 0, 100, 0)

filtered = projects.copy()
if selected_dates and "date" in filtered:
    filtered = filtered[filtered["date"].isin(selected_dates)]
if audience != "all" and not filtered.empty:
    filtered = filtered[
        (filtered["primary_audience"] == audience)
        | filtered["audience_tags"].apply(lambda value: audience in value if isinstance(value, list) else False)
    ]
if not filtered.empty:
    filtered = filtered[filtered["overall_insight_score"] >= min_score]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Repositories scanned", run.get("repos_discovered", 0))
k2.metric("Repositories selected", len(filtered))
k3.metric("Top score", f"{filtered['overall_insight_score'].max():.2f}" if not filtered.empty else "0")
k4.metric("Risk flagged", int(filtered["risk_flags"].apply(lambda value: len(value) if isinstance(value, list) else 0).gt(0).sum()) if not filtered.empty else 0)

st.subheader("Top repositories")
columns = [
    "rank_today",
    "full_name",
    "primary_audience",
    "overall_insight_score",
    "recommended_action",
    "difficulty_level",
    "language",
    "stars",
    "forks",
]
st.dataframe(filtered[columns] if not filtered.empty else filtered, use_container_width=True)

st.subheader("Project details")
for _, row in filtered.head(20).iterrows():
    with st.expander(f"{row['full_name']} - {row['overall_insight_score']:.2f}"):
        st.write(row.get("one_sentence_summary"))
        st.write("Recommended action:", row.get("recommended_action"))
        st.write("Portfolio idea:", row.get("portfolio_project_idea"))
        st.write("Evidence:", row.get("evidence"))
        st.write("Risk flags:", row.get("risk_flags"))
        st.link_button("Open repository", row.get("html_url"))

c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("Audience count")
    if not filtered.empty:
        st.bar_chart(filtered["primary_audience"].value_counts())
with c2:
    st.subheader("Top languages")
    if not filtered.empty:
        st.bar_chart(filtered["language"].value_counts().head(10))
with c3:
    st.subheader("Score distribution")
    if not filtered.empty:
        st.bar_chart(filtered["overall_insight_score"])

st.subheader("Archive")
st.dataframe(pd.DataFrame(archive), use_container_width=True)

if MASTER_CSV.exists():
    st.subheader("Historical master preview")
    st.dataframe(pd.read_csv(MASTER_CSV).head(50), use_container_width=True)
