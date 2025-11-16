### this is a demonstration of how to access the llm. serves no specific purpose in the graph

from dotenv import load_dotenv
import os
import requests

load_dotenv()

API_ENDPOINT = os.getenv("API_ENDPOINT")
API_TOKEN = os.getenv("API_TOKEN")
TEAM_ID = os.getenv("TEAM_ID")

response = requests.post(
    API_ENDPOINT,
    headers = {
        "Content-Type": "application/json",
        "X-Team-ID": TEAM_ID,
        "X-API-Token": API_TOKEN
    },
    json = {
        "team_id": TEAM_ID,
        "api_token": API_TOKEN,
        "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "messages": [
            {"role": "user", "content": "My name is Professor"}
        ],
        "max_tokens": 512
    }
)

result = response.json()
print(result)