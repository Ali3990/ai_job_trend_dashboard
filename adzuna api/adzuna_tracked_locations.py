import os
import time
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

app_id = os.getenv("adzuna_app_id")
app_key = os.getenv("adzuna_app_key")

endpoint_url = "https://api.adzuna.com/v1/api/jobs/us/search/1?"

test_location = "San Francisco, CA"

# Pull request limits: 2.5k a month, 1k per week, 250 per day, 25 per minute
params={
        "app_id": app_id,
        "app_key": app_key,
        "what": "machine learning",
        "where": "San Francisco",
        "results_per_page": 25,
        "content-type": "application/json"
    }

response = requests.get(endpoint_url, params=params, timeout=30)
print("status:", response.status_code)
print("URL:", response.url)

response.raise_for_status()
data = response.json()

print("Total job count:", data.get("count"))



