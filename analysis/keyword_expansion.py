"""
Keyword expansion engine — generates variations from base keywords.
"""

BOOK_SUFFIXES = [
    "book", "guide", "for beginners", "for professionals",
    "for engineers", "for managers", "for leaders", "for executives",
    "skills", "strategies", "tips", "techniques", "methods",
    "at work", "in the workplace", "in business",
]

BOOK_PREFIXES = [
    "how to", "best", "mastering", "complete guide to",
    "secrets of", "art of", "power of",
]

AUDIENCE_MODIFIERS = [
    "engineers", "managers", "executives", "professionals",
    "technical professionals", "leaders", "introverts",
    "mid-career professionals",
]


def expand_with_suffixes(keywords: list[str]) -> list[str]:
    expanded = set(keywords)
    for kw in keywords:
        for s in BOOK_SUFFIXES:
            expanded.add(f"{kw} {s}")
    return sorted(expanded)


def expand_with_prefixes(keywords: list[str]) -> list[str]:
    expanded = set(keywords)
    for kw in keywords:
        for p in BOOK_PREFIXES:
            expanded.add(f"{p} {kw}")
    return sorted(expanded)


def expand_with_audience(keywords: list[str]) -> list[str]:
    expanded = set(keywords)
    for kw in keywords:
        for a in AUDIENCE_MODIFIERS:
            expanded.add(f"{kw} for {a}")
    return sorted(expanded)


def full_expansion(keywords: list[str], max_results: int = 1000) -> list[str]:
    """Apply all expansion strategies and return deduplicated list."""
    expanded = set(keywords)
    expanded.update(expand_with_suffixes(keywords))
    expanded.update(expand_with_prefixes(keywords))
    expanded.update(expand_with_audience(keywords))
    result = sorted(expanded)
    return result[:max_results]
