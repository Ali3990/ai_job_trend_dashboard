import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="IT Job Trends Dashboard",
    layout="wide",
)

@st.cache_data
def load_data():
    path = Path()