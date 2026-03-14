"""
Amazon autocomplete keyword scraper.
Uses the public Amazon suggestions API — no credentials needed.
"""
import time
import string
import requests

AUTOCOMPLETE_URLS = {
    "US": "https://completion.amazon.com/api/2017/suggestions",
    "UK": "https://completion.amazon.co.uk/api/2017/suggestions",
    "DE": "https://completion.amazon.de/api/2017/suggestions",
    "FR": "https://completion.amazon.fr/api/2017/suggestions",
    "IT": "https://completion.amazon.it/api/2017/suggestions",
    "ES": "https://completion.amazon.es/api/2017/suggestions",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_suggestions(keyword: str, marketplace: str = "US", limit: int = 20) -> list[str]:
    """Return autocomplete suggestions for a keyword."""
    base_url = AUTOCOMPLETE_URLS.get(marketplace, AUTOCOMPLETE_URLS["US"])
    try:
        r = requests.get(
            base_url,
            params={"prefix": keyword, "limit": limit, "alias": "stripbooks"},
            headers=HEADERS,
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        return [s["value"] for s in data.get("suggestions", [])]
    except Exception:
        return []


def alphabet_expand(seed: str, marketplace: str = "US", delay: float = 0.4) -> list[str]:
    """
    Expand a seed keyword by appending a–z and digits.
    This mimics how tools like Publisher Rocket generate keyword lists.
    Returns deduplicated list of all suggestions found.
    """
    characters = list(string.ascii_lowercase) + list(string.digits)
    found = set()

    for char in characters:
        query = f"{seed} {char}"
        suggestions = get_suggestions(query, marketplace=marketplace)
        for s in suggestions:
            found.add(s.strip().lower())
        if delay:
            time.sleep(delay)

    return sorted(found)


def deep_crawl(
    seeds: list[str],
    marketplace: str = "US",
    delay: float = 0.5,
    max_keywords: int = 500,
    progress_callback=None,
) -> list[str]:
    """
    BFS keyword expansion: take a list of seeds, get suggestions for each,
    then expand each new suggestion alphabetically up to max_keywords total.
    """
    found = set()
    queue = list(seeds)
    processed = set()

    total_steps = len(queue)
    step = 0

    while queue and len(found) < max_keywords:
        seed = queue.pop(0)
        if seed in processed:
            continue
        processed.add(seed)
        step += 1

        if progress_callback:
            progress_callback(step, total_steps, seed)

        suggestions = get_suggestions(seed, marketplace=marketplace)
        for s in suggestions:
            s = s.strip().lower()
            if s not in found:
                found.add(s)
                if s not in processed:
                    queue.append(s)
                    total_steps += 1

        if delay:
            time.sleep(delay)

    return sorted(found)[:max_keywords]
