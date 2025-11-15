# ranking.py
# ---------------------------------------------------------
# Ranking module for the fashion rental agent.
#
# INPUT:
#   - user_query: string (what the user typed)
#   - items: list of dicts, each like:
#       {
#           "title": "Red Silk Dress",
#           "price": 45,
#           "delivery": "Next Day",
#           ... (other fields ignored by this module)
#       }
#
# OUTPUT:
#   - same list of dicts, but:
#       * sorted from best to worst
#       * each item has extra fields:
#           - price_score
#           - delivery_score
#           - similarity_score
#           - total_score
#
# This module does NOT call any LLM directly.
# It leaves a clear hook where an LLM-based similarity function
# can be plugged in later instead of simple_similarity_score().
# ---------------------------------------------------------

from typing import List, Dict


def simple_similarity_score(user_query: str, item_title: str) -> float:
    """
    Simple text similarity between the user query and an item title.

    For now:
    - Lowercases both strings
    - Splits into words
    - Calculates how many words overlap
    - Returns a value between 0 and 1

    This is a placeholder until an LLM-based similarity is plugged in.
    """
    q_words = set(user_query.lower().split())
    t_words = set(item_title.lower().split())

    if not q_words:
        return 0.0

    overlap = q_words.intersection(q_words.intersection(t_words))
    # Simpler and correct:
    overlap = q_words.intersection(t_words)

    return len(overlap) / len(q_words)


def score_item(user_query: str, item: Dict) -> Dict:
    """
    Takes a single item and:
    - extracts price, delivery, title
    - calculates three sub-scores:
        * price_score
        * delivery_score
        * similarity_score (to the user query)
    - sums them into total_score
    - returns the same item dict with extra score fields added
    """

    score = 0.0

    # -------- 1) PRICE SCORE --------
    price = item.get("price")
    price_score = 0.0

    # Thresholds are tweakable:
    #   <= 50 → +2
    #   <= 70 → +1
    if isinstance(price, (int, float)):
        if price <= 50:
            price_score = 2.0
        elif price <= 70:
            price_score = 1.0

    score += price_score

    # -------- 2) DELIVERY SCORE --------
    delivery = (item.get("delivery") or "").strip()
    delivery_score = 0.0

    # Simple keyword-based rules, can be adjusted later
    if "Next Day" in delivery:
        delivery_score = 2.0
    elif "2–3 Days" in delivery or "2-3 Days" in delivery:
        delivery_score = 1.0

    score += delivery_score

    # -------- 3) SIMILARITY SCORE --------
    title = (item.get("title") or "").strip()
    sim = simple_similarity_score(user_query, title)  # 0 to 1

    # Weight similarity slightly higher so title–query match matters
    similarity_score = sim * 2.0
    score += similarity_score

    # Store the sub-scores back on the item for explainability
    item["price_score"] = price_score
    item["delivery_score"] = delivery_score
    item["similarity_score"] = similarity_score
    item["total_score"] = score

    return item


def rank_items(user_query: str, items: List[Dict]) -> List[Dict]:
    """
    Main function to be used by the rest of the system.

    INPUT:
        user_query: user’s natural language request
        items: list of item dicts from the search / retrieval step

    PROCESS:
        - calls score_item(user_query, item) on each item
        - sorts items by total_score (highest first)

    OUTPUT:
        - list of items with scoring fields added:
            price_score, delivery_score, similarity_score, total_score
        - sorted from best to worst
    """

    scored_items: List[Dict] = []

    for item in items:
        scored = score_item(user_query, item)
        scored_items.append(scored)

    # Sort by total_score descending
    scored_items.sort(key=lambda x: x.get("total_score", 0.0), reverse=True)

    return scored_items


# Optional: quick self-test if this file is run directly
if __name__ == "__main__":
    example_query = "red dress for a wedding"
    example_items = [
        {"title": "Red Silk Dress", "price": 45, "delivery": "Next Day"},
        {"title": "Black Suit", "price": 55, "delivery": "2–3 Days"},
        {"title": "Gold Gown", "price": 70, "delivery": "Next Day"},
    ]

    ranked = rank_items(example_query, example_items)

    for i, item in enumerate(ranked, 1):
        print(
            f"{i}. {item['title']} "
            f"(total={item['total_score']:.2f}, "
            f"price={item['price_score']}, "
            f"delivery={item['delivery_score']}, "
            f"similarity={item['similarity_score']:.2f})"
        )
