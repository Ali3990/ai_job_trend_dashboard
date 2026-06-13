import pandas as pd
from pathlib import Path
import os


processed_path = Path('data/processed')
processed_file = processed_path / 'adzuna_it_jobs_ai_classified.csv'
staging_path = Path('data/staging')

adz_df = pd.read_csv(processed_file)

adz_df["date_created"] = pd.to_datetime(adz_df["created_timestamp"], utc=True)
month_year = pd.to_datetime(adz_df["created_timestamp"], utc=True).dt.strftime("%Y-%m")

if "month_year" not in adz_df.columns:
    adz_df.insert(1, "month_year", month_year)

year = adz_df['month_year'].str[:4]
if "year" not in adz_df.columns:
    adz_df.insert(2, "year", year)

cleaned_df = adz_df.drop(columns=["created_timestamp","category_tag", "search_state", 
                                  "search_category",])

cleaned_df = cleaned_df.dropna(subset=["lat", "lon"]).sort_values("month_year")

cleaned_df.to_csv(os.path.join(staging_path, 'adzuna_cleaned.csv'), index=False)
