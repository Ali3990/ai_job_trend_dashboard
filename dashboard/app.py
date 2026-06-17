import os
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
from dotenv import load_dotenv
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from flask_caching import Cache

load_dotenv()

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server  # exposed for gunicorn

cache = Cache(server, config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 3600})


@cache.memoize(timeout=3600)
def load_data():
    db_url = os.getenv("DATABASE_PUBLIC_URL").replace("postgresql://", "postgresql+psycopg2://", 1)
    engine = create_engine(db_url)
    df = pd.read_sql("SELECT * FROM adzuna_it_jobs;", engine)
    engine.dispose()
    df["month_year"] = pd.to_datetime(df["month_year"])
    return df


df_all = load_data()
all_states = sorted(df_all["state"].dropna().unique().tolist())


def filter_section(title, checklist_id, select_all_id, options, initial_values):
    return html.Div([
        html.P(title, className="fw-bold mb-1 small"),
        dcc.Checklist(
            id=select_all_id,
            options=[{"label": " Select All", "value": "all"}],
            value=["all"],
            className="mb-1",
        ),
        html.Hr(className="my-1"),
        html.Div(
            dcc.Checklist(
                id=checklist_id,
                options=[{"label": f" {o}", "value": o} for o in options],
                value=initial_values,
                labelStyle={"display": "block", "marginBottom": "2px", "fontSize": "0.8rem"},
            ),
            style={"maxHeight": "160px", "overflowY": "auto"},
        ),
    ], className="mb-3")


app.layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        # Sidebar
        dbc.Col(width=2, style={"borderRight": "1px solid #dee2e6", "minHeight": "100vh", "paddingTop": "1rem"}, children=[
            html.H5("Filters", className="mb-3"),
            filter_section("State", "state-checklist", "state-select-all", all_states, all_states),
            filter_section("County", "county-checklist", "county-select-all", [], []),
            filter_section("City", "city-checklist", "city-select-all", [], []),
            html.Hr(),
            html.Small("Active Filters", className="text-muted fw-bold"),
            html.Div(id="filter-summary", className="mt-1"),
        ]),
        # Main content
        dbc.Col(width=10, style={"paddingTop": "1rem"}, children=[
            html.H2("AI Jobs & Migration Trends"),
            html.Small("Source: Adzuna API, Placer.AI", className="text-muted"),
            html.Hr(),
            # Metric cards
            dbc.Row(className="mb-4", children=[
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.P("Total Jobs", className="text-muted small mb-1"),
                    html.H4(id="metric-total", className="mb-0"),
                ])), width=3),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.P("AI-related Roles", className="text-muted small mb-1"),
                    html.H4(id="metric-ai", className="mb-0"),
                ])), width=3),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.P("States", className="text-muted small mb-1"),
                    html.H4(id="metric-states", className="mb-0"),
                ])), width=3),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.P("Cities", className="text-muted small mb-1"),
                    html.H4(id="metric-cities", className="mb-0"),
                ])), width=3),
            ]),
            # Charts row
            dbc.Row(className="mb-3", children=[
                dbc.Col(width=7, children=[
                    html.H5("Monthly IT Job Postings (Last 6 Months)"),
                    dcc.Graph(id="bar-chart"),
                ]),
                dbc.Col(width=5, children=[
                    html.Div(
                        "Chart placeholder",
                        className="border rounded p-3 text-muted h-100 d-flex align-items-center justify-content-center",
                    ),
                ]),
            ]),
            html.Hr(),
            html.H5("Top Cities by Job Postings"),
            html.Div("Chart placeholder", className="border rounded p-3 text-muted mb-3"),
            html.Hr(),
            html.H5("Job Map"),
            html.Div("Map placeholder", className="border rounded p-3 text-muted mb-3"),
        ]),
    ])
])


# --- Filter callbacks ---

@app.callback(
    Output("state-checklist", "value", allow_duplicate=True),
    Input("state-select-all", "value"),
    State("state-checklist", "options"),
    prevent_initial_call=True,
)
def toggle_state_all(select_all, options):
    return [o["value"] for o in options] if select_all else []


@app.callback(
    Output("county-checklist", "options"),
    Output("county-checklist", "value"),
    Input("state-checklist", "value"),
)
def update_county_options(selected_states):
    df = load_data()
    if not selected_states:
        return [], []
    counties = sorted(df[df["state"].isin(selected_states)]["county"].dropna().unique().tolist())
    return [{"label": c, "value": c} for c in counties], counties


@app.callback(
    Output("county-checklist", "value", allow_duplicate=True),
    Input("county-select-all", "value"),
    State("county-checklist", "options"),
    prevent_initial_call=True,
)
def toggle_county_all(select_all, options):
    return [o["value"] for o in options] if select_all else []


@app.callback(
    Output("city-checklist", "options"),
    Output("city-checklist", "value"),
    Input("county-checklist", "value"),
    State("state-checklist", "value"),
)
def update_city_options(selected_counties, selected_states):
    df = load_data()
    if not selected_counties or not selected_states:
        return [], []
    cities = sorted(
        df[
            df["state"].isin(selected_states) & df["county"].isin(selected_counties)
        ]["city"].dropna().unique().tolist()
    )
    return [{"label": c, "value": c} for c in cities], cities


@app.callback(
    Output("city-checklist", "value", allow_duplicate=True),
    Input("city-select-all", "value"),
    State("city-checklist", "options"),
    prevent_initial_call=True,
)
def toggle_city_all(select_all, options):
    return [o["value"] for o in options] if select_all else []


# --- Dashboard update callback ---

@app.callback(
    Output("metric-total", "children"),
    Output("metric-ai", "children"),
    Output("metric-states", "children"),
    Output("metric-cities", "children"),
    Output("bar-chart", "figure"),
    Output("filter-summary", "children"),
    Input("state-checklist", "value"),
    Input("county-checklist", "value"),
    Input("city-checklist", "value"),
)
def update_dashboard(selected_states, selected_counties, selected_cities):
    df = load_data()

    selected_states = selected_states or []
    selected_counties = selected_counties or []
    selected_cities = selected_cities or []

    filtered = df[
        df["state"].isin(selected_states) &
        df["county"].isin(selected_counties) &
        df["city"].isin(selected_cities)
    ]

    total = f"{len(filtered):,}"
    ai_count = f"{int(filtered['is_ai_related'].sum()):,}"
    states_count = f"{filtered['state'].nunique():,}"
    cities_count = f"{filtered['city'].nunique():,}"

    # Bar chart
    if not filtered.empty:
        max_date = filtered["month_year"].max()
        six_months_ago = max_date - pd.DateOffset(months=5)
        recent = filtered[filtered["month_year"] >= six_months_ago].copy()
    else:
        recent = filtered.copy()

    recent["category"] = recent["is_ai_related"].map({True: "AI Jobs", False: "IT Jobs"})
    monthly = (
        recent
        .groupby(["month_year", "category"])
        .size()
        .reset_index(name="count")
        .sort_values("month_year")
    )

    fig = px.bar(
        monthly,
        x="month_year", y="count", color="category",
        barmode="stack",
        color_discrete_map={"IT Jobs": "#4C8BF5", "AI Jobs": "#F5A623"},
        labels={"month_year": "Month", "count": "Job Postings", "category": ""},
        height=350,
    )
    fig.update_yaxes(tickformat=",.0f")
    fig.update_xaxes(tickformat="%b %Y")
    fig.update_layout(
        margin=dict(t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Filter summary
    s_text = ", ".join(selected_states) if len(selected_states) <= 5 else f"{len(selected_states)} states"
    c_text = ", ".join(selected_counties) if len(selected_counties) <= 3 else f"{len(selected_counties)} counties"
    ci_text = ", ".join(selected_cities) if len(selected_cities) <= 3 else f"{len(selected_cities)} cities"

    summary = html.Div([
        html.Small(f"States: {s_text or 'None'}", className="d-block text-muted"),
        html.Small(f"Counties: {c_text or 'None'}", className="d-block text-muted"),
        html.Small(f"Cities: {ci_text or 'None'}", className="d-block text-muted"),
    ])

    return total, ai_count, states_count, cities_count, fig, summary


if __name__ == "__main__":
    app.run(debug=True)
