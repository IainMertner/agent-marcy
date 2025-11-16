from langgraph.graph import StateGraph, START, END
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from rank_items import rank_items
from sites import gmd_1, gmd_2, br_1, br_2, hs_1, hs_2, hurr_1, hurr_2, mwhq_1, mwhq_2
from langchain_core.tracers import ConsoleCallbackHandler
from langsmith import Client
import os


# initialise scraper modules for each site
SITE_MODULES = {
    "gmd_1": gmd_1,
    "gmd_2": gmd_2,
    "br_1": br_1,
    "br_2": br_2,
    "hs_1": hs_1,
    "hs_2": hs_2, # does not work
    "hurr_1": hurr_1,
    "hurr_2": hurr_2,
    "mwhq_1": mwhq_1,
    "mwhq_2": mwhq_2
}


@dataclass
class AgentState:
    user_input: Optional[str] = None
    parsed_input: Optional[str] = None
    sites: List[str] = field(default_factory=list)
    item_urls: List[Dict[str,str]] = field(default_factory=list)
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
            print(f"No model found for site: {site}")
            continue # no scraper module found

        # call site's scraper function with user input
        urls = module_1.get_item_urls(state.parsed_input)

        for url in urls:
            item_urls.append({"site": site, "url": url})

    return {"item_urls": item_urls}

## get individual item details from urls (dummy code)
def get_item_details_step(state: dict):
    items = []

    # iterate over each item url
    for item_url in state.item_urls:
        site = item_url.get("site")
        module_2 = SITE_MODULES.get(site + "_2")
        if module_2 is None:
            print(f"No model found for site: {site}")
            continue # no scraper module found

        # call site's item scraper function
        item = module_2.get_details(item_url.get("url"))
        items.append(item)

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


client = Client(api_key=os.getenv("LANGSMITH_API_KEY"))