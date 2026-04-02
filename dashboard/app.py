"""
dashboard/app.py  —  Task 3: Job Market Dashboard
Run: streamlit run dashboard/app.py

Shows: skill trends, top companies, location heatmap, timeline of listings.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import sqlite3, json
import pandas as pd
from collections import Counter
from datetime import date, timedelta

from config import DB_PATH

st.set_page_config(page_title="DataCharizard — Job Dashboard",
                   page_icon="🔥", layout="wide")

# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_jobs():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM jobs ORDER BY scraped_on DESC", conn)
    conn.close()
    if df.empty:
        return df
    df["skills_list"] = df["skills"].apply(
        lambda x: json.loads(x) if x else []
    )
    return df

@st.cache_data(ttl=300)
def load_progress():
    conn = sqlite3.connect(DB_PATH)
    p = pd.read_sql("SELECT * FROM user_progress", conn)
    q = pd.read_sql("SELECT * FROM quiz_results", conn)
    conn.close()
    return p, q


# ── Layout ─────────────────────────────────────────────────────────────────────

st.title("🔥 DataCharizard Dashboard")
tab1, tab2 = st.tabs(["📊 Job market", "🎮 My learning progress"])

# ─── TAB 1: Jobs ──────────────────────────────────────────────────────────────
with tab1:
    df = load_jobs()

    if df.empty:
        st.info("No jobs scraped yet. Run `python main.py jobs` first.")
    else:
        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total jobs", len(df))
        c2.metric("Today", len(df[df["scraped_on"] == str(date.today())]))
        c3.metric("Sources", df["source"].nunique())
        c4.metric("Companies", df["company"].nunique())

        st.divider()

        col_left, col_right = st.columns([1.2, 1])

        with col_left:
            st.subheader("🔧 Top skills in demand")
            all_skills = [s for sl in df["skills_list"] for s in sl]
            skill_counts = Counter(all_skills).most_common(15)
            if skill_counts:
                skills_df = pd.DataFrame(skill_counts, columns=["Skill", "Count"])
                st.bar_chart(skills_df.set_index("Skill"))

        with col_right:
            st.subheader("🏢 Top hiring companies")
            top_companies = df["company"].value_counts().head(10)
            st.bar_chart(top_companies)

        st.divider()

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("📍 Jobs by location")
            loc_counts = df["location"].value_counts().head(8)
            st.bar_chart(loc_counts)

        with col_b:
            st.subheader("📅 Jobs scraped over time")
            timeline = df.groupby("scraped_on").size().reset_index(name="count")
            st.line_chart(timeline.set_index("scraped_on"))

        st.divider()
        st.subheader("🔍 Browse all jobs")

        # Filters
        fc1, fc2, fc3 = st.columns(3)
        search = fc1.text_input("Search title / company", "")
        sources = fc2.multiselect("Source", df["source"].unique().tolist(),
                                   default=df["source"].unique().tolist())
        days = fc3.slider("Days back", 1, 30, 7)

        cutoff = str(date.today() - timedelta(days=days))
        filtered = df[
            (df["source"].isin(sources)) &
            (df["scraped_on"] >= cutoff) &
            (df["title"].str.contains(search, case=False) |
             df["company"].str.contains(search, case=False))
        ][["title", "company", "location", "source", "scraped_on", "url"]]

        st.dataframe(
            filtered,
            column_config={"url": st.column_config.LinkColumn("Apply")},
            hide_index=True,
            use_container_width=True
        )

# ─── TAB 2: Learning progress ─────────────────────────────────────────────────
with tab2:
    progress_df, quiz_df = load_progress()

    if progress_df.empty:
        st.info("No learning sessions yet. Run `python main.py coach` to start!")
    else:
        from utils.db import get_total_xp, get_level
        xp = get_total_xp()
        level = get_level(xp)

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Level", level)
        p2.metric("Total XP", xp)
        p3.metric("Lessons done", len(progress_df[progress_df["completed"] == 1]))
        accuracy = round(quiz_df["correct"].mean() * 100, 0) if not quiz_df.empty else 0
        p4.metric("Quiz accuracy", f"{accuracy}%")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📚 Lessons by topic")
            topic_counts = progress_df["topic"].value_counts()
            st.bar_chart(topic_counts)

        with col2:
            st.subheader("🎯 XP earned over time")
            xp_by_day = progress_df.groupby("date_done")["xp_earned"].sum()
            st.line_chart(xp_by_day)

        if not quiz_df.empty:
            st.divider()
            st.subheader("📊 Quiz performance by topic")
            quiz_summary = quiz_df.groupby("topic").agg(
                questions=("correct", "count"),
                accuracy=("correct", lambda x: f"{round(x.mean()*100,0)}%")
            ).reset_index()
            st.dataframe(quiz_summary, hide_index=True, use_container_width=True)
