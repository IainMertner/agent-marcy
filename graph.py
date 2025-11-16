from langgraph.graph import StateGraph, START, END
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from rank_items import rank_items
from sites import gmd_1, br_1, hs_1, hurr_1, mwhq_1
from urllib.parse import urlparse


SITE_MODULES = {
    "gmd_1": gmd_1,
    "br_1": br_1,
    "hs_1": hs_1,
    "hurr_1": hurr_1,
    "mwhq_1": mwhq_1,
}


@dataclass
class AgentState:
    user_input: Optional[str] = None
    parsed_input: Optional[str] = None
    sites: List[str] = field(default_factory=list)
    item_urls: List[Any] = field(default_factory=list)  # can be str or dict from scrapers
    items: List[Dict[str, Any]] = field(default_factory=list)
    ranked_items: List[Dict[str, Any]] = field(default_factory=list)


def parse_input_step(state: AgentState):
    return {"parsed_input": state.user_input}


def get_sites_step(state: AgentState):
    return {
        "sites": ["gmd", "br", "hs", "hurr", "mwhq"]
    }


def find_item_urls_step(state: AgentState):
    item_urls: List[Any] = []
    for site in state.sites:
        module_1 = SITE_MODULES.get(site + "_1")
        if module_1 is None:
            print(f"No module found for site: {site}")
            continue
        site_item_urls = module_1.get_item_urls(state.parsed_input)
        item_urls.extend(site_item_urls)
    return {"item_urls": item_urls}


def url_to_pretty_title(raw: Union[str, Dict[str, Any]]) -> str:
    """
    Take a product URL or a dict like {"url": "..."} and return
    a neat human title, e.g.:

      https://.../aga-sequin-maxi-dress-  ->  "Aga Sequin Maxi Dress"
    """
    if not raw:
        return "Untitled item"

    # If the scraper returns a dict, pull a URL-like field out of it
    if isinstance(raw, dict):
        url = raw.get("url") or raw.get("href") or ""
    else:
        url = str(raw)

    if not url:
        return "Untitled item"

    # Get the path part of the URL
    path = urlparse(url).path  
    slug = path.rstrip("/").split("/")[-1]  

    # Drop trailing dashes just in case, then replace internal dashes with spaces
    slug = slug.rstrip("-")         
    slug = slug.replace("-", " ")   

    # Title case it
    title = slug.strip().title()    

    # Fallback if for some reason it ends up empty
    return title or "Untitled item"


def get_item_details_step(state: AgentState):
    items: List[Dict[str, Any]] = []

    for raw in state.item_urls:
        # Normalise raw into a URL string
        if isinstance(raw, dict):
            url = raw.get("url") or raw.get("href") or ""
        else:
            url = str(raw)

        pretty_title = url_to_pretty_title(raw)

        # Mocked details for now – replace with real scraped data later
        items.append({
            "url": url,
            "title": pretty_title,
            "price": 45,
            "delivery": "Next Day",
            "description": f"{pretty_title} from our demo catalogue.",
        })

    return {"items": items}


def rank_items_step(state: AgentState):
    ranked = rank_items(state.user_input, state.items)
    return {"ranked_items": ranked}


# ---------- BUILD + COMPILE ----------

graph_builder = StateGraph(AgentState)

graph_builder.add_node("parse_input_step", parse_input_step)
graph_builder.add_node("get_sites_step", get_sites_step)
graph_builder.add_node("find_item_urls_step", find_item_urls_step)
graph_builder.add_node("get_item_details_step", get_item_details_step)
graph_builder.add_node("rank_items_step", rank_items_step)

graph_builder.add_edge(START, "parse_input_step")
graph_builder.add_edge("parse_input_step", "get_sites_step")
graph_builder.add_edge("get_sites_step", "find_item_urls_step")
graph_builder.add_edge("find_item_urls_step", "get_item_details_step")
graph_builder.add_edge("get_item_details_step", "rank_items_step")
graph_builder.add_edge("rank_items_step", END)

# THIS is the important line:
graph = graph_builder.compile()
