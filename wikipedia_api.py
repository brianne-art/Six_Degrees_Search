import requests
import time
from database import (
    get_cached_links,
    get_cached_backlinks,
    cache_page_links,
    cache_backlink
)

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {
    "User-Agent": "WikipediaChainFinder/1.0 (Educational project; contact@example.com)"
}
REQUEST_DELAY = 0.1  # Small delay between API requests to avoid rate limiting


def normalize_title(title):
    """Convert title to Wikipedia format: spaces to underscores, capitalize first letter."""
    if not title:
        return title
    title = title.strip().replace(" ", "_")
    return title[0].upper() + title[1:] if title else title


def article_exists(title):
    """Check if a Wikipedia article exists."""
    normalized = normalize_title(title)
    params = {
        "action": "query",
        "titles": normalized,
        "format": "json"
    }

    try:
        response = requests.get(WIKIPEDIA_API_URL, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id == "-1" or "missing" in page_data:
                return False
            return True
        return False
    except requests.RequestException as e:
        raise Exception(f"Error accessing Wikipedia API: {e}")


def get_outgoing_links(title):
    """Get all outgoing links from a Wikipedia article (namespace 0 only).

    Uses cache if available, otherwise fetches from API and caches result.
    """
    normalized = normalize_title(title)

    # Check cache first
    cached = get_cached_links(normalized)
    if cached is not None:
        return cached

    # Not cached, fetch from API
    links = []
    params = {
        "action": "query",
        "titles": normalized,
        "prop": "links",
        "pllimit": "max",
        "plnamespace": "0",
        "format": "json"
    }

    try:
        while True:
            response = requests.get(WIKIPEDIA_API_URL, params=params, headers=HEADERS, timeout=30)
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id == "-1" or "missing" in page_data:
                    return []
                page_links = page_data.get("links", [])
                for link in page_links:
                    links.append(link["title"].replace(" ", "_"))

            if "continue" in data:
                params["plcontinue"] = data["continue"]["plcontinue"]
                time.sleep(REQUEST_DELAY)  # Rate limiting
            else:
                break

        # Cache the results
        cache_page_links(normalized, links)

        return links
    except requests.RequestException as e:
        raise Exception(f"Error accessing Wikipedia API: {e}")


def get_incoming_links(title, max_links=500):
    """Get incoming links (backlinks) to a Wikipedia article (namespace 0 only).

    Uses hybrid approach: combines cached backlinks with fresh API results.
    Limited to max_links to improve performance (most searches don't need all backlinks).
    """
    normalized = normalize_title(title)

    # Get any cached backlinks
    cached_backlinks = set(get_cached_backlinks(normalized))

    # If we have enough cached, return them
    if len(cached_backlinks) >= max_links:
        return list(cached_backlinks)[:max_links]

    # Fetch from API (limited)
    api_links = []
    params = {
        "action": "query",
        "list": "backlinks",
        "bltitle": normalized,
        "bllimit": "500",  # Fetch 500 at a time
        "blnamespace": "0",
        "format": "json"
    }

    try:
        while len(api_links) < max_links:
            response = requests.get(WIKIPEDIA_API_URL, params=params, headers=HEADERS, timeout=30)
            response.raise_for_status()
            data = response.json()

            backlinks = data.get("query", {}).get("backlinks", [])
            for link in backlinks:
                link_title = link["title"].replace(" ", "_")
                api_links.append(link_title)
                # Cache this backlink relationship
                cache_backlink(link_title, normalized)

            if "continue" in data and len(api_links) < max_links:
                params["blcontinue"] = data["continue"]["blcontinue"]
                time.sleep(REQUEST_DELAY)
            else:
                break

        # Combine cached and API results (remove duplicates), limit total
        all_backlinks = list(cached_backlinks.union(set(api_links)))[:max_links]
        return all_backlinks

    except requests.RequestException as e:
        # If API fails, return cached backlinks if available
        if cached_backlinks:
            return list(cached_backlinks)[:max_links]
        raise Exception(f"Error accessing Wikipedia API: {e}")
