from llm_client import call_llm

def parse_input(user_input):
    system_prompt = (
        "Turn the following user requirements into a short search term for rental fashion sites.\n"
        "Include only garment type plus key attributes (e.g. colour, style, vibe)\n"
        "Do not include size, budget, date, or personal details.\n"
        "Return ONLY the search phrase, with + instead of spaces\n"
    )

    user_msg = (
        f"User requirements:\n{user_input}"
    )

    raw_response = call_llm(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=512,
    )

    print(raw_response)

    return raw_response