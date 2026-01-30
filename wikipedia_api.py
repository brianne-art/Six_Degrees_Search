import requests

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {
    "User-Agent": "WikipediaChainFinder/1.0 (Educational project)"
}


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
    except requests.RequestException:
        raise Exception("Error accessing Wikipedia API")


def get_outgoing_links(title):
    """Get all outgoing links from a Wikipedia article (namespace 0 only)."""
    normalized = normalize_title(title)
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
            else:
                break

        return links
    except requests.RequestException:
        raise Exception("Error accessing Wikipedia API")


def get_incoming_links(title):
    """Get all incoming links (backlinks) to a Wikipedia article (namespace 0 only)."""
    normalized = normalize_title(title)
    links = []
    params = {
        "action": "query",
        "list": "backlinks",
        "bltitle": normalized,
        "bllimit": "max",
        "blnamespace": "0",
        "format": "json"
    }

    try:
        while True:
            response = requests.get(WIKIPEDIA_API_URL, params=params, headers=HEADERS, timeout=30)
            response.raise_for_status()
            data = response.json()

            backlinks = data.get("query", {}).get("backlinks", [])
            for link in backlinks:
                links.append(link["title"].replace(" ", "_"))

            if "continue" in data:
                params["blcontinue"] = data["continue"]["blcontinue"]
            else:
                break

        return links
    except requests.RequestException:
        raise Exception("Error accessing Wikipedia API")
