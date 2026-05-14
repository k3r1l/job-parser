KEYWORDS = [
    "data scientist",
    "data science",
    "machine learning",
    "ml engineer",
    "analytics engineer",
    "data analyst",
    # "senior data " with trailing space prevents matching "senior datawarehouse" etc.
    "senior data ",
    "lead data ",
    "principal data",
]

LOCATION_KEYWORDS = [
    "london",
    "uk",
    "united kingdom",
    "remote",
    "hybrid",
]

# Explicit non-UK location signals — if any appear in the job text, reject the role.
# Ordered roughly by frequency in job postings.
_NON_UK_MARKERS = {
    # USA cities
    "san francisco", "new york", "los angeles", "seattle", "sunnyvale",
    "palo alto", "mountain view", "santa clara", "cupertino", "san jose",
    "chicago", "boston", "austin", "atlanta", "denver", "miami",
    "washington, d", "washington dc",
    # USA country / state signals
    "united states", ", usa", " usa", "california", ", ca ",
    # European cities / countries (not UK)
    "paris", "berlin", "amsterdam", "lisbon", "barcelona", "madrid",
    "milan", "zurich", "frankfurt", "munich", "stockholm", "copenhagen",
    "oslo", "warsaw", "prague", "brussels",
    "portugal", "spain", "france", "germany", "netherlands",
    "sweden", "norway", "denmark", "finland", "poland",
    "austria", "switzerland", "belgium",
    # Eastern Europe
    "riga", "latvia", "tallinn", "estonia", "vilnius", "lithuania",
    "sofia", "bulgaria", "bucharest", "romania",
    # Asia / Pacific / Other
    "tokyo", "japan", "singapore", "sydney", "australia",
    "toronto", "vancouver", "canada",
    "dubai", "israel", "herzliya", "tel aviv",
    "bangalore", "india",
    # Ireland (not UK — if the role says "Dublin, Ireland" it's EU)
    ", ireland", "dublin, ",
}


def is_relevant_title(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in KEYWORDS)


def is_uk_relevant(text: str) -> bool:
    """Return False if text explicitly names a non-UK location."""
    t = text.lower()
    return not any(marker in t for marker in _NON_UK_MARKERS)


def is_relevant_location(text: str) -> bool:
    t = text.lower()
    return not LOCATION_KEYWORDS or any(loc in t for loc in LOCATION_KEYWORDS)
