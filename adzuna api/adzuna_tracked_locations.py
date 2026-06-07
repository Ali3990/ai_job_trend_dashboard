import os
import time
import requests
from urllib.parse import quote

app_id = os.getenv("app_id")
app_key = os.getenv("app_key")

endpoint_url = ""

ai_keywords = ['"artificial intelligence"', '"machine learning"', '"large language model"', '"LLM"',
              '"RAG"', '"LangChain"', '"GenAI"', '"generative AI"']

locations = {"San Francisco"}