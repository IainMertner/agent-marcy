from typing import List, Dict

def simple_similarity_score(user_query: str, description: str) -> float:
    """
    Compute a simple similarity score between user query and item description
    based on word overlap. Returns a value between 0 and 1.
    """
    if not description:
        return 0.0

    q_words = set(user_query.lower().split())
    d_words = set(description.lower().split())

    if not q_words:
        return 0.0

    overlap = q_words.intersection(d_words)
    return len(overlap) / len(q_words)


def score_item(user_query: str, item: Dict) -> Dict:
    """
    Compute total score for a single item:
    - price_score
    - delivery_score
    - similarity_score
    - total_score (sum of the above)
    """
    score = 0.0

    # Price scoring 
    price = item.get("price")
    price_score = 0.0

    if isinstance(price, (int, float)):
        if price <= 50:
            price_score = 2.0
        elif price <= 70:
            price_score = 1.0

    score += price_score

    # Delivery Time scoring
    delivery = (item.get("delivery") or "").strip()
    delivery_score = 0.0

    if "Next Day" in delivery:
        delivery_score = 2.0
    elif "2–3 Days" in delivery or "2-3 Days" in delivery:
        delivery_score = 1.0

    score += delivery_score

    # Description similarity scoring
    # Use description if present, else fall back to title, else empty string
    desc = item.get("description") or item.get("title") or ""
    sim = simple_similarity_score(user_query, desc)  # 0 to 1

    similarity_score = sim * 2.0 
    score += similarity_score

    # Store component scores 
    item["price_score"] = price_score
    item["delivery_score"] = delivery_score
    item["similarity_score"] = similarity_score
    item["total_score"] = score

    return item


def rank_items(user_query: str, items: List[Dict]) -> List[Dict]:
    """
    Rank a list of items by their total_score (descending).
    Adds scoring fields to each item.
    """
    scored_items: List[Dict] = []

    for item in items:
        scored = score_item(user_query, item)
        scored_items.append(scored)

    scored_items.sort(key=lambda x: x.get("total_score", 0.0), reverse=True)

    return scored_items
