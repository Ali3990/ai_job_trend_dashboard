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

st.markdown("""
<style>
section[data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
    max-height: 200px;
    overflow-y: auto;
    padding-right: 4px;
}
</style>
""", unsafe_allow_html=True)

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

def checkbox_filter(label, options, key_prefix):
    with st.sidebar.expander(label):

        def toggle_all():
            state = st.session_state[f"{key_prefix}_all"]
            for opt in options:
                st.session_state[f"{key_prefix}_{opt}"] = state

        if f"{key_prefix}_all" not in st.session_state:
            st.session_state[f"{key_prefix}_all"] = True
        for opt in options:
            if f"{key_prefix}_{opt}" not in st.session_state:
                st.session_state[f"{key_prefix}_{opt}"] = True

        st.checkbox("Select All", key=f"{key_prefix}_all", on_change=toggle_all)
        st.divider()

        selected = []
        for opt in options:
            if st.checkbox(str(opt), key=f"{key_prefix}_{opt}"):
                selected.append(opt)

    return selected


df = load_data()

states = sorted(df["state"].dropna().unique().tolist())
selected_states = checkbox_filter("State", states, "state")

state_df = df[df["state"].isin(selected_states)]
counties = sorted(state_df["county"].dropna().unique().tolist())
selected_counties = checkbox_filter("County", counties, "county")

county_df = state_df[state_df["county"].isin(selected_counties)]
cities = sorted(county_df["city"].dropna().unique().tolist())
selected_cities = checkbox_filter("City", cities, "city")

filtered_df = df[
    df["state"].isin(selected_states) &
    df["county"].isin(selected_counties) &
    df["city"].isin(selected_cities)
]

st.sidebar.markdown("**Active Filters**")
st.sidebar.caption(f"States: {', '.join(selected_states) if len(selected_states) <= 5 else f'{len(selected_states)} states selected'}")
st.sidebar.caption(f"Counties: {', '.join(selected_counties) if len(selected_counties) <= 3 else f'{len(selected_counties)} counties selected'}")
st.sidebar.caption(f"Cities: {', '.join(selected_cities) if len(selected_cities) <= 3 else f'{len(selected_cities)} cities selected'}")

st.divider()

left_col, right_col = st.columns([3, 2])

with left_col:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Jobs", f"{len(filtered_df):,}")
    m2.metric("AI-related Roles", f"{filtered_df['is_ai_related'].sum():,}")
    m3.metric("States", f"{filtered_df['state'].nunique():,}")
    m4.metric("Cities", f"{filtered_df['city'].nunique():,}")

    st.subheader("Monthly IT Job Postings (Last 6 Months)")

    max_date = filtered_df["month_year"].max()
    six_months_ago = max_date - pd.DateOffset(months=5)
    recent_df = filtered_df[filtered_df["month_year"] >= six_months_ago].copy()
    recent_df["category"] = recent_df["is_ai_related"].map({True: "AI Jobs", False: "IT Jobs"})

    monthly_stacked = (
        recent_df
        .groupby(["month_year", "category"])
        .size()
        .reset_index(name="count")
        .sort_values("month_year")
    )

    fig_bar = px.bar(
        monthly_stacked,
        x="month_year",
        y="count",
        color="category",
        barmode="stack",
        color_discrete_map={"IT Jobs": "#4C8BF5", "AI Jobs": "#F5A623"},
        labels={"month_year": "Month", "count": "Job Postings", "category": ""},
        height=350,
    )
    fig_bar.update_yaxes(tickformat=",.0f")
    fig_bar.update_xaxes(tickformat="%b %Y")
    fig_bar.update_layout(
        margin=dict(t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with right_col:
    st.info("Chart placeholder")

st.divider()
st.subheader("Top Cities by Job Postings")
st.info("Chart placeholder")

st.divider()
st.subheader("Job Map")
st.info("Map placeholder")

