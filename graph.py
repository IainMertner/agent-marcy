from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from rank_items import rank_items
from sites import gmd_1, gmd_2, br_1, br_2, hs_1, hs_2, hurr_1, hurr_2, mwhq_1, mwhq_2

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

# define the shared state for the pipeline
@dataclass
class AgentState:
    user_input: Optional[str] = None
    parsed_input: Optional[str] = None
    sites: List[str] = field(default_factory=list)
    item_urls: List[Dict[str,str]] = field(default_factory=list)
    items: List[Dict[str, Any]] = field(default_factory=list)
    ranked_items: List[Dict[str, Any]] = field(default_factory=list)

### node functions

## parse user input (dummy code)
def parse_input_step(state: AgentState):
    return {"parsed_input": state.user_input}

## get list of sites to search
def get_sites_step(state: dict):
    return {"sites": [
        "gmd", # girlmeetsdress
        "br", # byrotation
        "hs", # hirestreet
        "hurr", # hurr
        "mwhq" # mywardrobehq
        ]}

## find list of item urls from all sites
def find_item_urls_step(state: dict):
    item_urls = []

    ## iterate over each site
    for site in state.sites:
        # find site's corresponding scraper
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

## score and rank items
def rank_items_step(state: dict):
    ranked = rank_items(state.user_input, state.items)
    return {"ranked_items": ranked}

### build graph

graph = StateGraph(AgentState)
## add nodes
graph.add_node("parse_input_step", parse_input_step)
graph.add_node("get_sites_step", get_sites_step)
graph.add_node("find_item_urls_step", find_item_urls_step)
graph.add_node("get_item_details_step", get_item_details_step)
graph.add_node("rank_items_step", rank_items_step)
## connect nodes through edges (fully sequential)
graph.add_edge(START, "parse_input_step")
graph.add_edge("parse_input_step", "get_sites_step")
graph.add_edge("get_sites_step", "find_item_urls_step")
graph.add_edge("find_item_urls_step", "get_item_details_step")
graph.add_edge("get_item_details_step", "rank_items_step")
graph.add_edge("rank_items_step", END)
# compile graph for execution
graph = graph.compile()