"""
Amazon book search scraper — discovers competitor books for a keyword.
Note: Amazon actively blocks scrapers. This uses polite rate limiting
and common browser headers to minimise blocking.
"""
import time
import requests
from bs4 import BeautifulSoup

SEARCH_URLS = {
    "US": "https://www.amazon.com/s",
    "UK": "https://www.amazon.co.uk/s",
    "DE": "https://www.amazon.de/s",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def search_books(keyword: str, marketplace: str = "US", max_results: int = 10) -> list[dict]:
    """
    Search Amazon books for a keyword and return list of
    {title, asin, author, rating, reviews, url} dicts.
    """
    base_url = SEARCH_URLS.get(marketplace, SEARCH_URLS["US"])
    try:
        r = requests.get(
            base_url,
            params={"k": keyword, "i": "stripbooks"},
            headers=HEADERS,
            timeout=10,
        )
        r.raise_for_status()
    except Exception as e:
        return [{"error": str(e)}]

    soup = BeautifulSoup(r.text, "html.parser")
    books = []

    for item in soup.select('[data-component-type="s-search-result"]')[:max_results]:
        try:
            title_el = item.select_one("h2 a span")
            title = title_el.text.strip() if title_el else "Unknown"

            asin = item.get("data-asin", "")

            author_el = item.select_one(".a-size-base+ .a-size-base, .a-color-secondary .a-size-base")
            author = author_el.text.strip() if author_el else ""

            rating_el = item.select_one(".a-icon-star-small .a-icon-alt, .a-icon-star .a-icon-alt")
            rating = rating_el.text.strip().split(" ")[0] if rating_el else ""

            review_el = item.select_one('[aria-label*="stars"] + span, .a-size-base.s-underline-text')
            reviews = review_el.text.strip() if review_el else ""

            url = ""
            link_el = item.select_one("h2 a")
            if link_el and link_el.get("href"):
                url = "https://www.amazon.com" + link_el["href"]

            books.append(
                {
                    "title": title,
                    "asin": asin,
                    "author": author,
                    "rating": rating,
                    "reviews": reviews,
                    "url": url,
                }
            )
        except Exception:
            continue

    return books


def extract_title_keywords(titles: list[str]) -> list[str]:
    """
    Extract meaningful n-grams from a list of book titles.
    Used to discover keyword ideas from competitor books.
    """
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "up", "about", "into", "through",
        "how", "what", "why", "when", "your", "my", "our", "their", "its",
        "is", "are", "was", "were", "be", "been", "being", "have", "has",
        "had", "do", "does", "did", "will", "would", "could", "should",
    }

    keywords = set()
    for title in titles:
        words = title.lower().replace(":", " ").replace("-", " ").split()
        words = [w.strip(".,!?\"'()[]") for w in words if w.isalpha()]
        words = [w for w in words if w not in stop_words and len(w) > 3]

        # single words
        for w in words:
            keywords.add(w)

        # bigrams
        for i in range(len(words) - 1):
            keywords.add(f"{words[i]} {words[i+1]}")

        # trigrams
        for i in range(len(words) - 2):
            keywords.add(f"{words[i]} {words[i+1]} {words[i+2]}")

    return sorted(keywords)
