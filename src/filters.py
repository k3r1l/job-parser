KEYWORDS = [
    "data scientist",
    "data science",
    "machine learning",
    "ml engineer",
    "analytics engineer",
    "data analyst",
    "senior data",
    "lead data",
    "principal data",
]

LOCATION_KEYWORDS = [
    "london",
    "uk",
    "united kingdom",
    "remote",
    "hybrid",
]


def is_relevant_title(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in KEYWORDS)


def is_relevant_location(text: str) -> bool:
    t = text.lower()
    return not LOCATION_KEYWORDS or any(loc in t for loc in LOCATION_KEYWORDS)
