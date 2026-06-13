import pandas as pd
from pathlib import Path


processed_path = Path('data\\processed')
processed_file = processed_path / 'adzuna_it_jobs_ai_classified.csv'

adz_df = pd.read_csv(processed_file)

adz_df["date_created"] = pd.to_datetime(adz_df["created_timestamp"], utc=True)
month_year = pd.to_datetime(adz_df["created_timestamp"], utc=True).dt.strftime("%Y-%m")

adz_df.insert(1, "month_year", month_year)

cleaned_df = adz_df.drop(columns=["created_timestamp","category_tag", "search_state", 
                                  "search_category",])

cleaned_df = cleaned_df.dropna(subset=["lat", "lon"])


cleaned_df
