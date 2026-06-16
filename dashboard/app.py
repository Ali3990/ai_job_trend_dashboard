import os
import psycopg2
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.express as px

load_dotenv()

st.set_page_config(
    page_title="AI Jobs & Migration Trends",
    layout="wide",
)

st.title("AI Jobs & Migration Trends")
st.caption("Source: Adzuna API, Placer.AI")

# refresh data from database each hour
@st.cache_data(ttl=3600)
def load_data():
    db_url = os.getenv("DATABASE_PUBLIC_URL")
    conn = psycopg2.connect(db_url)

    df = pd.read_sql("SELECT * FROM adzuna_it_jobs;", conn)

    conn.close()

    df["month_year"] = pd.to_datetime(df["month_year"])
    return df

# call and load_data
df = load_data()

# Side bar filters
years = sorted(df['year'].dropna().unique().astype(int).tolist())
selected_years = st.sidebar.multiselect("Year", years, default=years)

states = sorted(df["state"].dropna().unique().tolist())
selected_states = st.sidebar.multiselect("State", states, default=states)

filtered_df = df[df["year"].isin(selected_years) & df["state"].isin(selected_states)]

st.divider()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Jobs", f"{len(filtered_df):,}")
col2.metric("AI-related Roles", f"{filtered_df['is_ai_related'].sum():,}")
col3.metric("States", f"{filtered_df['state'].nunique():,}")
col4.metric("Cities", f"{filtered_df['city'].nunique():,}")

st.divider()
st.subheader("Monthly IT Job Postings")
st.info("Chart placeholder")

st.divider()
st.subheader("Top Cities by AI Job Postings")
st.info("Chart placeholder")

st.divider()
st.subheader("Job Map")
st.info("Map placeholder")

