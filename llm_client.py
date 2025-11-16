# llm_client.py

import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
from pathlib import Path

from dotenv import load_dotenv

# Just load from project root / current working dir
load_dotenv()


API_ENDPOINT = os.getenv("API_ENDPOINT")
API_TOKEN = os.getenv("API_TOKEN")
TEAM_ID = os.getenv("TEAM_ID")

#
print(
    ">>> DEBUG ENV in llm_client:",
    "API_ENDPOINT =", repr(API_ENDPOINT),
    "API_TOKEN =", "***" if API_TOKEN else None,
    "TEAM_ID =", repr(TEAM_ID),
)

# Recommended model from the hackathon
DEFAULT_MODEL = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"


def _to_bedrock_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Convert OpenAI-style messages (with 'system' + 'user') into the format
    the hackathon Bedrock proxy expects (user/assistant only).

    We:
    - Concatenate all `system` contents and prepend them.
    - Concatenate all `user` contents after that.
    - Send *one* user message: {"role": "user", "content": combined_text}.
    """
    system_parts = [m.get("content", "") for m in messages if m.get("role") == "system"]
    user_parts = [m.get("content", "") for m in messages if m.get("role") == "user"]

    combined = ""

    if system_parts:
        combined += "\n\n".join(system_parts).strip() + "\n\n"
    if user_parts:
        combined += "\n\n".join(user_parts).strip()

    combined = combined.strip()
    if not combined:
        combined = "You are an AI assistant helping choose the best fashion rental item."

    return [
        {
            "role": "user",
            "content": combined,
        }
    ]


def call_llm(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    max_tokens: int = 128,
) -> str:
    """
    Thin wrapper around the Holistic AI Bedrock proxy.
    Returns only the assistant text (or a JSON string fallback),
    not the full JSON response.
    """
    if not API_ENDPOINT:
        raise RuntimeError("API_ENDPOINT not set in environment/.env")
    if not TEAM_ID or not API_TOKEN:
        raise RuntimeError("TEAM_ID or API_TOKEN not set in environment/.env")

    headers = {
        "Content-Type": "application/json",
        "X-Team-ID": TEAM_ID,
        "X-API-Token": API_TOKEN,
    }

    # Convert our system+user messages to the simple user-only format
    bedrock_messages = _to_bedrock_messages(messages)

    # Match the working demo script payload shape
    payload = {
        "team_id": TEAM_ID,
        "api_token": API_TOKEN,
        "model": model,
        "messages": bedrock_messages,
        "max_tokens": max_tokens,
    }

    # Debug: see exactly what we're sending 
    print(">>> LLM payload:", payload)

    try:
        resp = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)

        if resp.status_code != 200:
            print(">>> LLM API error status:", resp.status_code)
            print(">>> LLM API response body:", resp.text)
            # Fallback JSON that agent_rank_with_llm can parse safely
            return (
                '{"chosen_index": 0, '
                '"explanation": "LLM call failed (HTTP error), using top rule-based item."}'
            )

        data = resp.json()

    except requests.exceptions.RequestException as e:
        print(">>> LLM request exception:", repr(e))
        return (
            '{"chosen_index": 0, '
            '"explanation": "LLM call failed (request error), using top rule-based item."}'
        )

    # Expect: {"content": [{"type": "text", "text": "..."}], ...}
    content = data.get("content", [])
    if not content:
        return (
            '{"chosen_index": 0, '
            '"explanation": "LLM call returned empty content, using top rule-based item."}'
        )

    # Join text blocks if there are multiple
    texts: List[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            texts.append(block.get("text", ""))

    text = "".join(texts).strip()

    if not text:
        return (
            '{"chosen_index": 0, '
            '"explanation": "LLM call returned no text content, using top rule-based item."}'
        )

    return text
