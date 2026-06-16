import pandas as pd
import re
from pathlib import Path

input_file = Path("data/raw/adzuna_it_jobs.csv")
output_file = Path("data/processed/adzuna_it_jobs_ai_classified.csv")

output_file.parent.mkdir(parents=True, exist_ok=True)

AI_TERMS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "large language model",
    "large language models",
    "llm",
    "generative ai",
    "genai",
    "rag",
    "retrieval augmented generation",
    "langchain",
    "llamaindex",
    "openai",
    "anthropic",
    "claude",
    "gpt",
    "gemini",
    "mistral",
    "computer vision",
    "natural language processing",
    "nlp",
    "reinforcement learning",
    "mlops",
    "model deployment",
    "model serving",
    "ai engineer",
    "ml engineer",
    "machine learning engineer",
    "applied scientist",
    "research scientist",
]

def find_ai_terms(text):
    if pd.isna(text):
        return []

    text = str(text).lower()
    matched_terms = []

    for term in AI_TERMS:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, text):
            matched_terms.append(term)

    return sorted(set(matched_terms))


def classify_ai_role(row):
    title = str(row.get("title", "")).lower()
    description = str(row.get("description", "")).lower()
    combined_text = f"{title} {description}"

    matched_terms = find_ai_terms(combined_text)

    is_ai_related = len(matched_terms) > 0

    if any(term in title for term in [
        "machine learning",
        "ml engineer",
        "ai engineer",
        "artificial intelligence",
        "applied scientist",
        "research scientist",
        "llm",
    ]):
        ai_relevance = "High"
    elif is_ai_related:
        ai_relevance = "Medium"
    else:
        ai_relevance = "Not AI"

    return pd.Series({
        "is_ai_related": is_ai_related,
        "ai_relevance": ai_relevance,
        "matched_ai_terms": ", ".join(matched_terms),
    })


def main():
    df = pd.read_csv(input_file)

    ai_columns = df.apply(classify_ai_role, axis=1)

    df["is_ai_related"] = ai_columns["is_ai_related"]
    df["ai_relevance"] = ai_columns["ai_relevance"]
    df["matched_ai_terms"] = ai_columns["matched_ai_terms"]

    df.to_csv(output_file, index=False)

    print(f"Rows processed: {len(df)}")
    print(f"AI-related rows: {df['is_ai_related'].sum()}")
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()