from llm_client import call_llm
import ast

def get_sites(user_input):
    system_prompt = (
        "Your task is to read a user's requirements and decide which of the listed possible fashion rental platforms are most suitable.\n"
        "Be generous in your selection choice, only excluding platforms which are clearly not suitable.\n"
        "Remember that renting clothes is cheaper than buying, so only exclude higher-price platforms for very low budgets."
        "You should list their CODES and not their names, in a python-format list.\n"
        "Do not put spaces inside the list.\n"
        "Output an explanation only AFTER the list, separated by a space.\n"
        "OUTPUT FORMAT:\n"
        "[\"platform1\",\"platform2\",\"platform3\"]\n"
        "Possible fashion rental platforms:\n"
        "CODE: \"br\", NAME: \"byrotation\", DESCRIPTION: wide variety\n"
        "CODE: \"gmd\", NAME: \"girlmeetsdress\", DESCRIPTION: primarily dresses, mid-price\n"
        "CODE: \"hs\", NAME: \"hirestreet\", DESCRIPTION: casual/semi-formal, budget-friendly\n"
        "CODE: \"hurr\", NAME: \"hurr\", DESCRIPTION: high-end fashion\n"
        "CODE: \"mwhq\", NAME: \"mywardrobehq\", DESCRIPTION: luxury fashion\n"
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

    parts = raw_response.split()
    sites = ast.literal_eval(parts[0])

    print(raw_response)

    return sites