import csv
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

app_id = os.getenv("adzuna_app_id")
app_key = os.getenv("adzuna_app_key")

endpoint_url = "https://api.adzuna.com/v1/api/jobs/us/search"

# Tracking the biggest AI hubs. Comment out states that were already completed
states = [
    "CA", "TX", "WA", "NY", "MA", "VA", "NC", "CO",
    "GA", "IL", "PA", "FL", "MD", "NJ", "AZ", "OR",

    "OH", "MI", "MN", "UT", "TN", "MO", "IN", "WI",
    "CT", "NH", "ME", "NV", "NM", "SC", "AL", "KY",

    "IA", "KS", "NE", "OK", "AR", "LA", "MS", "WV",
    "MT", "WY", "ID", "ND", "SD", "VT", "RI", "DE",
]

job_terms = [
    "machine learning",
    "artificial intelligence", "GenAI", "Generative AI",
    "LLM", "large language models",
    "AI Engineer", "ML Engineer",
    "Data Scientist", "Applied Scientist", "AI Research Scientist",
    "Prompt engineering", "Vector Databases",
    "AI Agents", "Mult-Agent Systems",
    "RAG", "Retrieval Augmented GenAI"

    # "OpenAI", "Anthropic",
    # "Claude", "GPT", "Gemini",
]

# 25 results per min, 250 per day, 1k per month limit
results_per_page = 25
max_requests_per_day = 250
delay = 3

OUTPUT_DIR = Path("job data")
OUTPUT_FILE = OUTPUT_DIR / "adzuna_ai_jobs.csv"
CHECKPOINT_FILE = "adzuna_checkpoint.json"

fieldnames  = [
    "id",
    "created_timestamp",
    "title",
    "description",
    "category_label",
    "category_tag",
    "company_name",
    "salary_min",
    "salary_max",
    "country",
    "state",
    "city",
    "neighborhood",
    "lat",
    "lon",
    "search_state",
    "search_term",
]


def load_checkpoint():
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    return {
        "state_index": 0,
        "term_index": 0,
        "page": 1,
    }


def save_checkpoint(state_index, term_index, page):
    checkpoint = {
        "state_index": state_index,
        "term_index": term_index,
        "page": page,
    }

    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as file:
        json.dump(checkpoint, file, indent=2)


def flatten_job(job, search_state, search_term):
    location = job.get("location") or {}
    area = location.get("area") or []

    category = job.get("category") or {}
    company = job.get("company") or {}

    return {
        "id": job.get("id"),
        "created_timestamp": job.get("created"),
        "title": job.get("title"),
        "description": job.get("description"),
        "category_label": category.get("label"),
        "category_tag": category.get("tag"),
        "company_name": company.get("display_name"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "country": area[0] if len(area) > 0 else None,
        "state": area[1] if len(area) > 1 else None,
        "city": area[2] if len(area) > 2 else None,
        "neighborhood": area[3] if len(area) > 3 else None,
        "lat": job.get("latitude"),
        "lon": job.get("longitude"),
        "search_state": search_state,
        "search_term": search_term,
    }


def fetch_page(state, term, page, max_retries=2):
    url = f"{endpoint_url}/{page}"

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": term,
        "where": state,
        "results_per_page": results_per_page,
        "permanent": "1",
        "full_time": "1",
    }

    for attempt in range(1, max_retries + 1):
        response = requests.get(url, params=params, timeout=30)

        print(
            f"State={state} | Term={term} | Page={page} | "
            f"Status={response.status_code} | Attempt={attempt}"
        )

        if response.status_code == 200:
            return response.json()

        if response.status_code in [429, 500, 502, 503, 504]:
            wait_seconds = 10 * attempt
            print(f"Retryable error. Waiting {wait_seconds} seconds...")
            time.sleep(wait_seconds)
            continue

        print(response.text[:500])
        response.raise_for_status()

        raise RuntimeError(
            f"Failed after {max_retries} retries: state={state}, term={term}, page={page}"
        )

    response = requests.get(url, params=params, timeout=30)

    print(
        f"State={state} | Term={term} | Page={page} | "
        f"Status={response.status_code}"
    )

    if response.status_code != 200:
        print(response.text[:500])

    response.raise_for_status()
    return response.json()


def load_existing_ids():
    if not Path(OUTPUT_FILE).exists():
        return set()

    existing_ids = set()

    with open(OUTPUT_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("id"):
                existing_ids.add(row["id"])

    return existing_ids


def append_rows(rows):
    file_exists = Path(OUTPUT_FILE).exists()

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)


def main():
    if not app_id or not app_key:
        raise ValueError("Missing or expired adzuna_app_id and/or adzuna_app_key.")

    checkpoint = load_checkpoint()

    start_state_index = checkpoint["state_index"]
    start_term_index = checkpoint["term_index"]
    start_page = checkpoint["page"]

    seen_ids = load_existing_ids()
    request_count = 0
    new_rows_count = 0

    for state_index in range(start_state_index, len(states)):
        state = states[state_index]

        term_start = start_term_index if state_index == start_state_index else 0

        for term_index in range(term_start, len(job_terms)):
            term = job_terms[term_index]

            page = (
                start_page
                if state_index == start_state_index and term_index == start_term_index
                else 1
            )

            while request_count < max_requests_per_day:
                data = fetch_page(state, term, page)
                request_count += 1

                results = data.get("results", [])
                total_count = data.get("count", 0)

                print(f"Total available for {state} / {term}: {total_count}")

                if not results:
                    save_checkpoint(state_index, term_index + 1, 1)
                    break

                rows_to_write = []

                for job in results:
                    job_id = job.get("id")

                    if not job_id or job_id in seen_ids:
                        continue

                    seen_ids.add(job_id)
                    rows_to_write.append(flatten_job(job, state, term))

                if rows_to_write:
                    append_rows(rows_to_write)
                    new_rows_count += len(rows_to_write)

                next_page = page + 1
                save_checkpoint(state_index, term_index, next_page)

                if page * results_per_page >= total_count:
                    save_checkpoint(state_index, term_index + 1, 1)
                    break

                page += 1

                if request_count >= max_requests_per_day:
                    break

                time.sleep(delay)

            if request_count >= max_requests_per_day:
                print("Reached daily request limit.")
                print(f"Resume checkpoint saved to {CHECKPOINT_FILE}.")
                break

        if request_count >= max_requests_per_day:
            break

    print(f"New jobs saved this run: {new_rows_count}")
    print(f"Requests used this run: {request_count}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Checkpoint file: {CHECKPOINT_FILE}")


if __name__ == "__main__":
    main()